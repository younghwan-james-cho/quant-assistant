# src/assistant/fetchers/alphavantage.py
from __future__ import annotations

import os
from contextlib import suppress
from typing import Dict, Optional

import requests
from aiohttp import ClientConnectorError, ClientResponseError

from assistant.config import settings
from assistant.utils.async_http import AsyncHttpClient
from assistant.utils.dto import PriceSnapshot
from assistant.utils.http import HttpClient
from assistant.utils.logging import logger

ALPHAVANTAGE_URL = "https://www.alphavantage.co/query"

if settings.ALPHAVANTAGE_KEY and "ALPHAVANTAGE_KEY" not in os.environ:
    os.environ["ALPHAVANTAGE_KEY"] = settings.ALPHAVANTAGE_KEY


def _has_api_message(payload: Dict | None, symbol: str) -> bool:
    if not isinstance(payload, dict):
        return False

    note = payload.get("Note")
    if note:
        logger.warning(
            "AlphaVantage throttled request for {symbol}: {note}",
            symbol=symbol,
            note=note,
        )
        return True

    error_message = payload.get("Error Message")
    if error_message:
        logger.warning(
            "AlphaVantage rejected request for {symbol}: {error}",
            symbol=symbol,
            error=error_message,
        )
        return True

    return False


def _parse_quote(payload: dict, symbol: str) -> Optional[PriceSnapshot]:
    if _has_api_message(payload, symbol):
        return None

    quote = payload.get("Global Quote", {}) if isinstance(payload, dict) else {}
    price_str = quote.get("05. price")
    ts_str = quote.get("07. latest trading day")
    if not price_str or not ts_str:
        logger.warning(
            "AlphaVantage returned incomplete data for {symbol}: {payload}",
            symbol=symbol,
            payload=payload,
        )
        return None
    try:
        price = float(price_str)
    except (ValueError, TypeError):
        logger.warning(
            "AlphaVantage price parse failed for {symbol}: {price_str}",
            symbol=symbol,
            price_str=price_str,
        )
        return None
    return PriceSnapshot(symbol=symbol, price=price, as_of=ts_str)


def global_quote(symbol: str, client: HttpClient | None = None) -> Optional[PriceSnapshot]:
    """Synchronous helper that surfaces missing API keys via RuntimeError."""
    api_key = os.getenv("ALPHAVANTAGE_KEY")
    if not api_key:
        raise RuntimeError("missing ALPHAVANTAGE_KEY")

    params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key}
    managed_client = client or HttpClient()
    data: dict = {}
    try:
        response = managed_client.get(ALPHAVANTAGE_URL, params=params)
        data = response.json()
    except requests.RequestException as exc:
        logger.warning(
            "AlphaVantage request failed for {symbol}: {error}",
            symbol=symbol,
            error=exc,
        )
        return None
    except ValueError as exc:
        logger.warning(
            "AlphaVantage response JSON decode failed for {symbol}: {error}",
            symbol=symbol,
            error=exc,
        )
        return None
    finally:
        if client is None:
            managed_client.close()
    return _parse_quote(data, symbol)


async def global_quote_async(client: AsyncHttpClient, symbol: str) -> Optional[PriceSnapshot]:
    """Asynchronous GLOBAL_QUOTE fetch used by the digest pipeline."""
    if not settings.ALPHAVANTAGE_KEY:
        return None

    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": settings.ALPHAVANTAGE_KEY,
    }

    data: dict = {}
    try:
        response = await client.get(ALPHAVANTAGE_URL, params=params)
        data = await response.json()
    except ClientResponseError as exc:
        safe_url = exc.request_info.url.with_query({}) if exc.request_info else "unknown"
        body = ""
        response_obj = getattr(exc, "response", None)
        if response_obj is not None:
            with suppress(Exception):
                body = (await response_obj.text())[:200]
        logger.warning(
            "AlphaVantage returned HTTP {status} for {symbol} ({url}): {body}",
            status=exc.status,
            symbol=symbol,
            url=safe_url,
            body=body,
        )
        return None
    except ClientConnectorError as exc:
        logger.error("AlphaVantage endpoint unreachable: {error}", error=exc)
        return None
    except Exception as exc:
        logger.warning(
            "AlphaVantage quote fetch failed for {symbol}: {error}",
            symbol=symbol,
            error=exc,
        )
        return None

    return _parse_quote(data, symbol)
