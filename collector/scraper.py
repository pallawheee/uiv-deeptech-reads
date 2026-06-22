import trafilatura
import requests
from typing import Optional

HEADERS = {"User-Agent": "UIV-DeepReads/1.0 (research aggregator)"}
TIMEOUT = 15
MIN_BODY_LENGTH = 200


def scrape_article(url: str) -> Optional[dict]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        body = trafilatura.extract(
            resp.text,
            include_comments=False,
            include_tables=False,
        )
        if not body or len(body) < MIN_BODY_LENGTH:
            return None
        words = body.split()
        return {"body": body, "word_count": len(words)}
    except Exception:
        return None
