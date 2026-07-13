from __future__ import annotations

import socket
import ssl
from datetime import UTC, datetime
from math import floor
from typing import Any, cast


def calculate_days_remaining(not_after: str, now: datetime | None = None) -> int:
    """Convert an OpenSSL notAfter value into whole remaining days."""
    expiry_timestamp = ssl.cert_time_to_seconds(not_after)
    expiry = datetime.fromtimestamp(expiry_timestamp, tz=UTC)
    reference = now or datetime.now(UTC)
    return floor((expiry - reference).total_seconds() / 86_400)


def inspect_tls_days_remaining(
    hostname: str,
    address: str,
    port: int,
    timeout_seconds: int,
) -> int:
    """Inspect a certificate using a validated address and the hostname for SNI."""
    context = ssl.create_default_context()
    with socket.create_connection(
        (address, port),
        timeout=timeout_seconds,
    ) as raw_socket:
        with context.wrap_socket(raw_socket, server_hostname=hostname) as tls_socket:
            certificate = cast(dict[str, Any], tls_socket.getpeercert())

    not_after = certificate.get("notAfter")
    if not isinstance(not_after, str) or not not_after:
        raise ValueError("certificate did not include notAfter")
    return calculate_days_remaining(not_after)
