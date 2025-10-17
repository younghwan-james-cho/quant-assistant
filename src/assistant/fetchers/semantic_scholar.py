from __future__ import annotations

from contextlib import suppress
from typing import Any, Dict, Iterable, List, Mapping, Optional

import requests
from aiohttp import ClientConnectorError, ClientResponseError

from assistant.config import settings
from assistant.utils.async_http import AsyncHttpClient
from assistant.utils.dto import PaperItem
from assistant.utils.http import HttpClient
from assistant.utils.logging import logger

SEMANTIC_SCHOLAR_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"
DEFAULT_FIELDS = "title,authors,year,url"


def _make_params(query: str, limit: int, fields: str) -> Dict[str, Any]:
    return {"query": query, "limit": limit, "fields": fields}


def _api_headers() -> Optional[Dict[str, str]]:
    key = settings.SEMANTIC_SCHOLAR_KEY
    if key:
        return {"x-api-key": key}
    return None


def _build_items(payload: Mapping[str, Any] | None) -> List[PaperItem]:
    items: List[PaperItem] = []
    if not payload:
        return items

    entries: Iterable[Any] = payload.get("data", [])
    for entry in entries:
        if not isinstance(entry, Mapping):
            continue
        title = entry.get("title", "")
        url = entry.get("url", "")
        authors = [a.get("name") for a in entry.get("authors", []) if a and a.get("name")]
        year = entry.get("year")
        items.append(PaperItem(title=title, authors=authors, year=year, url=url))
    return items


def _maybe_log_rate_limit(status: int | None) -> None:
    if status == 429:
        logger.warning(
            "Semantic Scholar API rate limit encountered; ensure the request volume"
            " respects the service limits and that the API key has sufficient quota."
        )


def search_papers(
    query: str,
    limit: int = 10,
    fields: str = DEFAULT_FIELDS,
    client: HttpClient | None = None,
) -> List[PaperItem]:
    """Synchronous paper search used by tests and simple scripts."""
    params = _make_params(query, limit, fields)
    managed_client = client or HttpClient()
    data: Mapping[str, Any] | None = None
    try:
        response = managed_client.get(
            SEMANTIC_SCHOLAR_SEARCH,
            params=params,
            headers=_api_headers(),
        )
        data = response.json()
    except requests.RequestException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        _maybe_log_rate_limit(status)
        logger.warning(f"Semantic Scholar request failed: {exc}")
        return []
    except ValueError as exc:
        logger.warning(f"Semantic Scholar response JSON parse failed: {exc}")
        return []
    finally:
        if client is None and hasattr(managed_client, "close"):
            managed_client.close()
    return _build_items(data)


async def search_papers_async(
    client: AsyncHttpClient,
    query: str,
    limit: int = 10,
    fields: str = DEFAULT_FIELDS,
) -> List[PaperItem]:
    """Asynchronous Semantic Scholar search for the digest workflow."""
    params = _make_params(query, limit, fields)
    try:
        response = await client.get(
            SEMANTIC_SCHOLAR_SEARCH,
            params=params,
            headers=_api_headers(),
        )
        data = await response.json()
    except ClientResponseError as exc:
        safe_url = exc.request_info.url.with_query({}) if exc.request_info else "unknown"
        body = ""
        if exc.response is not None:
            with suppress(Exception):
                body = (await exc.response.text())[:200]
        _maybe_log_rate_limit(exc.status)
        logger.warning(
            "Semantic Scholar returned HTTP %s for query '%s' (%s): %s",
            exc.status,
            query,
            safe_url,
            body,
        )
        return []
    except ClientConnectorError as exc:
        logger.error(f"Semantic Scholar endpoint unreachable: {exc}")
        return []
    except Exception as exc:  # pragma: no cover - keep digest resilient
        logger.warning(f"Semantic Scholar search failed for '{query}': {exc}")
        return []

    return _build_items(data)


__all__ = ["search_papers", "search_papers_async"]
