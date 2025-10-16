# src/assistant/fetchers/fred_vix.py
from __future__ import annotations
import os
from typing import Optional
from assistant.utils.http import HttpClient
from assistant.utils.dto import VixClose

FRED_SERIES_URL = "https://api.stlouisfed.org/fred/series/observations"

def latest_vix_close(api_key: Optional[str] = None) -> VixClose:
    """Fetch latest VIXCLS daily close from FRED; api_key optional for JSON."""
    key = api_key or os.getenv("FRED_API_KEY")
    params = {
        "series_id": "VIXCLS",
        "file_type": "json",
    }
    if key:
        params["api_key"] = key
    client = HttpClient()
    r = client.get(FRED_SERIES_URL, params=params)
    data = r.json()
    obs = data.get("observations", [])
    if not obs:
        raise RuntimeError("FRED: no observations returned")
    last = obs[-1]
    date = last.get("date")
    value_str = last.get("value")
    try:
        value = float(value_str)
    except Exception:
        raise RuntimeError(f"FRED: invalid value {value_str!r} for {date}")
    return VixClose(date=date, close=value)