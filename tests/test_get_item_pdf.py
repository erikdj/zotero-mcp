import base64
import json
import os

from zotero_mcp import server


class DummyContext:
    def info(self, *_a, **_k): return None
    def error(self, *_a, **_k): return None
    def warn(self, *_a, **_k): return None


class FakeZotero:
    def __init__(self, item, children):
        self._item = item
        self._children = children

    def add_parameters(self, **_kw):
        pass

    def item(self, key):
        return self._item

    def children(self, key):
        return self._children

    def dump(self, key, filename=None, path=None):
        # Write fake PDF bytes
        filepath = os.path.join(path, filename)
        with open(filepath, "wb") as f:
            f.write(b"%PDF-1.4 fake pdf content for testing")


def _make_fake_zotero():
    item = {
        "key": "ITEM001",
        "data": {
            "itemType": "journalArticle",
            "key": "ITEM001",
            "title": "Test Paper",
        },
    }
    children = [
        {
            "key": "ATT001",
            "data": {
                "itemType": "attachment",
                "key": "ATT001",
                "title": "Test PDF",
                "filename": "test.pdf",
                "contentType": "application/pdf",
                "md5": "abc123",
            },
        }
    ]
    return FakeZotero(item, children)


def test_get_item_pdf_base64(monkeypatch):
    monkeypatch.setattr(server, "get_zotero_client", _make_fake_zotero)
    result = server.get_item_pdf(item_key="ITEM001", output_mode="base64", ctx=DummyContext())
    data = json.loads(result)
    assert data["filename"] == "test.pdf"
    assert data["content_type"] == "application/pdf"
    assert data["size_bytes"] > 0
    # Verify base64 decodes correctly
    decoded = base64.b64decode(data["data"])
    assert decoded.startswith(b"%PDF")


def test_get_item_pdf_path(monkeypatch):
    monkeypatch.setattr(server, "get_zotero_client", _make_fake_zotero)
    result = server.get_item_pdf(item_key="ITEM001", output_mode="path", ctx=DummyContext())
    data = json.loads(result)
    assert data["filename"] == "test.pdf"
    assert data["content_type"] == "application/pdf"
    assert os.path.exists(data["path"])
    # Clean up
    os.unlink(data["path"])
    os.rmdir(os.path.dirname(data["path"]))


def test_get_item_pdf_no_attachment(monkeypatch):
    item = {"key": "ITEM002", "data": {"itemType": "journalArticle", "key": "ITEM002", "title": "No PDF"}}
    fake = FakeZotero(item, [])  # no children
    monkeypatch.setattr(server, "get_zotero_client", lambda: fake)
    result = server.get_item_pdf(item_key="ITEM002", output_mode="base64", ctx=DummyContext())
    assert "No attachment" in result or "not a PDF" in result.lower() or "no" in result.lower()
