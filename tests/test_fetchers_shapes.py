# tests/test_fetchers_shapes.py
import importlib

def test_dto_shapes_importable():
    dto = importlib.import_module("assistant.utils.dto")
    assert hasattr(dto, "PriceSnapshot")
    assert hasattr(dto, "VixClose")
    assert hasattr(dto, "CpiRelease")
    assert hasattr(dto, "PaperItem")

def test_http_client_defaults():
    http = importlib.import_module("assistant.utils.http")
    assert http.DEFAULT_TIMEOUT[0] > 0 and http.DEFAULT_TIMEOUT[1] > 0
    assert http.DEFAULT_MAX_RETRIES >= 1
    assert isinstance(http.DEFAULT_UA, str)

def test_arxiv_builds_items_without_network(monkeypatch):
    # Avoid live calls: monkeypatch feedparser.parse to return a fake feed
    import assistant.fetchers.arxiv_papers as ap

    class FakeFeed:
        entries = [{"title": "Test Paper", "link": "http://example.com",
                    "authors": [{"name": "Alice"}, {"name": "Bob"}],
                    "published_parsed": type("t", (), {"tm_year": 2025})()}]

    monkeypatch.setattr(ap, "feedparser", type("FP", (), {"parse": lambda *_: FakeFeed()}))
    items = ap.latest_arxiv_qfin(limit=1)
    assert len(items) == 1
    assert items[0].title == "Test Paper"
    assert items[0].authors == ["Alice", "Bob"]
    assert items[0].year == 2025

def test_semantic_scholar_builds_items_without_network(monkeypatch):
    import assistant.fetchers.semanticscholar as ss

    class FakeResponse:
        def json(self):
            return {"data": [{"title": "Meta", "url": "http://s2", "authors": [{"name": "C"}], "year": 2022}]}

    class FakeClient:
        def get(self, *_args, **_kwargs):
            return FakeResponse()

    monkeypatch.setattr(ss, "HttpClient", lambda: FakeClient())
    items = ss.search_papers("q-fin", limit=1)
    assert len(items) == 1
    assert items[0].title == "Meta"
    assert items[0].authors == ["C"]
    assert items[0].year == 2022

def test_alphavantage_requires_key(monkeypatch):
    import assistant.fetchers.alphavantage as av
    monkeypatch.delenv("ALPHAVANTAGE_KEY", raising=False)
    try:
        av.global_quote("SPY")
    except RuntimeError as e:
        assert "missing ALPHAVANTAGE_KEY" in str(e)
    else:
        assert False, "expected RuntimeError when key missing"