# src/assistant/fetchers/fred_vix.py
from __future__ import annotations
from typing import Optional
from contextlib import suppress

from aiohttp import ClientConnectorError, ClientResponseError

from assistant.config import settings
from assistant.utils.async_http import AsyncHttpClient
from assistant.utils.dto import VixClose
from assistant.utils.logging import logger


async def latest_vix_close(client: AsyncHttpClient) -> Optional[VixClose]:
    """Fetch latest VIXCLS daily close from FRED asynchronously."""
    if not settings.FRED_API_KEY:
        return None

    params = {
        "series_id": "VIXCLS",
        "file_type": "json",
        "api_key": settings.FRED_API_KEY,
    }

    try:
        response = await client.get(settings.api_endpoints.fred, params=params)
        data = await response.json()
    except ClientResponseError as exc:
        safe_url = exc.request_info.url.with_query({}) if exc.request_info else "unknown"
        body = ""
        if exc.response is not None:
            with suppress(Exception):
                body = (await exc.response.text())[:200]
        logger.warning(
            "FRED request failed with status %s (%s): %s",
            exc.status,
            safe_url,
            body,
        )
        return None
    except ClientConnectorError as exc:
        logger.error(f"FRED endpoint unreachable: {exc}")
        return None
    except Exception as exc:
        logger.warning(f"Failed to fetch VIX from FRED: {exc}")
        return None

    obs = data.get("observations", [])
    if not obs:
        logger.warning("FRED response did not contain observations.")
        return None

    last = obs[-1]
    date = last.get("date")
    value_str = last.get("value")
    try:
        # FRED sometimes returns '.' for value on non-trading days
        if value_str == ".":
            logger.warning("FRED returned '.' for VIX value; skipping datum.")
            return None
        value = float(value_str)
    except (ValueError, TypeError):
        logger.warning(f"FRED VIX close could not be parsed: {value_str}")
        return None

    return VixClose(date=date, close=value)
