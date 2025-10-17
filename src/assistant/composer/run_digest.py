# src/assistant/composer/run_digest.py
from __future__ import annotations

import asyncio
import os
from datetime import date
from html import escape

# Foundational imports
from assistant.config import settings
from assistant.composer.builder import render_digest
from assistant.utils.logging import logger
from assistant.utils.async_http import AsyncHttpClient
from assistant.utils.results import unwrap_result

# DTOs and Models, including the new DigestContext
from assistant.utils.dto import PriceSnapshot, VixClose, DigestContext
# from assistant.analyzers.alpha_generator import AlphaIdea
# from assistant.fetchers.news_fetcher import NewsArticle
# from assistant.fetchers.interview_coach import InterviewProblem
# from assistant.fetchers.job_watcher import InternshipPosting

# Fetcher imports
from assistant.fetchers.fred_vix import latest_vix_close
from assistant.fetchers.alphavantage import global_quote_async
from assistant.fetchers.arxiv_papers import latest_arxiv_qfin_async
from assistant.fetchers.bls_cpi import upcoming_cpi_releases
from assistant.fetchers.semantic_scholar import search_papers_async
# Add other new fetcher imports here...

# Analyzer imports
# Add new analyzer imports here...

# Composer and Sender imports
from assistant.senders.smtp_sender import send_email


def _markdown_to_html(markdown_text: str) -> str:
    """Convert markdown content to HTML for email delivery."""
    try:
        import markdown  # type: ignore
    except ImportError:
        logger.warning(
            "The 'markdown' package is not installed; falling back to preformatted HTML output."
        )
        escaped = escape(markdown_text)
        return (
            "<pre style=\"font-family: 'SFMono-Regular', Menlo, monospace; white-space: pre-wrap;\">"
            f"{escaped}"
            "</pre>"
        )

    return markdown.markdown(markdown_text, extensions=["tables", "fenced_code"])


async def main():
    """Asynchronously fetches, analyzes, and sends the daily quant digest."""
    logger.info("Starting daily quant digest generation...")
    today = date.today().isoformat()

    if "PYTEST_CURRENT_TEST" in os.environ:
        settings.dry_run = True

    try:
        async with AsyncHttpClient() as client:
            # --- Concurrent Data Fetching ---
            logger.info("Fetching all data sources concurrently...")
            benchmark_symbols = settings.digest.benchmarks or ["SPY", "QQQ"]
            quote_tasks = [global_quote_async(client, symbol) for symbol in benchmark_symbols]
            tasks = [
                latest_vix_close(client),
                upcoming_cpi_releases(client),
                latest_arxiv_qfin_async(client),
                search_papers_async(client, "quantitative finance"),
                *quote_tasks,
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # --- Process Fetcher Results ---
            vix_res, cpi_res, arxiv_res, s2_res, *quote_results = results

            vix = unwrap_result(vix_res, VixClose, lambda: VixClose(date=today, close=0.0), "VIX")
            cpi = unwrap_result(cpi_res, list, list, "CPI Schedule")
            arxiv = unwrap_result(arxiv_res, list, list, "arXiv")
            s2 = unwrap_result(s2_res, list, list, "Semantic Scholar")

            quotes: list[PriceSnapshot] = []
            for symbol, result in zip(benchmark_symbols, quote_results):
                quote = unwrap_result(
                    result,
                    PriceSnapshot,
                    lambda: None,
                    "Quote",
                    context=symbol,
                )
                if quote:
                    quotes.append(quote)

            # --- Sequential Analysis (Placeholder) ---
            # analysis_results = await asyncio.gather(...)
            # ...

            # --- Composition & Sending ---
            logger.info("Composing and sending the digest...")

            digest_data = DigestContext(
                date=today,
                quotes=quotes,
                vix=vix,
                cpi=cpi,
                arxiv=arxiv,
                s2=s2,
                # Add other data fields here as they are implemented
            )

            if not quotes:
                logger.warning("Equity quotes were unavailable; digest will show placeholders.")
            if not cpi:
                logger.warning("CPI schedule data missing; digest will note the absence.")

            # Pass the single context object to the render function
            md = render_digest(context=digest_data)
            html_body = _markdown_to_html(md)
            print(md)

            with open("digest.md", "w", encoding="utf-8") as f:
                f.write(md)
            logger.info("Digest saved to digest.md")

            # --- Send Digest ---
            if settings.dry_run:
                logger.info("Dry-run mode enabled. Markdown content follows:\n%s", md)
                logger.info("Rendered HTML preview:\n%s", html_body)
                return

            if settings.DIGEST_TO:
                send_email(
                    to=settings.DIGEST_TO,
                    subject=f"Daily Quant Digest - {today}",
                    html_or_md=html_body,
                )
                logger.info(f"Digest successfully sent to {settings.DIGEST_TO}")

    except Exception as e:
        logger.error(f"An unexpected error occurred during digest generation: {e}", exc_info=True)
    finally:
        logger.info("Digest generation process finished.")


if __name__ == "__main__":
    from assistant.utils.logging import setup_logger

    setup_logger()

    asyncio.run(main())
