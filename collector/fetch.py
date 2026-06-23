import sys
import time
import yaml
import feedparser
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from store import (
    load_articles, save_articles, article_id,
    is_duplicate, append_article, log_error,
)
from scraper import scrape_article, scrape_index_links
from enricher import enrich_article

SOURCES_FILE = Path(__file__).parent / "sources.yaml"
MAX_ARTICLE_AGE_DAYS = 30
RATE_LIMIT_SLEEP = 0.5


def load_sources() -> list:
    with open(SOURCES_FILE) as f:
        return [s for s in yaml.safe_load(f)["sources"] if not s.get("disabled")]


def parse_published_at(entry) -> str:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
        except Exception:
            pass
    return datetime.now(timezone.utc).isoformat()


def is_too_old(published_at: str) -> bool:
    try:
        dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt) > timedelta(days=MAX_ARTICLE_AGE_DAYS)
    except Exception:
        return False


def _process_candidate(url: str, title: str, published_at: str, source: dict, data: dict) -> bool:
    if is_duplicate(url, data):
        print(f"  skip (duplicate): {title[:50]}")
        return False

    scraped = scrape_article(url)
    if not scraped:
        print(f"  skip (scrape failed): {title[:50]}")
        log_error({"url": url, "source": source["name"], "reason": "scrape_failed"})
        return False

    resolved_title = title or scraped.get("title") or url.split("/")[-1].replace("-", " ").title()
    resolved_date = published_at or scraped.get("date") or datetime.now(timezone.utc).isoformat()

    try:
        enrichment = enrich_article(resolved_title, scraped["body"], scraped["word_count"])
    except Exception as e:
        print(f"  skip (enrich failed): {resolved_title[:50]} — {e}")
        log_error({"url": url, "source": source["name"], "reason": f"enrich_failed: {e}"})
        return False

    if not enrichment["sectors"]:
        print(f"  skip (no deeptech sector): {resolved_title[:50]}")
        return False

    article = {
        "id": article_id(url),
        "title": resolved_title,
        "url": url,
        "source_name": source["name"],
        "source_type": source["type"],
        "published_at": resolved_date,
        "sectors": enrichment["sectors"],
        "excerpt": enrichment["excerpt"],
        "signal": enrichment["signal"],
        "estimated_read_minutes": enrichment["estimated_read_minutes"],
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
    append_article(article, data)
    print(f"  + {resolved_title[:60]}")
    return True


def _fetch_rss(source: dict, data: dict) -> int:
    added = 0
    try:
        feed = feedparser.parse(source["url"])
    except Exception as e:
        log_error({"source": source["name"], "reason": f"rss_parse_failed: {e}"})
        return 0

    for entry in feed.entries[:10]:
        url = entry.get("link", "").strip()
        title = entry.get("title", "").strip()
        if not url or not title:
            continue
        published_at = parse_published_at(entry)
        if is_too_old(published_at):
            print(f"  skip (too old): {title[:50]}")
            continue
        if _process_candidate(url, title, published_at, source, data):
            added += 1
            time.sleep(RATE_LIMIT_SLEEP)
    return added


def _fetch_scrape_index(source: dict, data: dict) -> int:
    added = 0
    links = scrape_index_links(source["url"])
    if not links:
        log_error({"source": source["name"], "reason": "scrape_index_returned_no_links"})
        return 0

    for url in links:
        if _process_candidate(url, "", "", source, data):
            added += 1
            time.sleep(RATE_LIMIT_SLEEP)
    return added


def fetch_all() -> int:
    sources = load_sources()
    data = load_articles()
    added = 0

    for source in sources:
        print(f"\n[{source['name']}] Checking {source['url']}")

        if source.get("feed_type") == "scrape_index":
            added += _fetch_scrape_index(source, data)
        else:
            added += _fetch_rss(source, data)

    save_articles(data)
    print(f"\nDone — {added} new articles added")
    return added


if __name__ == "__main__":
    fetch_all()
