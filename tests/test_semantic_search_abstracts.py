import sys
import pytest

if sys.version_info >= (3, 14):
    pytest.skip("chromadb incompatible with Python 3.14+", allow_module_level=True)

from zotero_mcp import server


class DummyContext:
    def info(self, *_a, **_k): return None
    def error(self, *_a, **_k): return None
    def warn(self, *_a, **_k): return None


class FakeSemanticSearch:
    def search_abstracts(self, query, limit=10, filters=None):
        return {
            "query": query,
            "limit": limit,
            "filters": filters,
            "results": [
                {
                    "item_key": "KEY001",
                    "similarity_score": 0.95,
                    "matched_text": "abstract about neural networks",
                    "metadata": {},
                    "zotero_item": {
                        "data": {
                            "title": "Neural Network Survey",
                            "itemType": "journalArticle",
                            "creators": [{"firstName": "Test", "lastName": "Author", "creatorType": "author"}],
                            "date": "2024",
                            "abstractNote": "A survey of neural network methods.",
                            "tags": [{"tag": "AI"}],
                        }
                    },
                }
            ],
            "total_found": 1,
        }


def test_semantic_search_abstracts_formats_output(monkeypatch):
    # The function does `from zotero_mcp.semantic_search import create_semantic_search`
    # inside its body, so we patch it at the source module
    import zotero_mcp.semantic_search as ss_mod
    monkeypatch.setattr(ss_mod, "create_semantic_search", lambda *a, **kw: FakeSemanticSearch())

    result = server.semantic_search_abstracts(
        query="neural networks", limit=10, ctx=DummyContext()
    )
    assert "Neural Network Survey" in result
    assert "Similarity Score:" in result
    assert "0.950" in result


def test_semantic_search_abstracts_empty_query(monkeypatch):
    result = server.semantic_search_abstracts(query="  ", limit=10, ctx=DummyContext())
    assert "Error" in result
