import asyncio

import pytest

from assistant.composer.run_digest import main
from assistant.utils.dto import CpiRelease, PaperItem, PriceSnapshot, VixClose


@pytest.mark.filterwarnings("ignore::RuntimeWarning")
def test_main_does_not_raise(monkeypatch, capsys):
    # Provide lightweight stubs so the pipeline does not hit real network services.
    async def fake_vix(_client):
        return VixClose(date="2025-10-15", close=15.0)

    async def fake_cpi(_client):
        return [CpiRelease(date="Nov 13, 2025", time_et="08:30", url="http://cpi")]

    async def fake_arxiv(_client, _limit=None):
        return [PaperItem(title="Test", authors=["A"], year=2025, url="http://x")]

    async def fake_s2(_client, _query, _limit=10, _fields="title,authors,year,url"):
        return [PaperItem(title="Meta", authors=["B"], year=2024, url="http://y")]

    async def fake_quote(_client, symbol):
        return PriceSnapshot(symbol=symbol, price=500.0, as_of="2025-10-15")

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr("assistant.composer.run_digest.latest_vix_close", fake_vix)
    monkeypatch.setattr("assistant.composer.run_digest.upcoming_cpi_releases", fake_cpi)
    monkeypatch.setattr("assistant.composer.run_digest.latest_arxiv_qfin_async", fake_arxiv)
    monkeypatch.setattr("assistant.composer.run_digest.search_papers_async", fake_s2)
    monkeypatch.setattr("assistant.composer.run_digest.global_quote_async", fake_quote)
    monkeypatch.setattr("assistant.composer.run_digest.AsyncHttpClient", DummyClient)

    asyncio.run(main())

    out, err = capsys.readouterr()
    assert "Daily Quant Digest" in out
    assert err == ""
