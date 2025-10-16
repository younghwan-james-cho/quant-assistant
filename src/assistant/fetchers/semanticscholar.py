# src/assistant/fetchers/semanticscholar.py
from __future__ import annotations
from typing import List
from assistant.utils.http import HttpClient
from assistant.utils.dto import PaperItem

SEMANTIC_SCHOLAR_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"

def search_papers(query: str, limit: int = 10, fields: str = "title,authors,year,url") -> List[PaperItem]:
    client = HttpClient()
    params = {"query": query, "limit": limit, "fields": fields}
    r = client.get(SEMANTIC_SCHOLAR_SEARCH, params=params)
    data = r.json().get("data", [])
    items: List[PaperItem] = []
    for p in data:
        title = p.get("title") or ""
        url = p.get("url") or ""
        authors = [a.get("name") for a in p.get("authors", []) if a.get("name")]
        year = p.get("year")
        items.append(PaperItem(title=title, authors=authors, year=year, url=url))
    return items