import httpx

from watch.collectors import WebsiteCollector, extract_title
from watch.models import Target

PUBLIC_IP = "93.184.216.34"


def _target() -> Target:
    return Target(target_id="demo-site", name="Demo", url="https://example.com")


def test_extract_title_normalizes_whitespace() -> None:
    assert extract_title("<html><title> Demo   Site </title></html>") == "Demo Site"


def test_collector_captures_http_metadata_and_dns() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<html><head><title>Example</title></head></html>",
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=lambda hostname: [PUBLIC_IP],
        ).collect(_target())

    assert result.http_status == 200
    assert result.final_url == "https://example.com/"
    assert result.page_title == "Example"
    assert result.resolved_ips == [PUBLIC_IP]
    assert result.errors == []


def test_collector_returns_structured_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=lambda hostname: [PUBLIC_IP],
        ).collect(_target())

    assert result.http_status is None
    assert result.errors
    assert result.errors[0].startswith("HTTP timeout:")


def test_collector_blocks_private_initial_target() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=lambda hostname: ["127.0.0.1"],
        ).collect(_target())

    assert calls == 0
    assert result.http_status is None
    assert result.errors == [
        "Target validation failed: non-public address blocked: 127.0.0.1"
    ]


def test_collector_blocks_redirect_to_private_target() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            request=request,
            headers={"location": "http://internal.test"},
        )

    def resolver(hostname: str) -> list[str]:
        return [PUBLIC_IP] if hostname == "example.com" else ["10.0.0.5"]

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=resolver,
        ).collect(_target())

    assert result.http_status is None
    assert result.redirect_chain == ["https://example.com/"]
    assert result.errors == [
        "Target validation failed: non-public address blocked: 10.0.0.5"
    ]


def test_collector_stops_when_dns_fails() -> None:
    def failing_dns(hostname: str) -> list[str]:
        raise OSError("unavailable")

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, request=request)
    )
    with httpx.Client(transport=transport) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=failing_dns,
        ).collect(_target())

    assert result.http_status is None
    assert result.errors == ["Target validation failed: unavailable"]
