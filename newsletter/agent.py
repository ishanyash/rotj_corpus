"""Newsletter agent orchestrator — fetches content, formats, and publishes to Google Doc."""

import os
import json
import datetime
import random

from google.oauth2 import service_account
from googleapiclient.discovery import build

from . import config
from .history import load_history, save_history, record_published
from .fetchers import fetch_ai_news
from .content_pools import (
    fetch_ai_tools,
    fetch_youtube_video,
    fetch_insights,
    get_prompt_tip,
    generate_why_it_matters,
    FALLBACK_TOOLS,
)
from .formatter import DocFormatter
from .gdoc import clear_document, write_to_doc


def _log(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {timestamp} - {message}")


class NewsletterAgent:
    def __init__(self):
        _log("Initializing Newsletter Agent")
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        self.doc_id = os.environ.get('DOCUMENT_ID')

        if not creds_json or not self.doc_id:
            _log("Missing environment variables. Set GOOGLE_CREDENTIALS and DOCUMENT_ID.", "ERROR")
            raise ValueError("Missing required environment variables")

        try:
            creds_dict = json.loads(creds_json)
            creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/documents'],
            )
            self.docs_service = build('docs', 'v1', credentials=creds)
            _log("Google Docs API client initialized")
        except Exception as e:
            _log(f"Failed to initialize Google Docs API client: {e}", "ERROR")
            raise

        self.today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        self.history = load_history()

    def _fetch_all_content(self):
        """Fetch all content sections."""
        self.news_items = fetch_ai_news(self.history)
        self.ai_tools = fetch_ai_tools(self.history)
        self.youtube_video = fetch_youtube_video(self.history)
        self.insights = fetch_insights(self.history)
        self.prompt_tip = get_prompt_tip(self.history)

    def _validate_content(self):
        """Ensure minimum viable content before publishing."""
        issues = []
        if len(self.news_items) < config.MIN_NEWS_ITEMS:
            issues.append(f"Only {len(self.news_items)} news items (need {config.MIN_NEWS_ITEMS})")
        if len(self.ai_tools) < config.MIN_TOOLS:
            issues.append(f"Only {len(self.ai_tools)} tools (need {config.MIN_TOOLS})")
        if not self.youtube_video:
            issues.append("No YouTube video selected")
        if len(self.insights) < config.MIN_INSIGHTS:
            issues.append(f"Only {len(self.insights)} insights (need {config.MIN_INSIGHTS})")

        if issues:
            _log(f"Content validation failed: {'; '.join(issues)}", "WARNING")
            return False
        return True

    def _build_formatted_doc(self):
        """Build the newsletter using DocFormatter for rich Google Doc output."""
        _log("Building formatted newsletter")
        fmt = DocFormatter()

        # --- Title ---
        fmt.add_heading(f"Return of the Jed(AI) - {self.today}", level=1)
        fmt.add_newline()

        # --- Headline from top story ---
        headline_emoji = config.random_emoji("headline")
        if self.news_items:
            fmt.add_heading(f"{headline_emoji} {self.news_items[0]['title']}", level=2)
            fmt.add_italic_text("PLUS: The AI tools reshaping how we work & create")
            fmt.add_newline()
        else:
            fmt.add_heading(f"{headline_emoji} AI's Wild Week: Breakthroughs & Innovations", level=2)

        fmt.add_newline()
        fmt.add_horizontal_rule()
        fmt.add_newline()

        # --- Welcome ---
        welcome_emoji = config.random_emoji("welcome")
        fmt.add_heading(f"{welcome_emoji} Welcome, fellow humans!", level=2)
        fmt.add_text("Hope your algorithms are optimized and your neural nets are firing on all nodes today. ")
        fmt.add_text("Let's dive into the latest from the AI universe.")
        fmt.add_newline()
        fmt.add_newline()
        fmt.add_horizontal_rule()
        fmt.add_newline()

        # --- Main Story ---
        if self.news_items:
            main = self.news_items[0]
            fmt.add_heading("Main Story", level=2)
            fmt.add_newline()
            fmt.add_heading(f"{main['title']}", level=3)
            fmt.add_text(main['summary'])
            fmt.add_newline()
            fmt.add_newline()
            why = generate_why_it_matters(main['title'], main['summary'], main['source'])
            fmt.add_bold_text("Why it matters: ")
            fmt.add_text(why)
            fmt.add_newline()
            fmt.add_newline()
            fmt.add_link("Read the full story \u2192", main['link'])
            fmt.add_newline()
            fmt.add_newline()
            fmt.add_horizontal_rule()
            fmt.add_newline()

        # --- Prompt Tip ---
        if self.prompt_tip:
            prompt_emoji = config.random_emoji("prompt")
            fmt.add_heading(f"{prompt_emoji} Prompt Magic of the Day", level=2)
            fmt.add_newline()
            fmt.add_bold_text(self.prompt_tip['intro'])
            fmt.add_newline()
            fmt.add_newline()
            fmt.add_text("Try this prompt:")
            fmt.add_newline()
            fmt.add_newline()
            fmt.add_italic_text(self.prompt_tip['prompt'])
            fmt.add_newline()
            fmt.add_newline()
            fmt.add_text(self.prompt_tip['explanation'])
            fmt.add_newline()
            fmt.add_newline()
            fmt.add_horizontal_rule()
            fmt.add_newline()

        # --- AI Tools ---
        if self.ai_tools:
            tools_emoji = config.random_emoji("tools")
            fmt.add_heading(f"{tools_emoji} AI Toolkit: New & Noteworthy", level=2)
            fmt.add_newline()
            bullet_start = fmt._cursor
            for tool in self.ai_tools:
                fmt.add_bold_text(tool['name'])
                fmt.add_text(f" \u2014 {tool['description']}")
                fmt.add_newline()
            bullet_end = fmt._cursor
            fmt.add_bullets_to_range(bullet_start, bullet_end)
            fmt.add_newline()
            fmt.add_horizontal_rule()
            fmt.add_newline()

        # --- Quick Hits ---
        if len(self.news_items) > 1:
            news_emoji = config.random_emoji("news")
            fmt.add_heading(f"{news_emoji} Around the Horn (Quick Hits)", level=2)
            fmt.add_newline()
            bullet_start = fmt._cursor
            for news in self.news_items[1:5]:
                fmt.add_bold_text(f"{news['source']}: ")
                fmt.add_text(news['title'])
                fmt.add_newline()
            bullet_end = fmt._cursor
            fmt.add_bullets_to_range(bullet_start, bullet_end)
            fmt.add_newline()
            fmt.add_horizontal_rule()
            fmt.add_newline()

        # --- YouTube Video ---
        if self.youtube_video:
            video_emoji = config.random_emoji("video")
            fmt.add_heading(f"{video_emoji} This Week in AI (Video Pick)", level=2)
            fmt.add_newline()
            fmt.add_bold_text(self.youtube_video['title'])
            fmt.add_text(f" from {self.youtube_video['channel']}")
            fmt.add_newline()
            fmt.add_newline()
            fmt.add_link("Watch Now \u2192", self.youtube_video['link'])
            fmt.add_newline()
            fmt.add_newline()
            fmt.add_horizontal_rule()
            fmt.add_newline()

        # --- Insights ---
        if self.insights:
            insights_emoji = config.random_emoji("insights")
            fmt.add_heading(f"{insights_emoji} Intelligent Insights", level=2)
            fmt.add_newline()
            bullet_start = fmt._cursor
            for insight in self.insights:
                if insight.get('source') and insight['source'] != 'AI Research':
                    fmt.add_bold_text(f"{insight['source']}: ")
                fmt.add_text(insight['text'])
                if insight.get('link'):
                    fmt.add_text(" ")
                    fmt.add_link("[source]", insight['link'])
                fmt.add_newline()
            bullet_end = fmt._cursor
            fmt.add_bullets_to_range(bullet_start, bullet_end)
            fmt.add_newline()
            fmt.add_horizontal_rule()
            fmt.add_newline()

        # --- CTA Footer ---
        fmt.add_heading("That's a wrap!", level=2)
        fmt.add_newline()
        fmt.add_text("Thanks for reading! The best way to support us is by sharing this newsletter with a friend.")
        fmt.add_newline()

        return fmt.build_requests()

    def _record_all_published(self):
        """Record all published content in history to avoid future repeats."""
        for item in self.news_items[:5]:
            record_published(item['title'], self.history, category='news')
        for tool in self.ai_tools:
            record_published(tool['name'], self.history, category='tool')
        if self.youtube_video:
            record_published(self.youtube_video['title'], self.history, category='video')
        for insight in self.insights:
            record_published(insight['text'], self.history, category='insight')
        if self.prompt_tip:
            record_published(self.prompt_tip['intro'], self.history, category='prompt_tip')

    def run(self):
        """Run the complete newsletter generation process."""
        _log("Starting Return of the Jed(AI) Newsletter Agent")

        try:
            # 1. Fetch all content
            self._fetch_all_content()

            # 2. Validate minimum content
            if not self._validate_content():
                _log("Insufficient content — skipping publish", "ERROR")
                return {
                    "status": "error",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "message": "Content validation failed — not enough content to publish",
                }

            # 3. Build formatted document requests
            api_requests = self._build_formatted_doc()

            # 4. Clear the doc and write new content
            clear_document(self.docs_service, self.doc_id)
            success = write_to_doc(self.docs_service, self.doc_id, api_requests)

            if success:
                # 5. Record published content and save history
                self._record_all_published()
                save_history(self.history)

                _log("Newsletter generation and update completed successfully!")
                return {
                    "status": "success",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "message": "Newsletter updated successfully",
                    "stats": {
                        "news_items": len(self.news_items),
                        "tools": len(self.ai_tools),
                        "insights": len(self.insights),
                        "has_video": bool(self.youtube_video),
                        "has_prompt_tip": bool(self.prompt_tip),
                    },
                }
            else:
                _log("Failed to update newsletter", "ERROR")
                return {
                    "status": "error",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "message": "Failed to update Google Doc",
                }

        except Exception as e:
            _log(f"Error in newsletter generation: {e}", "ERROR")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.datetime.now().isoformat(),
            }
