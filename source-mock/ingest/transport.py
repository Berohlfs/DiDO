"""Minimal HTTP POST transport (stdlib urllib) + a fakeable seam.

Both ``auth`` and ``sender`` accept an ``http_post`` callable with this
signature so tests can inject a fake transport with no real network.
"""
from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class HttpResponse:
    status: int
    headers: dict
    body: bytes


def http_post(url: str, data: bytes, headers: dict) -> HttpResponse:
    """POST ``data`` to ``url`` and return an HttpResponse (never raises on HTTP errors)."""
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return HttpResponse(resp.status, dict(resp.headers), resp.read())
    except urllib.error.HTTPError as e:
        return HttpResponse(e.code, dict(e.headers), e.read())


def get_header(headers: dict, name: str):
    """Case-insensitive header lookup; returns the value or None."""
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None
