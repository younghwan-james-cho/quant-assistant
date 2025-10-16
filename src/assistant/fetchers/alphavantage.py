# src/assistant/fetchers/alphavantage.py
from __future__ import annotations
import os
from typing import Optional
from assistant.utils.http import HttpClient
from assistant.utils.dto import PriceSnapshot

ALPHAVANTAGE_URL = "https://www.alphavantage.co/query"

def global_quote(symbol: str, api_key: Optional[str] = None) -> PriceSnapshot:
    """Fetch minimal GLOBAL_QUOTE snapshot for a symbol (respect free rate constraints)."""
    key = api_key or os.getenv("ALPHAVANTAGE_KEY")
    if not key:
        raise RuntimeError("Alpha Vantage: missing ALPHAVANTAGE_KEY")
    params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": key}
    client = HttpClient()
    r = client.get(ALPHAVANTAGE_URL, params=params)
    data = r.json().get("Global Quote", {})
    price_str = data.get("05. price")
    ts_str = data.get("07. latest trading day") or data.get("10. latest trading day")
    if not price_str or not ts_str:
        raise RuntimeError(f"Alpha Vantage: incomplete quote for {symbol}: {data!r}")
    try:
        price = float(price_str)
    except Exception:
        raise RuntimeError(f"Alpha Vantage: invalid price {price_str!r} for {symbol}")
    return PriceSnapshot(symbol=symbol, price=price, as_of=ts_str)