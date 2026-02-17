"""RSS feed fetching with retry logic and relevance filtering."""

import re
import html
import time
import datetime
import feedparser

from . import config
from .dedup import deduplicate_news, filter_previously_published
from .history import was_published


def _log(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {timestamp} - {message}")


def fetch_feed_with_retry(url, max_retries=None, delay=None):
    """Fetch an RSS feed with exponential backoff retry."""
    if max_retries is None:
        max_retries = config.MAX_RETRIES
    if delay is None:
        delay = config.RETRY_DELAY_SECONDS

    for attempt in range(max_retries):
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                return feed
            # Empty feed — might be temporary, retry
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))
                continue
        except Exception as e:
            _log(f"Feed fetch attempt {attempt + 1}/{max_retries} failed for {url}: {e}", "WARNING")
            if attempt < max_retries - 1:
                time.sleep(delay * (attempt + 1))

    return None


def is_ai_relevant(title, summary=""):
    """Check if an article is genuinely about AI, not a false positive."""
    text = (title + " " + summary).lower()

    for term in config.AI_TERMS:
        if term in text:
            # Guard against false positives for the short term "ai"
            if term == 'ai' or term == 'claude':
                if re.search(r'\b' + re.escape(term) + r'\b', text):
                    return True
            else:
                return True

    return False


def _clean_summary(raw_summary):
    """Clean an RSS entry summary: strip HTML tags, unescape, trim."""
    if not raw_summary:
        return "No summary available."
    summary = html.unescape(raw_summary)
    summary = re.sub(r'<.*?>', '', summary)
    if len(summary) > 300:
        summary = summary[:297] + "..."
    return summary


def _extract_source(title):
    """Extract source name from title like 'Headline - Source Name'."""
    if ' - ' in title:
        parts = title.split(' - ')
        if len(parts) > 1:
            return ' - '.join(parts[:-1]), parts[-1]
    return title, "AI News"


def fetch_ai_news(history):
    """Fetch AI news from Google News RSS feeds with dedup and history filtering."""
    _log("Fetching AI news")
    news_items = []

    for feed_url in config.NEWS_FEEDS:
        feed = fetch_feed_with_retry(feed_url)
        if not feed:
            _log(f"Failed to fetch feed: {feed_url}", "WARNING")
            continue

        for entry in feed.entries[:5]:
            raw_title = html.unescape(entry.title) if hasattr(entry, 'title') else "Untitled"
            raw_summary = entry.summary if hasattr(entry, 'summary') else ""

            if not is_ai_relevant(raw_title, raw_summary):
                continue

            title, source = _extract_source(raw_title)
            summary = _clean_summary(raw_summary)

            news_items.append({
                'title': title,
                'link': entry.link if hasattr(entry, 'link') else "#",
                'published': entry.published if hasattr(entry, 'published') else datetime.datetime.now().isoformat(),
                'summary': summary,
                'source': source,
            })

    # Deduplicate within this run
    news_items = deduplicate_news(news_items)

    # Filter out previously published stories
    news_items = filter_previously_published(news_items, history)

    # Sort by publication date, newest first
    news_items.sort(key=lambda x: x['published'], reverse=True)

    _log(f"Collected {len(news_items)} unique news items")
    return news_items
