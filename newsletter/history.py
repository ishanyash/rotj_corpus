"""Content history tracking to avoid repeating content across newsletter editions."""

import json
import hashlib
import datetime
import os

HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'content_history.json')
HISTORY_MAX_DAYS = 90


def _title_hash(title):
    """Create a normalized hash of a title for comparison."""
    normalized = title.lower().strip()
    return hashlib.md5(normalized.encode()).hexdigest()


def load_history():
    """Load content history from JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return {"published_titles": {}, "last_updated": None}
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"published_titles": {}, "last_updated": None}


def save_history(history):
    """Save content history, pruning entries older than HISTORY_MAX_DAYS."""
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=HISTORY_MAX_DAYS)).isoformat()

    # Prune old entries
    history["published_titles"] = {
        k: v for k, v in history.get("published_titles", {}).items()
        if v.get("date", "") >= cutoff
    }
    history["last_updated"] = datetime.datetime.now().isoformat()

    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def was_published(title, history):
    """Check if a title was already published."""
    h = _title_hash(title)
    return h in history.get("published_titles", {})


def record_published(title, history, category="news"):
    """Record a title as published."""
    h = _title_hash(title)
    history.setdefault("published_titles", {})[h] = {
        "title": title,
        "category": category,
        "date": datetime.datetime.now().isoformat(),
    }
