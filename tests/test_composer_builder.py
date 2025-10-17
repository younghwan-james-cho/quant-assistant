from assistant.composer.builder import render_digest
from assistant.utils.dto import (
    CpiRelease,
    DigestContext,
    PaperItem,
    PriceSnapshot,
    VixClose,
)


def test_render_digest_basic() -> None:
    ctx = DigestContext(
        date="2025-10-16",
        quotes=[PriceSnapshot(symbol="SPY", price=500.0, as_of="2025-10-15")],
        vix=VixClose(date="2025-10-15", close=15.0),
        cpi=[CpiRelease(date="Nov 13, 2025", time_et="08:30", url=None)],
        arxiv=[PaperItem(title="Test", authors=["A"], year=2025, url="http://x")],
        s2=[PaperItem(title="Meta", authors=["B"], year=2024, url="http://y")],
    )

    md = render_digest(context=ctx)

    assert "Daily Quant Digest" in md
    assert "- SPY: $500.00 (as of 2025-10-15)" in md
    assert "## Volatility Watch" in md
    assert "## Economic Calendar" in md
    assert "## Research Highlights" in md


def test_render_digest_empty_papers_and_no_quotes() -> None:
    """Render digest with empty data and expect graceful placeholder messages."""

    ctx = DigestContext(
        date="2025-10-16",
        quotes=[],
        vix=VixClose(date="2025-10-15", close=0.0),
        cpi=[],
        arxiv=[],
        s2=[],
    )

    md = render_digest(context=ctx)

    assert "_No market quotes available for today._" in md
    assert "_No upcoming CPI releases reported._" in md
    assert "_No new papers found today._" in md
