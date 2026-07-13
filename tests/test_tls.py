from datetime import UTC, datetime

import pytest

from watch.tls import calculate_days_remaining, inspect_tls_days_remaining


def test_calculate_days_remaining() -> None:
    now = datetime(2030, 1, 1, tzinfo=UTC)
    assert calculate_days_remaining("Jan 31 00:00:00 2030 GMT", now) == 30


def test_calculate_days_remaining_reports_expired_certificate() -> None:
    now = datetime(2030, 2, 2, tzinfo=UTC)
    assert calculate_days_remaining("Jan 31 00:00:00 2030 GMT", now) == -2


def test_inspector_uses_validated_address_and_hostname(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: dict[str, object] = {}

    class FakeTlsSocket:
        def __enter__(self) -> "FakeTlsSocket":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def getpeercert(self) -> dict[str, str]:
            return {"notAfter": "Jan 31 00:00:00 2030 GMT"}

    class FakeContext:
        def wrap_socket(
            self,
            raw_socket: object,
            server_hostname: str,
        ) -> FakeTlsSocket:
            observed["server_hostname"] = server_hostname
            observed["raw_socket"] = raw_socket
            return FakeTlsSocket()

    class FakeRawSocket:
        def __enter__(self) -> "FakeRawSocket":
            return self

        def __exit__(self, *args: object) -> None:
            return None

    def fake_create_connection(
        endpoint: tuple[str, int],
        timeout: int,
    ) -> FakeRawSocket:
        observed["endpoint"] = endpoint
        observed["timeout"] = timeout
        return FakeRawSocket()

    monkeypatch.setattr("watch.tls.socket.create_connection", fake_create_connection)
    monkeypatch.setattr("watch.tls.ssl.create_default_context", FakeContext)
    monkeypatch.setattr(
        "watch.tls.datetime",
        _FixedDatetime,
    )

    days = inspect_tls_days_remaining("example.com", "93.184.216.34", 443, 7)

    assert days == 30
    assert observed["endpoint"] == ("93.184.216.34", 443)
    assert observed["timeout"] == 7
    assert observed["server_hostname"] == "example.com"


class _FixedDatetime(datetime):
    @classmethod
    def now(cls, tz: object = None) -> datetime:
        return datetime(2030, 1, 1, tzinfo=UTC)
