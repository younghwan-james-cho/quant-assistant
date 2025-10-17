# src/assistant/fetchers/bls_cpi.py
from __future__ import annotations
import asyncio
from typing import List
from contextlib import suppress
from aiohttp import ClientConnectorError, ClientResponseError
from bs4 import BeautifulSoup
from assistant.utils.async_http import AsyncHttpClient
from assistant.utils.dto import CpiRelease
import logging

logger = logging.getLogger(__name__)

BLS_CPI_SCHEDULE = "https://www.bls.gov/schedule/news_release/cpi.htm"


def _parse_cpi_html(html: str) -> List[CpiRelease]:
    """Synchronous parsing logic for CPI data."""
    soup = BeautifulSoup(html, "html.parser")
    releases: List[CpiRelease] = []
    for a in soup.select("a[href*='cpi_']"):
        text = a.get_text(strip=True)
        href = a.get("href")
        if any(ch.isdigit() for ch in text) and "," in text:
            url = f"https://www.bls.gov{href}" if href and href.startswith("/") else href
            releases.append(CpiRelease(date=text, time_et="08:30", url=url))
    return releases


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


async def upcoming_cpi_releases(client: AsyncHttpClient) -> List[CpiRelease]:
    """Scrape BLS CPI schedule asynchronously."""
    try:
        response = await client.get(BLS_CPI_SCHEDULE, headers=headers)
        html = await response.text()
    except ClientResponseError as exc:
        safe_url = exc.request_info.url.with_query({}) if exc.request_info else "unknown"
        body = ""
        response_obj = getattr(exc, "response", None)
        if response_obj is not None:
            with suppress(Exception):
                body = (await response_obj.text())[:200]
        logger.warning(
            "BLS CPI schedule returned HTTP %s (%s): %s",
            exc.status,
            safe_url,
            body,
        )
        return []
    except ClientConnectorError as exc:
        logger.error(f"BLS CPI schedule unreachable: {exc}")
        return []
    except Exception as exc:
        logger.warning(f"Failed to fetch CPI schedule: {exc}")
        return []

    loop = asyncio.get_running_loop()
    try:
        return await loop.run_in_executor(None, _parse_cpi_html, html)
    except Exception as e:
        logger.error(f"Error occurred while parsing CPI HTML: {e}")
        return []
