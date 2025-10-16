# src/assistant/utils/dto.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

@dataclass(frozen=True)
class PriceSnapshot:
    symbol: str
    price: float
    as_of: str  # ISO 8601 string

@dataclass(frozen=True)
class VixClose:
    date: str     # YYYY-MM-DD
    close: float  # daily close

@dataclass(frozen=True)
class CpiRelease:
    date: str     # YYYY-MM-DD
    time_et: str  # HH:MM ET
    url: Optional[str] = None

@dataclass(frozen=True)
class PaperItem:
    title: str
    authors: List[str]
    year: Optional[int]
    url: str