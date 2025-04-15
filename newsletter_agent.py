import os
import json
import requests
import feedparser
import datetime
from datetime import timedelta
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
import re
import html
from transformers import pipeline

# Configure environment variables (for local testing)
# For GitHub Actions, you'll set these as secrets
# GOOGLE_CREDENTIALS should be the contents of your service account JSON key
# DOCUMENT_ID should be the ID of your Google Doc (from the URL)

# Initialize the summarizer (using a lightweight model for the free tier)
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

class AINewsletterAgent:
    def __init__(self):
        self.doc_id = os.environ.get('DOCUMENT_ID')
        self.setup_google_docs()
        self.news_items = []
        self.ai_tools = []
        self.youtube_video = None
        
    def setup_google_docs(self):
        """Set up Google Docs API client."""
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        creds_dict = json.loads(creds_json)
        
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/documents']
        )
        
        self.docs_service = build('docs', 'v1', credentials=creds)
        
    def fetch_ai_news(self):
        """Fetch AI news from Google News RSS feed."""
        # Define AI and tech related RSS feeds
        feeds = [
            'https://news.google.com/rss/search?q=artificial+intelligence+when:1d&hl=en-US&gl=US&ceid=US:en',
            'https://news.google.com/rss/search?q=machine+learning+when:1d&hl=en-US&gl=US&ceid=US:en',
            'https://news.google.com/rss/search?q=openai+when:1d&hl=en-US&gl=US&ceid=US:en',
            'https://news.google.com/rss/search?q=anthropic+claude+when:1d&hl=en-US&gl=US&ceid=US:en',
            'https://news.google.com/rss/search?q=generative+ai+when:1d&hl=en-US&gl=US&ceid=US:en'
        ]
        
        for feed_url in feeds:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:  # Get the top 5 entries from each feed
                # Basic cleaning
                title = html.unescape(entry.title)
                if 'artificial intelligence' in title.lower() or 'ai' in title.lower() or 'machine learning' in title.lower() or 'openai' in title.lower() or 'anthropic' in title.lower() or 'claude' in title.lower() or 'gpt' in title.lower():
                    # Get the summary and clean it up
                    if hasattr(entry, 'summary'):
                        summary = html.unescape(entry.summary)
                        # Remove HTML tags
                        summary = re.sub(r'<.*?>', '', summary)
                    else:
                        summary = "No summary available."
                    
                    # Use the transformer model to create a better summary if the article has content
                    if len(summary) > 100:
                        try:
                            ai_summary = summarizer(summary, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
                        except Exception as e:
                            print(f"Error summarizing: {e}")
                            ai_summary = summary[:150] + "..."
                    else:
                        ai_summary = summary
                    
                    self.news_items.append({
                        'title': title,
                        'link': entry.link,
                        'published': entry.published,
                        'summary': ai_summary,
                        'source': entry.source.title if hasattr(entry, 'source') and hasattr(entry.source, 'title') else "News Source"
                    })
        
        # Sort by publication date, newest first
        self.news_items.sort(key=lambda x: x['published'], reverse=True)
        
    def fetch_ai_tools(self):
        """Fetch new AI tools from Product Hunt or other sources."""
        # For the free tier, we'll use a simple approach with Product Hunt RSS
        ph_feed_url = 'https://www.producthunt.com/feed?category=artificial-intelligence'
        feed = feedparser.parse(ph_feed_url)
        
        for entry in feed.entries[:5]:
            self.ai_tools.append({
                'name': html.unescape(entry.title),
                'link': entry.link,
                'description': html.unescape(entry.summary)[:150] + "..." if len(entry.summary) > 150 else html.unescape(entry.summary)
            })
    
    def fetch_youtube_video(self):
        """Fetch a trending AI YouTube video."""
        # Since YouTube API requires a key and has quotas, for the free tier, we'll use a fallback approach
        # This is a simplified version - in production, you might want to use the YouTube API
        
        # Predefined list of popular AI channels
        ai_channels = [
            "https://www.youtube.com/@TwoMinutePapers/videos",
            "https://www.youtube.com/@lexfridman/videos",
            "https://www.youtube.com/@YannicKilcher/videos"
        ]
        
        try:
            # For demo purposes, just getting the first channel's latest video
            response = requests.get(ai_channels[0])
            
            if response.status_code == 200:
                # Very basic extraction - in production, use a proper parser or the API
                video_id_match = re.search(r'watch\?v=([a-zA-Z0-9_-]+)', response.text)
                if video_id_match:
                    video_id = video_id_match.group(1)
                    self.youtube_video = {
                        'title': "Latest AI Video",
                        'link': f"https://www.youtube.com/watch?v={video_id}",
                        'channel': "Two Minute Papers"
                    }
        except Exception as e:
            print(f"Error fetching YouTube video: {e}")
            self.youtube_video = {
                'title': "AI Explained: Latest in Generative Models",
                'link': "https://www.youtube.com/watch?v=example",
                'channel': "AI Research Channel"
            }
    
    def generate_prompt_tip(self):
        """Generate a helpful prompt tip for Claude/ChatGPT users."""
        # List of useful prompts
        prompts = [
            "Try this in Claude: 'Explain [complex AI concept] as if you're teaching a high school student who's interested in AI but has no technical background.'",
            "Claude prompt hack: 'I need to write a blog post about [topic]. Can you create an outline with 5 key sections, each with 3 bullet points of what to cover?'",
            "ChatGPT productivity tip: 'Act as a domain expert in [field] and review my draft text for technical accuracy and suggest improvements.'",
            "AI writing prompt: 'Help me craft a tweet thread about [latest AI news]. Make it informative but conversational, with 5 tweets including relevant hashtags.'",
            "Data analysis prompt: 'I have a dataset about [topic]. What are 5 interesting questions I could explore, and how would I approach analyzing each one?'"
        ]
        
        # For a real system, you could use an LLM to generate custom prompts
        # But for the free tier, we'll use a predefined list
        import random
        return random.choice(prompts)
    
    def format_newsletter_content(self):
        """Format all collected content into the newsletter template."""
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        # Generate a catchy headline based on the top news item
        if self.news_items:
            main_story = self.news_items[0]
            headline = f"🤖 {main_story['title'].split(' - ')[0]}"
            
            # Generate subheading
            subheading = f"PLUS: The AI tools reshaping how we work & create"
        else:
            headline = "🤖 AI's Wild Week: Breakthroughs, Breakdowns & Breakthroughs"
            subheading = "PLUS: 3 essential Claude prompts you're not using yet"
        
        newsletter = f"""# Return of the Jed(AI) - {today}

## {headline}

### {subheading}

---

## 👋 Welcome, fellow humans!

Hope your algorithms are optimized and your neural nets are firing on all nodes today.

Let's dive into the latest from the AI universe—where the machines are learning faster, 
but we're still the ones asking the important questions.

---

## 📰 Main Story
"""
        
        # Add main article
        if self.news_items:
            main_news = self.news_items[0]
            newsletter += f"""
### 🚀 {main_news['title'].split(' - ')[0]}

{main_news['summary']}

**Why it matters**: This development could reshape how AI is developed and deployed in everyday applications.

[Read the full story →]({main_news['link']})

---
"""
        
        # Add prompt tip of the day
        prompt_tip = self.generate_prompt_tip()
        newsletter += f"""
## 💡 Prompt Magic of the Day

{prompt_tip}

Try it out and let us know your results!

---
"""
        
        # Add AI tools list
        newsletter += f"""
## 🧰 AI Toolkit: New & Noteworthy

"""
        for i, tool in enumerate(self.ai_tools[:3]):
            newsletter += f"- **{tool['name']}** → {tool['description']}\n"
        
        newsletter += """
[Explore all tools →](https://www.example.com/tools)

---
"""
        
        # Add quick hits section
        newsletter += """
## 🌀 Around the Horn (Quick Hits)

"""
        # Use the next 4-5 news items for quick hits
        for i, news in enumerate(self.news_items[1:6]):
            company = news['title'].split(':')[0] if ':' in news['title'] else news['source']
            headline = news['title'].split(' - ')[0].split(': ')[-1] if ': ' in news['title'] else news['title'].split(' - ')[0]
            newsletter += f"- **{company}**: {headline}\n"
        
        # Add YouTube video recommendation
        if self.youtube_video:
            newsletter += f"""
---

## 🎧 This Week in AI (Video Pick)

**{self.youtube_video['title']}** from {self.youtube_video['channel']}

[Watch Now →]({self.youtube_video['link']})

"""
        
        # Add final CTA
        newsletter += """
---

## 📣 That's a wrap!

Thanks for reading! The best way to support us is by sharing this newsletter with a friend.

👉 [Subscribe] | [Visit our site] | [Explore AI tools]

"""
        return newsletter
    
    def update_google_doc(self, content):
        """Update the Google Doc with the formatted newsletter content."""
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1  # Insert at the beginning of the document
                    },
                    'text': content
                }
            }
        ]
        
        try:
            result = self.docs_service.documents().batchUpdate(
                documentId=self.doc_id,
                body={'requests': requests}
            ).execute()
            
            print(f"Document updated successfully at {datetime.datetime.now()}")
            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False
    
    def run(self):
        """Run the complete newsletter generation process."""
        print("Starting AI Newsletter Agent...")
        
        # Fetch all content
        self.fetch_ai_news()
        self.fetch_ai_tools()
        self.fetch_youtube_video()
        
        # Format into newsletter
        newsletter_content = self.format_newsletter_content()
        
        # Update Google Doc
        success = self.update_google_doc(newsletter_content)
        
        if success:
            print("Newsletter updated successfully!")
            return {
                "status": "success",
                "timestamp": datetime.datetime.now().isoformat(),
                "articles_found": len(self.news_items),
                "tools_found": len(self.ai_tools)
            }
        else:
            print("Failed to update newsletter.")
            return {
                "status": "error",
                "timestamp": datetime.datetime.now().isoformat()
            }

# Main execution
if __name__ == "__main__":
    agent = AINewsletterAgent()
    result = agent.run()
    print(json.dumps(result))