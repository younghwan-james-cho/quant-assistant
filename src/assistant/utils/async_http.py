# src/assistant/utils/async_http.py
from __future__ import annotations

import aiohttp
from aiohttp_retry import RetryClient, ExponentialRetry

# CORRECTED: Changed the User-Agent to mimic a standard web browser.
DEFAULT_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"


class AsyncHttpClient:
    """Resilient asynchronous HTTP client with retries and a default User-Agent."""

    def __init__(self) -> None:
        retry_options = ExponentialRetry(attempts=3)

        headers = {"User-Agent": DEFAULT_UA}
        self.session = RetryClient(retry_options=retry_options, headers=headers)
        self._closed = False

    async def __aenter__(self) -> "AsyncHttpClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def get(
        self, url: str, params: dict | None = None, headers: dict | None = None
    ) -> aiohttp.ClientResponse:
        """Perform an asynchronous GET request."""
        response = await self.session.get(url, params=params, headers=headers, timeout=20)
        response.raise_for_status()
        return response

    async def post(
        self, url: str, headers: dict | None = None, json: dict | None = None
    ) -> aiohttp.ClientResponse:
        """Perform an asynchronous POST request."""
        response = await self.session.post(url, headers=headers, json=json, timeout=120)
        response.raise_for_status()
        return response

    async def close(self) -> None:
        """Close the client session."""
        if not self._closed:
            await self.session.close()
            self._closed = True
