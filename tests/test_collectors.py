import httpx

from watch.collectors import WebsiteCollector, extract_title
from watch.models import Target


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

    with httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=lambda hostname: ["203.0.113.10"],
        ).collect(_target())

    assert result.http_status == 200
    assert result.final_url == "https://example.com/"
    assert result.page_title == "Example"
    assert result.resolved_ips == ["203.0.113.10"]
    assert result.errors == []


def test_collector_returns_structured_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = WebsiteCollector(client=client, dns_resolver=lambda hostname: []).collect(
            _target()
        )

    assert result.http_status is None
    assert result.errors
    assert result.errors[0].startswith("HTTP timeout:")


def test_collector_preserves_http_result_when_dns_fails() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204, request=request)

    def failing_dns(hostname: str) -> list[str]:
        raise OSError("unavailable")

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = WebsiteCollector(client=client, dns_resolver=failing_dns).collect(_target())

    assert result.http_status == 204
    assert result.errors == ["DNS resolution failed: unavailable"]
