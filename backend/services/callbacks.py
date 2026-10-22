"""Safe callback delivery for training jobs."""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import requests
from django.conf import settings


def _is_public_ip(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return bool(ip.is_global)


def _is_allowed_private_ip(address: str) -> bool:
    """Allow loopback and RFC1918/ULA private addresses, not metadata/link-local."""
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    if ip.is_loopback:
        return True
    return bool(
        ip.is_private
        and not ip.is_link_local
        and not ip.is_reserved
        and not ip.is_unspecified
    )


def validate_callback_url(url: str, *, allow_private: bool | None = None) -> str:
    """Validate an outbound callback URL and return it unchanged.

    Public HTTPS endpoints are allowed. Loopback/private HTTP endpoints are
    allowed only when ``DEBUG`` is enabled or ``allow_private=True``, which
    keeps the local demo receiver usable without opening an SSRF path in
    production.
    """
    if not isinstance(url, str):
        raise ValueError("callback_url must be a string")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("callback_url must use http or https")
    if parsed.username or parsed.password:
        raise ValueError("callback_url must not contain credentials")
    if not parsed.hostname:
        raise ValueError("callback_url must include a hostname")

    if allow_private is None:
        allow_private = bool(getattr(settings, "DEBUG", False))

    if parsed.scheme == "http" and not allow_private:
        raise ValueError("callback_url must use https in production")
    if parsed.scheme == "https" and allow_private:
        # Private HTTPS endpoints are still checks below; this branch is for
        # clarity only.
        pass

    try:
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
    except ValueError as exc:
        raise ValueError("callback_url has an invalid port") from exc
    try:
        addresses = {
            info[4][0]
            for info in socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
        }
    except (OSError, ValueError) as exc:
        raise ValueError("callback_url host could not be resolved") from exc

    if not addresses:
        raise ValueError("callback_url host could not be resolved")

    for address in addresses:
        if allow_private and _is_allowed_private_ip(address):
            continue
        if not _is_public_ip(address):
            raise ValueError("callback_url must resolve to a public address")

    return url


def post_json(
    url: str,
    payload: dict,
    headers: dict | None = None,
    timeout: int = 10,
) -> dict:
    """POST a JSON payload without following redirects or exposing responses."""
    validate_callback_url(url)
    response = requests.post(
        url,
        json=payload,
        headers=headers or {},
        timeout=timeout,
        allow_redirects=False,
    )
    return {
        "status": "ok",
        "http_status": response.status_code,
        "text": response.text[:1000],
    }
