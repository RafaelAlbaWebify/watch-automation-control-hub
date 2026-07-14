import httpx

from watch.collectors import WebsiteCollector, extract_title
from watch.models import Target

PUBLIC_IP = "93.184.216.34"
PUBLIC_IPV6 = "2606:2800:220:1:248:1893:25c8:1946"


def _target(url: str = "https://example.com") -> Target:
    return Target(target_id="demo-site", name="Demo", url=url)


def _tls_ok(hostname: str, address: str, port: int, timeout: int) -> int:
    return 90


def test_extract_title_normalizes_whitespace() -> None:
    assert extract_title("<html><title> Demo   Site </title></html>") == "Demo Site"


def test_collector_pins_validated_ipv4_and_preserves_host_and_sni() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
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
            tls_probe=_tls_ok,
        ).collect(_target())

    assert result.http_status == 200
    assert result.final_url == "https://example.com/"
    assert result.page_title == "Example"
    assert result.resolved_ips == [PUBLIC_IP]
    assert result.tls_days_remaining == 90
    assert result.errors == []
    assert len(captured) == 1
    assert captured[0].url.host == PUBLIC_IP
    assert captured[0].headers["host"] == "example.com"
    assert captured[0].extensions["sni_hostname"] == "example.com"


def test_collector_pins_validated_ipv6_address() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=lambda hostname: [PUBLIC_IPV6],
            tls_probe=_tls_ok,
        ).collect(_target())

    assert result.http_status == 200
    assert captured[0].url.host == PUBLIC_IPV6
    assert str(captured[0].url).startswith("https://[2606:2800:")
    assert captured[0].headers["host"] == "example.com"
    assert captured[0].extensions["sni_hostname"] == "example.com"


def test_redirect_revalidates_and_pins_each_destination() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if len(captured) == 1:
            return httpx.Response(
                302,
                request=request,
                headers={"location": "https://www.example.org/final"},
            )
        return httpx.Response(200, request=request)

    def resolver(hostname: str) -> list[str]:
        return [PUBLIC_IP] if hostname == "example.com" else ["104.18.2.24"]

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=resolver,
            tls_probe=_tls_ok,
        ).collect(_target())

    assert result.http_status == 200
    assert result.final_url == "https://www.example.org/final"
    assert result.redirect_chain == ["https://example.com/"]
    assert [request.url.host for request in captured] == [PUBLIC_IP, "104.18.2.24"]
    assert [request.headers["host"] for request in captured] == [
        "example.com",
        "www.example.org",
    ]
    assert [request.extensions["sni_hostname"] for request in captured] == [
        "example.com",
        "www.example.org",
    ]


def test_non_default_port_is_preserved_in_host_header() -> None:
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=lambda hostname: [PUBLIC_IP],
            tls_probe=_tls_ok,
        ).collect(_target("https://example.com:8443/status"))

    assert result.http_status == 200
    assert captured[0].url.port == 8443
    assert captured[0].headers["host"] == "example.com:8443"


def test_collector_returns_structured_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=lambda hostname: [PUBLIC_IP],
            tls_probe=_tls_ok,
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
            tls_probe=_tls_ok,
        ).collect(_target())

    assert calls == 0
    assert result.http_status is None
    assert result.errors == [
        "Target validation failed: non-public address blocked: 127.0.0.1"
    ]


def test_collector_blocks_mixed_public_and_private_results() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(200, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=lambda hostname: [PUBLIC_IP, "10.0.0.5"],
            tls_probe=_tls_ok,
        ).collect(_target())

    assert calls == 0
    assert result.errors == [
        "Target validation failed: non-public address blocked: 10.0.0.5"
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
            tls_probe=_tls_ok,
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
            tls_probe=_tls_ok,
        ).collect(_target())

    assert result.http_status is None
    assert result.errors == ["Target validation failed: unavailable"]


def test_http_target_skips_tls_probe() -> None:
    tls_calls = 0

    def tls_probe(hostname: str, address: str, port: int, timeout: int) -> int:
        nonlocal tls_calls
        tls_calls += 1
        return 90

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, request=request)
    )
    with httpx.Client(transport=transport) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=lambda hostname: [PUBLIC_IP],
            tls_probe=tls_probe,
        ).collect(_target("http://example.com"))

    assert result.http_status == 200
    assert result.tls_days_remaining is None
    assert tls_calls == 0


def test_tls_failure_preserves_http_evidence() -> None:
    def failing_tls(
        hostname: str,
        address: str,
        port: int,
        timeout: int,
    ) -> int:
        raise OSError("handshake failed")

    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, request=request)
    )
    with httpx.Client(transport=transport) as client:
        result = WebsiteCollector(
            client=client,
            dns_resolver=lambda hostname: [PUBLIC_IP],
            tls_probe=failing_tls,
        ).collect(_target())

    assert result.http_status == 200
    assert result.tls_days_remaining is None
    assert result.errors == ["TLS inspection failed: handshake failed"]
