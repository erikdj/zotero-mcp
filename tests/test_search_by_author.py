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


def test_search_by_author_ranks_results(monkeypatch):
    items = [
        {"key": "A", "data": {"itemType": "journalArticle", "title": "Paper One", "date": "2024",
                               "creators": [{"firstName": "Alice", "lastName": "Zhang", "creatorType": "author"}], "tags": []}},
        {"key": "B", "data": {"itemType": "journalArticle", "title": "Paper Two", "date": "2024",
                               "creators": [{"firstName": "Jane", "lastName": "Smith", "creatorType": "author"}], "tags": []}},
        {"key": "C", "data": {"itemType": "journalArticle", "title": "Paper Three", "date": "2024",
                               "creators": [{"firstName": "Bob", "lastName": "Smith", "creatorType": "author"}], "tags": []}},
    ]
    monkeypatch.setattr(server, "get_zotero_client", lambda: FakeZotero(items))

    result = server.search_by_author(query="Jane Smith", limit=10, ctx=DummyContext())
    assert "Relevance:" in result
    # Jane Smith exact match should rank highest
    lines = result.split("\n")
    heading_lines = [l for l in lines if l.startswith("## ")]
    assert "Paper Two" in heading_lines[0]


def test_search_by_author_no_results(monkeypatch):
    monkeypatch.setattr(server, "get_zotero_client", lambda: FakeZotero([]))
    result = server.search_by_author(query="Unknown", limit=10, ctx=DummyContext())
    assert "No items found" in result
