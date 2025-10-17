# src/assistant/fetchers/news_fetcher.py
from __future__ import annotations
from typing import List, Dict
from contextlib import suppress
from pydantic import BaseModel
from assistant.config import settings
from assistant.utils.async_http import AsyncHttpClient
from assistant.utils.logging import logger
import aiohttp
import json
from cachetools import TTLCache
from aiohttp import ClientConnectorError, ClientResponseError

# Create a cache with a TTL of 15 minutes
cache = TTLCache(maxsize=100, ttl=900)


class NewsArticle(BaseModel):
    title: str
    url: str


async def fetch_financial_news(client: AsyncHttpClient) -> List[NewsArticle]:
    """Fetch top business news from NewsAPI.org.

    Results are cached for fifteen minutes to avoid hammering the upstream API
    during repeated dry runs.
    """
    try:
        cache_key = "__financial_news__"
        cached = cache.get(cache_key)
        if cached:
            return [NewsArticle(**item) for item in cached]

        params = {
            "apiKey": settings.NEWS_API_KEY,
            "q": settings.fetcher_settings.news_api.query,
            "language": settings.fetcher_settings.news_api.language,
            "sortBy": settings.fetcher_settings.news_api.sort_by,
            "pageSize": settings.fetcher_settings.news_api.page_size,
        }
        response = await client.get(settings.api_endpoints.news_api, params=params)
        data = await response.json()

        raw_articles = data.get("articles", [])
        articles = [NewsArticle(title=a["title"], url=a["url"]) for a in raw_articles]
        cache[cache_key] = [article.dict() for article in articles]
        return articles
    except ClientResponseError as exc:
        safe_url = exc.request_info.url.with_query({}) if exc.request_info else "unknown"
        body = ""
        response_obj = getattr(exc, "response", None)
        if response_obj is not None:
            with suppress(Exception):
                body = (await response_obj.text())[:200]
        logger.warning(
            "NewsAPI returned HTTP %s (%s): %s",
            exc.status,
            safe_url,
            body,
        )
        return []
    except ClientConnectorError as exc:
        logger.error(f"NewsAPI endpoint unreachable: {exc}")
        return []
    except Exception as e:
        logger.warning(f"Failed to fetch financial news: {e}")
        return []


async def fetch_news(api_key: str, query: str) -> List[Dict]:
    """
    Fetch news articles from the NewsAPI with caching.

    Args:
        api_key (str): API key for NewsAPI.
        query (str): Search query.

    Returns:
        List[Dict]: List of news articles.
    """
    if query in cache:
        return cache[query]

    url = "https://newsapi.org/v2/everything"
    params = {"q": query, "apiKey": api_key}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, params=params) as response:
                if response.status == 429:
                    logger.warning("Rate limit exceeded for NewsAPI.")
                    return []
                elif response.status != 200:
                    logger.error(
                        f"NewsAPI call failed with status code {response.status}: {response.reason}"
                    )
                    return []

                try:
                    data = await response.json()
                    articles = data.get("articles", [])
                    if not articles:
                        logger.warning("No articles found in NewsAPI response.")
                    cache[query] = articles
                    return articles
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode JSON response from NewsAPI: {e}")
                    return []
        except aiohttp.ClientError as e:
            logger.error(f"HTTP client error occurred while fetching news: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error occurred while fetching news: {e}")
            return []
