# src/assistant/fetchers/bls_cpi.py
from __future__ import annotations
from typing import List
from bs4 import BeautifulSoup  # optional: if you prefer not to add bs4, we can parse manually
from assistant.utils.http import HttpClient
from assistant.utils.dto import CpiRelease

BLS_CPI_SCHEDULE = "https://www.bls.gov/schedule/news_release/cpi.htm"

def upcoming_cpi_releases() -> List[CpiRelease]:
    """Scrape BLS CPI schedule and extract upcoming dates (08:30 ET)."""
    client = HttpClient()
    r = client.get(BLS_CPI_SCHEDULE)
    html = r.text

    # Minimal parse: we try to find date strings in the schedule table.
    # To avoid adding bs4, you can do simple regex parsing; for clarity we use bs4 here.
    soup = BeautifulSoup(html, "html.parser")
    releases: List[CpiRelease] = []
    for a in soup.select("a[href*='cpi_']"):
        text = a.get_text(strip=True)
        href = a.get("href")
        # Heuristic: if text looks like a month day (e.g., "November 13, 2025")
        if any(ch.isdigit() for ch in text) and "," in text:
            releases.append(CpiRelease(date=text, time_et="08:30", url=f"https://www.bls.gov{href}" if href and href.startswith("/") else href))
    return releases