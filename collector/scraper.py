import trafilatura
import requests
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from typing import Optional

HEADERS = {"User-Agent": "UIV-DeepReads/1.0 (research aggregator)"}
TIMEOUT = 15
MIN_BODY_LENGTH = 200

_SKIP_PATH_SEGMENTS = {"tag", "category", "author", "page", "feed", "rss", "tags"}


class _LinkExtractor(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self._base = base_url
        self._domain = urlparse(base_url).netloc
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag != "a":
            return
        href = dict(attrs).get("href", "")
        if not href:
            return
        abs_url = urljoin(self._base, href).split("?")[0].split("#")[0]
        parsed = urlparse(abs_url)
        if parsed.netloc != self._domain:
            return
        segments = [s for s in parsed.path.strip("/").split("/") if s]
        if not segments:
            return
        if any(s in _SKIP_PATH_SEGMENTS for s in segments):
            return
        self.links.append(abs_url)


def scrape_index_links(listing_url: str, max_links: int = 15) -> list[str]:
    """Fetch a blog listing page and return unique article URLs on the same domain."""
    try:
        resp = requests.get(listing_url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        extractor = _LinkExtractor(listing_url)
        extractor.feed(resp.text)
        seen: set[str] = set()
        links: list[str] = []
        for link in extractor.links:
            if link not in seen and link != listing_url:
                seen.add(link)
                links.append(link)
        return links[:max_links]
    except Exception:
        return []


def scrape_article(url: str) -> Optional[dict]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        result = trafilatura.bare_extraction(
            resp.text,
            include_comments=False,
            include_tables=False,
            url=url,
        )
        if not result:
            return None
        body = getattr(result, "text", None) or (result.get("text") if isinstance(result, dict) else None)
        if not body or len(body) < MIN_BODY_LENGTH:
            return None
        words = body.split()
        title = getattr(result, "title", None) or (result.get("title") if isinstance(result, dict) else None)
        date = getattr(result, "date", None) or (result.get("date") if isinstance(result, dict) else None)
        return {"body": body, "word_count": len(words), "title": title or "", "date": date or ""}
    except Exception:
        return None
