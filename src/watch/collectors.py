from __future__ import annotations

import ipaddress
import socket
from collections.abc import Callable
from html.parser import HTMLParser
from time import perf_counter
from urllib.parse import urljoin, urlparse

import httpx

from watch.models import ObservationSet, Target
from watch.tls import inspect_tls_days_remaining

DnsResolver = Callable[[str], list[str]]
TlsProbe = Callable[[str, str, int, int], int]


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
    return sorted({str(record[4][0]) for record in records})


def extract_title(html: str) -> str | None:
    parser = _TitleParser()
    parser.feed(html)
    return parser.title


def validate_public_ips(addresses: list[str]) -> None:
    if not addresses:
        raise ValueError("hostname did not resolve to any address")
    blocked = [
        address
        for address in addresses
        if not ipaddress.ip_address(address).is_global
    ]
    if blocked:
        raise ValueError(f"non-public address blocked: {', '.join(blocked)}")


def _host_header(url: httpx.URL) -> str:
    hostname = url.host
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    default_port = 443 if url.scheme == "https" else 80
    return hostname if url.port in (None, default_port) else f"{hostname}:{url.port}"


def _pinned_request(url: str, address: str) -> tuple[httpx.URL, dict[str, str], dict[str, str]]:
    logical_url = httpx.URL(url)
    hostname = logical_url.host
    transport_url = logical_url.copy_with(host=address)
    headers = {"Host": _host_header(logical_url)}
    extensions = {"sni_hostname": hostname}
    return transport_url, headers, extensions


class WebsiteCollector:
    def __init__(
        self,
        client: httpx.Client | None = None,
        dns_resolver: DnsResolver = resolve_hostname,
        tls_probe: TlsProbe = inspect_tls_days_remaining,
        max_redirects: int = 5,
    ) -> None:
        self._client = client
        self._dns_resolver = dns_resolver
        self._tls_probe = tls_probe
        self._max_redirects = max_redirects

    def _resolve_public(self, url: str) -> list[str]:
        hostname = urlparse(url).hostname
        if not hostname:
            raise ValueError("URL has no hostname")
        addresses = self._dns_resolver(hostname)
        validate_public_ips(addresses)
        return addresses

    def collect(self, target: Target) -> ObservationSet:
        errors: list[str] = []
        resolved_ips: list[str] = []
        redirect_chain: list[str] = []
        current_url = str(target.url)

        owns_client = self._client is None
        client = self._client or httpx.Client(
            follow_redirects=False,
            timeout=target.timeout_seconds,
            headers={"User-Agent": "WATCH/0.2 read-only health check"},
            trust_env=False,
        )

        started = perf_counter()
        try:
            for redirect_index in range(self._max_redirects + 1):
                try:
                    hop_ips = self._resolve_public(current_url)
                    if redirect_index == 0:
                        resolved_ips = hop_ips
                except (OSError, ValueError) as exc:
                    errors.append(f"Target validation failed: {exc}")
                    break

                request_url, request_headers, request_extensions = _pinned_request(
                    current_url, hop_ips[0]
                )
                response = client.get(
                    request_url,
                    headers=request_headers,
                    extensions=request_extensions,
                    follow_redirects=False,
                )
                location = response.headers.get("location")
                if response.is_redirect and location:
                    if redirect_index == self._max_redirects:
                        errors.append(f"Redirect limit exceeded: {self._max_redirects}")
                        break
                    redirect_chain.append(current_url)
                    current_url = urljoin(current_url, location)
                    continue

                elapsed_ms = round((perf_counter() - started) * 1000)
                content_type = response.headers.get("content-type", "")
                page_title = (
                    extract_title(response.text)
                    if "text/html" in content_type.lower()
                    else None
                )
                tls_days_remaining: int | None = None
                parsed_url = urlparse(current_url)
                if parsed_url.scheme == "https" and parsed_url.hostname:
                    try:
                        tls_days_remaining = self._tls_probe(
                            parsed_url.hostname,
                            hop_ips[0],
                            parsed_url.port or 443,
                            target.timeout_seconds,
                        )
                    except (OSError, ValueError) as exc:
                        errors.append(f"TLS inspection failed: {exc}")

                return ObservationSet(
                    http_status=response.status_code,
                    final_url=str(httpx.URL(current_url)),
                    redirect_count=len(redirect_chain),
                    redirect_chain=redirect_chain,
                    response_ms=elapsed_ms,
                    tls_days_remaining=tls_days_remaining,
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

        return ObservationSet(
            redirect_count=len(redirect_chain),
            redirect_chain=redirect_chain,
            resolved_ips=resolved_ips,
            errors=errors,
        )
