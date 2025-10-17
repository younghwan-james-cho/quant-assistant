from __future__ import annotations
from datetime import date
import os

from assistant.fetchers.fred_vix import latest_vix_close
from assistant.fetchers.alphavantage import global_quote
from assistant.fetchers.bls_cpi import upcoming_cpi_releases
from assistant.fetchers.arxiv_papers import latest_arxiv_qfin
from assistant.fetchers.semanticscholar import search_papers
from assistant.composer.builder import render_digest
from assistant.utils.dto import PriceSnapshot, VixClose


def main():
    today = date.today().isoformat()

    # VIX with fallback if FRED api_key missing or network fails
    try:
        vix = latest_vix_close()
    except Exception as e:
        print(f"[warn] VIX fetch failed: {e}")
        vix = VixClose(date=today, close=0.0)

    # Quotes (optional; only if ALPHAVANTAGE_KEY is set)
    quotes: list[PriceSnapshot] = []
    if os.getenv("ALPHAVANTAGE_KEY"):
        for sym in ("SPY", "QQQ"):
            try:
                quotes.append(global_quote(sym))
            except Exception as e:
                print(f"[warn] quote fetch failed for {sym}: {e}")

    # CPI schedule
    try:
        cpi = upcoming_cpi_releases()
    except Exception as e:
        print(f"[warn] CPI schedule parse failed: {e}")
        cpi = []

    # Papers
    try:
        arxiv = latest_arxiv_qfin(limit=10)
    except Exception as e:
        print(f"[warn] arXiv fetch failed: {e}")
        arxiv = []

    try:
        s2 = search_papers("quantitative finance", limit=10)
    except Exception as e:
        print(f"[warn] Semantic Scholar fetch failed: {e}")
        s2 = []

    md = render_digest(today, quotes, vix, cpi, arxiv, s2)
    print(md)

    # Attempt to send digest if DIGEST_TO is configured.
    to = os.getenv("DIGEST_TO")
    if to:
        html = md.replace("\n", "<br/>")
        try:
            from assistant.senders.smtp_sender import send_email as smtp_send

            smtp_send(to=to, subject="Daily Quant Digest", html_or_md=html)
            print("[info] sent digest via SMTP sender")
        except Exception as e:
            print(f"[warn] smtp send failed: {e}")
            # Fallback: Resend
            try:
                from assistant.senders.resend_sender import send_email_resend

                send_email_resend(to=to, subject="Daily Quant Digest", html_or_md=html)
                print("[info] sent digest via Resend sender")
            except Exception as e2:
                print(f"[error] resend send failed: {e2}")


if __name__ == "__main__":
    main()
