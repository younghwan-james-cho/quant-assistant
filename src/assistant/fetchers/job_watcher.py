# src/assistant/fetchers/job_watcher.py
from __future__ import annotations
import asyncio
from typing import List, Optional, Tuple
from urllib.parse import urljoin
from pydantic import BaseModel
from bs4 import BeautifulSoup
from assistant.utils.async_http import AsyncHttpClient
from assistant.utils.logging import logger


class InternshipPosting(BaseModel):
    title: str
    location: str
    url: str


def _extract_job_details(listing) -> Optional[Tuple[str, str, str]]:
    """Extract job details from a single listing."""
    title_tag = listing.select_one(".job-title")
    location_tag = listing.select_one(".job-location")

    if not title_tag or not location_tag:
        return None

    title = title_tag.get_text(strip=True)
    location = location_tag.get_text(strip=True)
    url = listing.get("href")

    return title, location, url


def _filter_quant_internships(title: str, location: str) -> bool:
    """Filter for quant internships in APAC regions."""
    lower_title = title.lower()
    is_quant_intern = "quant" in lower_title and "intern" in lower_title
    apac_locations = [
        "Hong Kong",
        "Singapore",
        "Tokyo",
        "Seoul",
        "Sydney",
        "Shanghai",
    ]
    is_apac = any(loc in location for loc in apac_locations)
    return is_quant_intern and is_apac


def _parse_jane_street_html(html: str) -> List[InternshipPosting]:
    """Synchronous parsing logic for Jane Street career page."""
    soup = BeautifulSoup(html, "html.parser")
    if soup.select_one("main") is None:
        logger.error(
            "Jane Street careers page structure appears to have changed; 'main' container missing."
        )
        return []
    postings = []

    for listing in soup.select(".job-listing-item"):
        job_details = _extract_job_details(listing)
        if not job_details:
            continue

        title, location, url = job_details
        if not url:
            continue

        absolute_url = urljoin("https://www.janestreet.com", url)
        if _filter_quant_internships(title, location):
            postings.append(InternshipPosting(title=title, location=location, url=absolute_url))

    return postings


async def scrape_jane_street_internships(client: AsyncHttpClient) -> List[InternshipPosting]:
    """Scrape QR internship postings from the Jane Street careers page."""
    url = "https://www.janestreet.com/careers/engineering/"  # Example URL, needs verification
    try:
        response = await client.get(url)
        html = await response.text()

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _parse_jane_street_html, html)
    except Exception as e:
        logger.warning(f"Failed to scrape Jane Street internships: {e}")
        return []
