from __future__ import annotations
from typing import List
import feedparser
from assistant.utils.dto import PaperItem

ARXIV_QFIN_FEED = "https://export.arxiv.org/rss/q-fin"

def latest_arxiv_qfin(limit: int = 10) -> List[PaperItem]:
    """Fetch latest q-fin papers via arXiv RSS."""
    feed = feedparser.parse(ARXIV_QFIN_FEED)
    items: List[PaperItem] = []
    for entry in feed.entries[:limit]:
        # Support both dict-like and attribute-style entries
        get = entry.get if hasattr(entry, "get") else lambda k, default=None: getattr(entry, k, default)

        title = (get("title", "") or "").strip()
        link = get("link", "") or ""
        authors_raw = get("authors", []) or []
        authors = [
            a.get("name") if hasattr(a, "get") else getattr(a, "name", None)
            for a in authors_raw
        ]
        authors = [a for a in authors if a]

        year = None
        published_parsed = get("published_parsed")
        if published_parsed:
            year = published_parsed.tm_year

        items.append(PaperItem(title=title, authors=authors, year=year, url=link))
    return items