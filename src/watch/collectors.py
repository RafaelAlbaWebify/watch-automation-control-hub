from __future__ import annotations

import socket
from html.parser import HTMLParser
from time import perf_counter
from typing import Callable
from urllib.parse import urlparse

import httpx

from watch.models import ObservationSet, Target

DnsResolver = Callable[[str], list[str]]


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._inside_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "title":
            self._inside_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._inside_title = False

    def handle_data(self, data: str) -> None:
        if self._inside_title:
            self.parts.append(data)

    @property
    def title(self) -> str | None:
        value = " ".join(" ".join(self.parts).split()).strip()
        return value or None


def resolve_hostname(hostname: str) -> list[str]:
    records = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    return sorted({record[4][0] for record in records})


def extract_title(html: str) -> str | None:
    parser = _TitleParser()
    parser.feed(html)
    return parser.title


class WebsiteCollector:
    def __init__(
        self,
        client: httpx.Client | None = None,
        dns_resolver: DnsResolver = resolve_hostname,
    ) -> None:
        self._client = client
        self._dns_resolver = dns_resolver

    def collect(self, target: Target) -> ObservationSet:
        errors: list[str] = []
        resolved_ips: list[str] = []
        hostname = urlparse(str(target.url)).hostname

        if hostname:
            try:
                resolved_ips = self._dns_resolver(hostname)
            except OSError as exc:
                errors.append(f"DNS resolution failed: {exc}")

        owns_client = self._client is None
        client = self._client or httpx.Client(
            follow_redirects=True,
            timeout=target.timeout_seconds,
            headers={"User-Agent": "WATCH/0.2 read-only health check"},
        )

        started = perf_counter()
        try:
            response = client.get(str(target.url))
            elapsed_ms = round((perf_counter() - started) * 1000)
            redirect_chain = [str(item.url) for item in response.history]
            content_type = response.headers.get("content-type", "")
            page_title = (
                extract_title(response.text)
                if "text/html" in content_type.lower()
                else None
            )
            return ObservationSet(
                http_status=response.status_code,
                final_url=str(response.url),
                redirect_count=len(response.history),
                redirect_chain=redirect_chain,
                response_ms=elapsed_ms,
                page_title=page_title,
                resolved_ips=resolved_ips,
                errors=errors,
            )
        except httpx.TimeoutException as exc:
            errors.append(f"HTTP timeout: {exc}")
        except httpx.RequestError as exc:
            errors.append(f"HTTP request failed: {exc}")
        finally:
            if owns_client:
                client.close()

        return ObservationSet(resolved_ips=resolved_ips, errors=errors)
