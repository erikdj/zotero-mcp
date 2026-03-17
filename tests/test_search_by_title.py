from zotero_mcp import server


class DummyContext:
    def info(self, *_a, **_k): return None
    def error(self, *_a, **_k): return None
    def warn(self, *_a, **_k): return None


class FakeZotero:
    def __init__(self, items):
        self._items = items

    def add_parameters(self, **_kw):
        pass

    def items(self, **_kw):
        return self._items


def test_search_by_title_ranks_results(monkeypatch):
    items = [
        {"key": "A", "data": {"itemType": "journalArticle", "title": "Biology Today", "date": "2024", "creators": [], "tags": []}},
        {"key": "B", "data": {"itemType": "journalArticle", "title": "Quantum Computing", "date": "2024", "creators": [], "tags": []}},
        {"key": "C", "data": {"itemType": "journalArticle", "title": "Quantum Computing in Practice", "date": "2024", "creators": [], "tags": []}},
    ]
    monkeypatch.setattr(server, "get_zotero_client", lambda: FakeZotero(items))

    result = server.search_by_title(query="Quantum Computing", limit=10, ctx=DummyContext())
    assert "Relevance:" in result
    # Best match should appear first
    lines = result.split("\n")
    first_title_idx = next(i for i, l in enumerate(lines) if "Quantum Computing" in l and "##" in l)
    assert "Quantum Computing" in lines[first_title_idx]


def test_search_by_title_empty_query(monkeypatch):
    monkeypatch.setattr(server, "get_zotero_client", lambda: FakeZotero([]))
    result = server.search_by_title(query="", limit=10, ctx=DummyContext())
    assert "Error" in result


def test_search_by_title_no_results(monkeypatch):
    monkeypatch.setattr(server, "get_zotero_client", lambda: FakeZotero([]))
    result = server.search_by_title(query="nonexistent", limit=10, ctx=DummyContext())
    assert "No items found" in result
