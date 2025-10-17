from assistant.composer.builder import render_digest
from assistant.utils.dto import PriceSnapshot, VixClose, CpiRelease, PaperItem


def test_render_digest_basic():
    md = render_digest(
        date="2025-10-16",
        quotes=[PriceSnapshot(symbol="SPY", price=500.0, as_of="2025-10-15")],
        vix=VixClose(date="2025-10-15", close=15.0),
        cpi=[CpiRelease(date="Nov 13, 2025", time_et="08:30", url=None)],
        arxiv=[PaperItem(title="Test", authors=["A"], year=2025, url="http://x")],
        s2=[PaperItem(title="Meta", authors=["B"], year=2024, url="http://y")],
    )
    assert "Daily Quant Digest" in md and "SPY" in md and "VIX" in md


def test_render_digest_empty_papers_and_no_quotes():
    """Render digest with no market quotes and empty paper lists.

    Expect a user-friendly message for no papers and no market quote entries.
    """
    md = render_digest(
        date="2025-10-16",
        quotes=[],  # no market quotes
        vix=VixClose(date="2025-10-15", close=0.0),
        cpi=[],
        arxiv=[],  # empty arXiv list
        s2=[],  # empty Semantic Scholar list
    )

    # Simulate HTML rendering used by the runner (simple newline -> <br/>)
    html = md.replace("\n", "<br/>")

    # Expect a "no papers" message to be present in the final output.
    assert "No new papers found today" in md or "No new papers found today" in html

    # Ensure no market quote list items are present in the Market Summary section.
    start = md.find("## Market Summary")
    assert start != -1, "Market Summary header should be present"
    next_sec = md.find("##", start + 1)
    market_section = md[start:next_sec] if next_sec != -1 else md[start:]
    # When quotes list is empty, there should be the "No market quotes" message and no "- " items.
    assert (
        "No market quotes available" in market_section
        or "No market quotes available" in market_section.lower()
    )
    assert "- " not in market_section.replace("_No market quotes available for today._", "")
