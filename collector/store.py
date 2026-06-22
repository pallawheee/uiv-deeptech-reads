import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path(__file__).parent.parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"
FETCH_LOG_FILE = DATA_DIR / "fetch_log.json"
MAX_ARTICLES = 500


def load_articles() -> dict:
    if not ARTICLES_FILE.exists():
        return {"last_updated": None, "articles": []}
    with open(ARTICLES_FILE) as f:
        return json.load(f)


def save_articles(data: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(ARTICLES_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def is_duplicate(url: str, data: dict) -> bool:
    aid = article_id(url)
    return any(a["id"] == aid for a in data["articles"])


def append_article(article: dict, data: dict) -> None:
    data["articles"].insert(0, article)
    if len(data["articles"]) > MAX_ARTICLES:
        data["articles"] = data["articles"][:MAX_ARTICLES]


def log_error(entry: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    log = []
    if FETCH_LOG_FILE.exists():
        with open(FETCH_LOG_FILE) as f:
            log = json.load(f)
    log.append({**entry, "timestamp": datetime.now(timezone.utc).isoformat()})
    log = log[-100:]
    with open(FETCH_LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)
