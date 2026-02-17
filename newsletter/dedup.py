"""Deduplication utilities for newsletter content."""

from difflib import SequenceMatcher
from .history import was_published


def similarity(a, b):
    """Return 0-1 similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def deduplicate_news(items, threshold=0.65):
    """Remove near-duplicate news items based on title similarity.

    Uses O(n^2) comparison which is fine for <50 items.
    Keeps the first occurrence (earlier = higher priority feed).
    """
    unique = []
    for item in items:
        is_dup = False
        for existing in unique:
            if similarity(item['title'], existing['title']) > threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(item)
    return unique


def filter_previously_published(items, history):
    """Remove items that were published in previous newsletter editions."""
    return [item for item in items if not was_published(item['title'], history)]
