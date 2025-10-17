# src/assistant/fetchers/arxiv_papers.py
from __future__ import annotations

from contextlib import suppress
from typing import Iterable, List

from aiohttp import ClientConnectorError, ClientResponseError
from cachetools import TTLCache
import feedparser

from assistant.config import settings
from assistant.utils.async_http import AsyncHttpClient
from assistant.utils.dto import PaperItem
from assistant.utils.logging import logger

_ARXIV_CACHE = TTLCache(maxsize=32, ttl=900)


def _entry_get(entry, key, default=None):
    if hasattr(entry, key):
        return getattr(entry, key)
    if isinstance(entry, dict):
        return entry.get(key, default)
    if hasattr(entry, "__getitem__"):
        with suppress(Exception):
            return entry[key]
    return default


def _extract_authors(raw: Iterable | None) -> list[str]:
    authors: list[str] = []
    if not raw:
        return authors
    for entry in raw:
        name = None
        if isinstance(entry, dict):
            name = entry.get("name")
        else:
            name = getattr(entry, "name", None) or getattr(entry, "title", None)
            if not name:
                with suppress(Exception):
                    representation = str(entry).strip()
                    if representation:
                        name = representation
        if name:
            authors.append(name)
    return authors


def _to_papers(entries, limit: int) -> List[PaperItem]:
    items: List[PaperItem] = []
    if not entries:
        return items
    for entry in list(entries)[:limit]:
        title = (_entry_get(entry, "title", "") or "").strip()
        url = _entry_get(entry, "link") or _entry_get(entry, "id") or ""
        published = _entry_get(entry, "published_parsed")
        year = getattr(published, "tm_year", None) if published else None
        authors = _extract_authors(_entry_get(entry, "authors", []))
        items.append(PaperItem(title=title, authors=authors, year=year, url=url))
    return items


def _normalise_limit(limit: int | None) -> int:
    configured = settings.fetcher_settings.arxiv.max_results
    return limit if limit is not None else configured


def latest_arxiv_qfin(limit: int | None = None) -> List[PaperItem]:
    """Synchronous helper primarily used by tests to fetch arXiv q-fin entries."""
    resolved_limit = _normalise_limit(limit)
    cache_key = ("sync", resolved_limit)
    cached = _ARXIV_CACHE.get(cache_key)
    if cached is not None:
        return cached

    try:
        feed = feedparser.parse(settings.api_endpoints.arxiv_qfin)
    except Exception as exc:  # pragma: no cover - unexpected network/parser failure
        logger.warning(f"Failed to fetch arXiv feed: {exc}")
        return []

    papers = _to_papers(getattr(feed, "entries", []), resolved_limit)
    _ARXIV_CACHE[cache_key] = papers
    return papers


async def latest_arxiv_qfin_async(
    client: AsyncHttpClient, limit: int | None = None
) -> List[PaperItem]:
    """Asynchronous variant used by the production digest workflow."""
    resolved_limit = _normalise_limit(limit)
    cache_key = ("async", resolved_limit)
    cached = _ARXIV_CACHE.get(cache_key)
    if cached is not None:
        return cached

    try:
        response = await client.get(settings.api_endpoints.arxiv_qfin)
        rss_text = await response.text()
    except ClientResponseError as exc:
        safe_url = exc.request_info.url.with_query({}) if exc.request_info else "unknown"
        body = ""
        response_obj = getattr(exc, "response", None)
        if response_obj is not None:
            with suppress(Exception):
                body = (await response_obj.text())[:200]
        logger.warning(
            "arXiv returned HTTP %s for query '%s' (%s): %s",
            exc.status,
            settings.fetcher_settings.arxiv.query,
            safe_url,
            body,
        )
        return []
    except ClientConnectorError as exc:
        logger.error(f"arXiv endpoint unreachable: {exc}")
        return []
    except Exception as exc:  # pragma: no cover - broad to keep digest alive
        logger.warning(f"Failed to fetch arXiv q-fin feed: {exc}")
        return []

    feed = feedparser.parse(rss_text)
    papers = _to_papers(getattr(feed, "entries", []), resolved_limit)
    _ARXIV_CACHE[cache_key] = papers
    return papers
