import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "collector"))

import scraper


def test_scrape_returns_body_and_word_count():
    fake_html = "<html><body><article>" + ("word " * 300) + "</article></body></html>"
    mock_resp = MagicMock()
    mock_resp.text = fake_html
    mock_resp.raise_for_status = MagicMock()

    with patch("scraper.requests.get", return_value=mock_resp), \
         patch("scraper.trafilatura.extract", return_value="word " * 300):
        result = scraper.scrape_article("https://example.com/article")

    assert result is not None
    assert "body" in result
    assert "word_count" in result
    assert result["word_count"] == 300


def test_scrape_returns_none_when_body_too_short():
    mock_resp = MagicMock()
    mock_resp.text = "<html><body>Short</body></html>"
    mock_resp.raise_for_status = MagicMock()

    with patch("scraper.requests.get", return_value=mock_resp), \
         patch("scraper.trafilatura.extract", return_value="too short"):
        result = scraper.scrape_article("https://example.com/short")

    assert result is None


def test_scrape_returns_none_when_trafilatura_returns_none():
    mock_resp = MagicMock()
    mock_resp.text = "<html></html>"
    mock_resp.raise_for_status = MagicMock()

    with patch("scraper.requests.get", return_value=mock_resp), \
         patch("scraper.trafilatura.extract", return_value=None):
        result = scraper.scrape_article("https://example.com/empty")

    assert result is None


def test_scrape_returns_none_on_request_exception():
    with patch("scraper.requests.get", side_effect=Exception("connection refused")):
        result = scraper.scrape_article("https://unreachable.example.com")

    assert result is None


def test_scrape_returns_none_on_http_error():
    mock_resp = MagicMock()
    mock_resp.raise_for_status.side_effect = Exception("404 Not Found")

    with patch("scraper.requests.get", return_value=mock_resp):
        result = scraper.scrape_article("https://example.com/gone")

    assert result is None
