"""Helpers for normalising asynchronous fetcher results."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from aiohttp import ClientConnectorError, ClientResponseError

from assistant.utils.logging import logger

T = TypeVar("T")


def unwrap_result(
    result: object,
    expected_type: type[T],
    fallback: Callable[[], T],
    name: str,
    context: str | None = None,
) -> T:
    """Return a typed value or a fallback while logging anomalies."""
    if isinstance(result, expected_type):
        return result

    if isinstance(result, ClientConnectorError):
        logger.error("{name} service unreachable: {error}", name=name, error=result)
    elif isinstance(result, ClientResponseError):
        safe_url = result.request_info.url.with_query({}) if result.request_info else "unknown"
        message = getattr(result, "message", "")
        logger.error(
            "{name} returned HTTP {status} from {url}: {message}",
            name=name,
            status=result.status,
            url=safe_url,
            message=message,
        )
    elif isinstance(result, Exception):
        if context:
            logger.warning(
                "{name} fetch failed for {context}: {error}",
                name=name,
                context=context,
                error=result,
            )
        else:
            logger.warning("{name} fetch failed: {error}", name=name, error=result)
    else:
        details = f" for {context}" if context else ""
        logger.warning(
            "{name} returned unexpected payload type{details}: {type_name}; falling back to default.",
            name=name,
            details=details,
            type_name=type(result).__name__,
        )
    return fallback()
