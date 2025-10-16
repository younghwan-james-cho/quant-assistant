from __future__ import annotations
from datetime import date
import os
from assistant.fetchers.fred_vix import latest_vix_close
from assistant.fetchers.alphavantage import global_quote
from assistant.fetchers.bls_cpi import upcoming_cpi_releases
from assistant.fetchers.arxiv_papers import latest_arxiv_qfin
from assistant.fetchers.semanticscholar import search_papers
from assistant.composer.builder import render_digest
from assistant.utils.dto import PriceSnapshot

def main():
    today = date.today().isoformat()
    vix = latest_vix_close()
    quotes: list[PriceSnapshot] = []
    if os.getenv("ALPHAVANTAGE_KEY"):
        for sym in ("SPY","QQQ"):
            try:
                quotes.append(global_quote(sym))
            except Exception as e:
                print(f"[warn] quote fetch failed: {e}")
    cpi   = upcoming_cpi_releases()
    arxiv = latest_arxiv_qfin(limit=10)
    s2    = search_papers("quantitative finance", limit=10)
    print(render_digest(today, quotes, vix, cpi, arxiv, s2))

if __name__ == "__main__": main()
