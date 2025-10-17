# src/assistant/utils/dto.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

# --- Existing DTOs ---


@dataclass(frozen=True)
class PriceSnapshot:
    symbol: str
    price: float
    as_of: str


@dataclass(frozen=True)
class VixClose:
    date: str
    close: float


@dataclass(frozen=True)
class CpiRelease:
    date: str
    time_et: str
    url: Optional[str] = None


@dataclass(frozen=True)
class PaperItem:
    title: str
    authors: List[str]
    year: Optional[int]
    url: str


@dataclass(frozen=True)
class DigestContext:
    """A single object to hold all data for rendering the digest template."""

    date: str
    quotes: List[PriceSnapshot]
    vix: VixClose
    cpi: List[CpiRelease]
    arxiv: List[PaperItem]
    s2: List[PaperItem]
    # Add other fields as you implement the new modules
    # market_summary: str
    # alpha_idea: Optional[AlphaIdea]
    # ... and so on
