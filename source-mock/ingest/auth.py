"""OAuth client_credentials token minting + per-run caching."""
from __future__ import annotations

import json
import urllib.parse

from .transport import http_post as _default_http_post


class TokenError(Exception):
    """Raised when the token endpoint refuses to mint a token."""


class TokenProvider:
    """Mints and caches a ``write``-scoped bearer token for one CLI run."""

    def __init__(self, config, http_post=_default_http_post):
        self._config = config
        self._http_post = http_post
        self._token: str | None = None

    def get_token(self) -> str:
        """Return the cached token, minting one on first use."""
        if self._token is None:
            self._token = self._mint()
        return self._token

    def refresh(self) -> str:
        """Force a new mint (used after a 401)."""
        self._token = self._mint()
        return self._token

    def _mint(self) -> str:
        url = f"{self._config.base_url}/token"
        form = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
            "scope": self._config.scopes,
        }).encode("utf-8")
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        resp = self._http_post(url, form, headers)
        if resp.status != 200:
            raise TokenError(
                f"token mint failed (HTTP {resp.status}) from {url}: "
                f"{resp.body.decode('utf-8', 'replace')[:300]}"
            )
        try:
            payload = json.loads(resp.body.decode("utf-8"))
            return payload["access_token"]
        except (json.JSONDecodeError, KeyError) as e:
            raise TokenError(f"token response missing access_token: {e}")
