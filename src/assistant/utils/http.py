# src/assistant/utils/http.py
from __future__ import annotations
import time
from typing import Optional, Dict, Any
import requests

DEFAULT_TIMEOUT = (5, 20)  # (connect, read) seconds
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 1.5
DEFAULT_UA = "quant-assistant/0.1 (+https://example.com)"

class HttpClient:
    """Simple HTTP client with timeouts, retries, backoff, and a default User-Agent."""

    def __init__(
        self,
        timeout: tuple[int, int] = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session = requests.Session()
        base_headers = {"User-Agent": DEFAULT_UA}
        if headers:
            base_headers.update(headers)
        self.session.headers.update(base_headers)

    def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                r = self.session.get(url, params=params, timeout=self.timeout)
                r.raise_for_status()
                return r
            except Exception as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * attempt)
                else:
                    raise
        # Defensive: should never get here
        assert last_exc is not None
        raise last_exc