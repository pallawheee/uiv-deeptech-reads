import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "collector"))

import enricher

BODY_SHORT = "First sentence is the lede hook. " * 2 + (
    "Second sentence has the real argument about semiconductor supply chains. "
    "Third sentence explains why fabs matter for national security. "
    "Fourth sentence describes investment implications for India. "
) * 5


def test_enrich_returns_all_required_fields():
    result = enricher.enrich_article("Test Title", BODY_SHORT, 200)
    assert "excerpt" in result
    assert "signal" in result
    assert "sectors" in result
    assert "estimated_read_minutes" in result


def test_enrich_signal_is_empty_string():
    result = enricher.enrich_article("Any title", BODY_SHORT, 100)
    assert result["signal"] == ""


def test_enrich_excerpt_skips_first_sentence():
    body = (
        "This is the lede hook sentence that should be skipped entirely. "
        "This is the second sentence with real substance about quantum computing. "
        "This is the third sentence about chip design challenges. "
        "This is the fourth sentence about investment thesis. "
        "This is the fifth sentence about market dynamics. "
    )
    result = enricher.enrich_article("Title", body, 50)
    assert "lede hook" not in result["excerpt"]
    assert "second sentence" in result["excerpt"]


def test_enrich_read_time_rounds_up():
    result = enricher.enrich_article("Title", BODY_SHORT, 201)
    assert result["estimated_read_minutes"] == 2


def test_enrich_read_time_minimum_one_minute():
    result = enricher.enrich_article("Title", BODY_SHORT, 10)
    assert result["estimated_read_minutes"] == 1


def test_sector_classification_detects_semiconductors():
    body = "The CHIPS Act has accelerated semiconductor fab investment globally. TSMC is building new foundries."
    result = enricher.enrich_article("Chip Fabs", body, 20)
    assert "Semiconductors" in result["sectors"]


def test_sector_classification_detects_multiple_sectors():
    body = (
        "Drone delivery is reshaping robotics logistics. "
        "Meanwhile quantum computing breakthroughs are enabling new cryptography. "
        "UAV regulations are changing fast."
    )
    result = enricher.enrich_article("Tech Overview", body, 30)
    assert "Robotics" in result["sectors"]
    assert "Quantum Computing" in result["sectors"]


def test_sector_classification_returns_empty_for_unrelated_content():
    body = "The weather today is sunny with light winds across the coastal regions."
    result = enricher.enrich_article("Weather", body, 15)
    assert result["sectors"] == []


def test_enrich_excerpt_fallback_when_body_too_short():
    short_body = "Only one sentence here."
    result = enricher.enrich_article("Title", short_body, 5)
    assert len(result["excerpt"]) > 0
