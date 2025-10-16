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
