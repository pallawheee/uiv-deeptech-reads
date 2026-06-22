import json
import sys
import tempfile
from pathlib import Path
import pytest

# Add collector/ to path so we can import store
sys.path.insert(0, str(Path(__file__).parent.parent / "collector"))

import store


@pytest.fixture(autouse=True)
def patch_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "ARTICLES_FILE", tmp_path / "articles.json")
    monkeypatch.setattr(store, "FETCH_LOG_FILE", tmp_path / "fetch_log.json")


def test_load_articles_returns_empty_when_file_missing():
    data = store.load_articles()
    assert data == {"last_updated": None, "articles": []}


def test_save_and_load_roundtrip():
    data = {"last_updated": None, "articles": [{"id": "abc", "title": "Test"}]}
    store.save_articles(data)
    loaded = store.load_articles()
    assert loaded["articles"][0]["title"] == "Test"
    assert loaded["last_updated"] is not None


def test_article_id_is_deterministic():
    id1 = store.article_id("https://example.com/article")
    id2 = store.article_id("https://example.com/article")
    assert id1 == id2
    assert len(id1) == 16


def test_article_id_differs_for_different_urls():
    assert store.article_id("https://a.com") != store.article_id("https://b.com")


def test_is_duplicate_detects_existing_url():
    url = "https://example.com/test"
    data = {"articles": [{"id": store.article_id(url)}]}
    assert store.is_duplicate(url, data) is True


def test_is_duplicate_returns_false_for_new_url():
    data = {"articles": [{"id": store.article_id("https://other.com")}]}
    assert store.is_duplicate("https://new.com", data) is False


def test_append_article_inserts_at_front():
    data = {"articles": [{"id": "old"}]}
    store.append_article({"id": "new"}, data)
    assert data["articles"][0]["id"] == "new"


def test_append_article_trims_to_max():
    data = {"articles": [{"id": str(i)} for i in range(store.MAX_ARTICLES)]}
    store.append_article({"id": "newest"}, data)
    assert len(data["articles"]) == store.MAX_ARTICLES
    assert data["articles"][0]["id"] == "newest"


def test_log_error_creates_file_and_appends():
    store.log_error({"url": "https://fail.com", "reason": "timeout"})
    store.log_error({"url": "https://fail2.com", "reason": "parse_error"})
    log = json.loads(store.FETCH_LOG_FILE.read_text())
    assert len(log) == 2
    assert log[0]["url"] == "https://fail.com"
    assert "timestamp" in log[0]


def test_log_error_caps_at_100_entries():
    for i in range(105):
        store.log_error({"url": f"https://fail{i}.com", "reason": "test"})
    log = json.loads(store.FETCH_LOG_FILE.read_text())
    assert len(log) == 100
