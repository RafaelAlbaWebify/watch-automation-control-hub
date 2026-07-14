import httpx

from watch.collectors import WebsiteCollector, select_response_headers
from watch.models import Target

PUBLIC_IP = "93.184.216.34"


def _tls_ok(hostname: str, address: str, port: int, timeout: int) -> int:
    return 90


def test_select_response_headers_keeps_only_bounded_allowlist() -> None:
    headers = httpx.Headers(
        {
            "Cache-Control": "public, max-age=300",
            "Content-Language": "en",
            "ETag": '"demo-v1"',
            "Last-Modified": "Tue, 14 Jul 2026 10:00:00 GMT",
            "Server": "example-edge/1.0",
            "Set-Cookie": "session=secret",
            "X-Internal-Trace": "private-correlation-value",
        }
    )

    assert select_response_headers(headers) == {
        "cache-control": "public, max-age=300",
        "content-language": "en",
        "etag": '"demo-v1"',
        "last-modified": "Tue, 14 Jul 2026 10:00:00 GMT",
        "server": "example-edge/1.0",
    }


def test_select_response_headers_truncates_persisted_values() -> None:
    selected = select_response_headers(httpx.Headers({"Server": "x" * 700}))

    assert len(selected["server"]) == 500


def test_collector_records_content_metadata_without_sensitive_headers() -> None:
    content = b"<html><head><title>Evidence Demo</title></head></html>"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            request=request,
            headers={
                "content-type": "text/html; charset=utf-8",
                "cache-control": "public, max-age=60",
                "server": "demo-server",
                "set-cookie": "session=secret",
            },
            content=content,
        )

    target = Target(
        target_id="evidence-demo",
        name="Evidence Demo",
        url="https://example.com",
    )
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=lambda hostname: [PUBLIC_IP],
            tls_probe=_tls_ok,
        ).collect(target)

    assert result.content_type == "text/html; charset=utf-8"
    assert result.content_length_bytes == len(content)
    assert result.page_title == "Evidence Demo"
    assert result.response_headers == {
        "cache-control": "public, max-age=60",
        "server": "demo-server",
    }
    assert "set-cookie" not in result.response_headers
