"""Lightweight synchronous HTTP utilities used by fetchers and tests."""

from __future__ import annotations

from typing import Any, Mapping

import requests

DEFAULT_TIMEOUT: tuple[float, float] = (3.05, 27)
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_UA: str = "quant-assistant-http/1.0"


class HttpClient:
    """Simple wrapper around ``requests`` for deterministic tests."""

    def __init__(
        self,
        *,
        timeout: tuple[float, float] = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_UA,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", user_agent)

    def get(
        self,
        url: str,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, Any] | None = None,
    ) -> requests.Response:
        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response

    def close(self) -> None:
        self.session.close()
