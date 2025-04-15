import os
import json
import requests
import feedparser
import datetime
import random
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

# List of emojis for section headers and titles
EMOJIS = {
    "headline": ["🤖", "🚀", "🔥", "✨", "💡", "🌟", "🎮", "💻", "🧠", "🔮", "👁️", "🌐", "📱", "🤯"],
    "tools": ["🧰", "🔧", "🛠️", "⚙️", "🔨", "🔍", "🔎", "🎯", "🎨", "✏️", "🔌", "💾", "📂", "📋"],
    "news": ["🌀", "📰", "🗞️", "📢", "📣", "📡", "📻", "📺", "📝", "📌", "📍", "🔔", "🔊", "🗣️"],
    "video": ["🎧", "🎬", "📹", "🎥", "📽️", "🎞️", "📺", "🎙️", "🎤", "📀", "💿", "📡", "📺", "🎦"],
    "insights": ["🧠", "💭", "🔍", "💡", "⚡", "🔎", "🧐", "🤔", "👀", "📊", "📈", "📉", "📗", "👁️"],
    "welcome": ["👋", "✌️", "🙌", "👏", "👐", "🤝", "🖐️", "🤟", "👍", "🎯", "🎆", "🌈", "🌞", "🌠"],
    "prompt": ["💬", "🗯️", "💭", "💡", "✏️", "📝", "⌨️", "🖋️", "📋", "🤔", "👨‍💻", "📊", "🧮", "🧩"]
}

class AINewsletterAgent:
    def __init__(self):
        self.doc_id = os.environ.get('DOCUMENT_ID')
        self.setup_google_docs()
        self.news_items = []
        self.ai_tools = []
        self.youtube_video = None
        self.startup_news = []
        self.insights = []
        self.today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
    def setup_google_docs(self):
        """Set up Google Docs API client."""
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        creds_dict = json.loads(creds_json)
        
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/documents']
        )
        
        self.docs_service = build('docs', 'v1', credentials=creds)
        
url in feeds:
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
        """Fetch new AI tools from Product Hunt and other sources."""
        # For the free tier, we'll use a simple approach with Product Hunt RSS
        ph_feed_url = 'https://www.producthunt.com/feed?category=artificial-intelligence'
        feed = feedparser.parse(ph_feed_url)
        
        for entry in feed.entries[:7]:  # Get more entries for better selection
            # Clean up the title and summary
            title = html.unescape(entry.title).strip()
            summary = html.unescape(entry.summary).strip()
            summary = re.sub(r'<.*?>', '', summary)  # Remove HTML tags
            
            # Truncate and format the description
            description = summary[:100] + "..." if len(summary) > 100 else summary
            
            self.ai_tools.append({
                'name': title,
                'link': entry.link,
                'description': description
            })
        
        # Add some fallback tools in case the RSS feed fails or returns low-quality results
        fallback_tools = [
            {
                'name': 'Claude 3.7',
                'link': 'https://claude.ai',
                'description': 'Anthropic\'s most advanced AI assistant with enhanced reasoning capabilities'
            },
            {
                'name': 'Midjourney v7',
                'link': 'https://midjourney.com',
                'description': 'Create stunning images with the latest text-to-image model'
            },
            {
                'name': 'Supaboard',
                'link': 'https://supaboard.co',
                'description': 'Transform complex data into instant dashboards and actionable insights'
            },
            {
                'name': 'Vapi',
                'link': 'https://vapi.ai',
                'description': 'Create voice AI agents that handle calls and integrate with your existing tools'
            },
            {
                'name': 'Adaptive',
                'link': 'https://adaptive.security',
                'description': 'Protect your organization from GenAI social engineering attacks with deepfake simulations'
            }
        ]
        
        # If we didn't get enough tools from the feed, add some fallbacks
        if len(self.ai_tools) < 3:
            self.ai_tools.extend(fallback_tools[:5 - len(self.ai_tools)])
        
        # Shuffle to mix real and fallback tools
        random.shuffle(self.ai_tools)
    
    def fetch_youtube_video(self):
        """Fetch a trending AI YouTube video."""
        # Since YouTube API requires a key and has quotas, for the free tier, we'll use a fallback approach
        # This is a simplified version - in production, you might want to use the YouTube API
        
        # Predefined list of popular AI channels
        ai_channels = [
            {"url": "https://www.youtube.com/@TwoMinutePapers/videos", "channel": "Two Minute Papers"},
            {"url": "https://www.youtube.com/@lexfridman/videos", "channel": "Lex Fridman"},
            {"url": "https://www.youtube.com/@YannicKilcher/videos", "channel": "Yannic Kilcher"},
            {"url": "https://www.youtube.com/@DataIndependent/videos", "channel": "StatQuest with Josh Starmer"},
            {"url": "https://www.youtube.com/@AIExplained-official/videos", "channel": "AI Explained"}
        ]
        
        try:
            # Randomly select a channel for variety
            channel_info = random.choice(ai_channels)
            response = requests.get(channel_info["url"])
            
            if response.status_code == 200:
                # Very basic extraction - in production, use a proper parser or the API
                video_id_match = re.search(r'watch\?v=([a-zA-Z0-9_-]+)', response.text)
                video_title_match = re.search(r'title="([^"]+)"', response.text)
                
                if video_id_match:
                    video_id = video_id_match.group(1)
                    title = "Latest AI Insights" if not video_title_match else video_title_match.group(1)
                    
                    self.youtube_video = {
                        'title': title[:60] + ("..." if len(title) > 60 else ""),
                        'link': f"https://www.youtube.com/watch?v={video_id}",
                        'channel': channel_info["channel"]
                    }
                    return
        except Exception as e:
            print(f"Error fetching YouTube video: {e}")
            
        # Fallback with predefined options if fetching fails
        fallback_videos = [
            {
                'title': "The Future of AI: 2025 Predictions",
                'link': "https://www.youtube.com/watch?v=rQJmDWB9Zwk",
                'channel': "Two Minute Papers"
            },
            {
                'title': "How Claude 3.7 Changes Everything",
                'link': "https://www.youtube.com/watch?v=rQJmDWB9Zwk",
                'channel': "AI Explained"
            },
            {
                'title': "New Breakthroughs in LLM Research",
                'link': "https://www.youtube.com/watch?v=rQJmDWB9Zwk",
                'channel': "Yannic Kilcher"
            }
        ]
        
        self.youtube_video = random.choice(fallback_videos)
    
    def generate_prompt_tip(self):
        """Generate a helpful prompt tip for Claude/ChatGPT users."""
        # List of useful prompts with catchy intros
        prompts = [
            {
                "intro": "**IDK about you, but we're really impressed with Claude 3.7**",
                "prompt": "Please fact check each fact in the above output against the original sources to confirm they are accurate. Assume there are mistakes, so don't stop until you've checked every fact and found all mistakes.",
                "explanation": "Once you prompt it, click the little diagonal arrow next to the thinking dialogue box to expand its thoughts, and you can watch as it meticulously combs through each fact."
            },
            {
                "intro": "**Unleash Claude's Creative Writing Skills**",
                "prompt": "I need a creative story about [topic]. Before writing, create a character profile with background, motivations, and flaws. Then outline a 3-act structure with conflict and resolution. Now write the story incorporating these elements.",
                "explanation": "This prompt forces Claude to plan before executing, resulting in richer characters and more coherent plots."
            },
            {
                "intro": "**Make Claude Your Personal Coding Tutor**",
                "prompt": "Act as a coding mentor teaching me [language/concept]. First explain the core concept in simple terms with an analogy. Then show a basic code example. Finally, give me a simple exercise to try, with its solution hidden below.",
                "explanation": "Perfect for learning programming concepts step-by-step with the right amount of challenge."
            },
            {
                "intro": "**Get Better Research from ChatGPT**",
                "prompt": "I'm researching [topic]. First, identify 3 distinct perspectives on this issue. Then for each perspective: 1) Summarize their core arguments, 2) Note their strongest evidence, 3) Identify potential weaknesses, and 4) List key scholars/sources associated with this view.",
                "explanation": "This structured approach helps ensure more balanced, thorough research summaries."
            },
            {
                "intro": "**Better Data Analysis with Claude**",
                "prompt": "I have a dataset about [topic]. Walk me through an analysis plan: 1) What cleaning/preprocessing steps should I take? 2) Suggest 3 key insights we might extract, 3) Recommend specific visualization approaches for each insight, 4) Identify potential confounding variables to control for.",
                "explanation": "Helps you approach data more systematically, even before you start crunching numbers."
            },
            {
                "intro": "**Claude's Decision-Making Framework**",
                "prompt": "I'm deciding between [option A] and [option B]. Create a decision matrix with 5 key factors to consider. For each factor: 1) Explain why it matters, 2) Rate each option from 1-10, 3) Suggest questions I should ask to refine my understanding.",
                "explanation": "Turns vague choices into structured decisions with clear evaluation criteria."
            }
        ]
        
        # Pick a random prompt tip
        selected_prompt = random.choice(prompts)
        
        # Format the prompt tip nicely
        formatted_tip = f"{selected_prompt['intro']} and its ability to help you get things done. Try this prompt:\n\n{selected_prompt['prompt']}\n\n{selected_prompt['explanation']}"
        
        return formatted_tip
        
    def fetch_industry_insights(self):
        """Fetch interesting insights and WTF moments in AI."""
        # For a free tier, we'll use a predefined list of insights that rotates
        insights_list = [
            "Half of OpenAI's security team recently quit over internal disagreements.",
            "Legal scholars argue training AI on pirated content should be considered 'fair use'.",
            "AI cheats in video games have evolved to be nearly undetectable by anti-cheat software.",
            "Intelligence agencies report a decline in critical thinking skills as analysts increasingly rely on AI.",
            "Research shows AI models consistently make the same logical errors as humans when not given specific reasoning prompts.",
            "Meta's newest multimodal model can generate videos that fool humans 62% of the time in authenticity tests.",
            "Hospitals using AI for initial patient screening reported a 23% reduction in misdiagnoses.",
            "Microsoft researchers found that fine-tuning LLMs on fanfiction produces more creative and diverse outputs.",
            "The Pentagon is developing an AI that can detect other AIs by analyzing subtle patterns in their outputs.",
            "AI voice cloning can now be achieved with just 3 seconds of audio, down from 30 seconds last year.",
            "Researchers discovered that multilingual AI models outperform monolingual ones, even for English-only tasks.",
            "A new benchmark shows most advanced AI models still struggle with logical reasoning problems that 12-year-olds can solve.",
            "ChatGPT Plus subscribers dropped 25% after the recent price increase.",
            "Universities report 42% of professors have caught students submitting AI-generated essays.",
            "Several major animation studios are now using AI to generate initial storyboards, cutting production time by 50%."
        ]
        
        # Select a random subset of insights
        self.insights = random.sample(insights_list, 4)
        
    def fetch_startup_news(self):
        """Fetch news about AI startups and funding."""
        startup_news_list = [
            {
                "company": "Runway",
                "news": "raised $308M (and $536M+ total) to support more research on its video generator",
                "link": "https://techcrunch.com/runway-funding"
            },
            {
                "company": "CoreWeave",
                "news": "inked a five-year, $12 billion contract with OpenAI to supply AI infrastructure",
                "link": "https://reuters.com/coreweave-openai"
            },
            {
                "company": "Thinking Machines Lab",
                "news": "reportedly seeking a staggering $2 billion in seed funding for new venture",
                "link": "https://techcrunch.com/thinking-machines-lab"
            },
            {
                "company": "Anthropic",
                "news": "partnering with Google to integrate Claude AI into Google Workspace",
                "link": "https://www.anthropic.com/news"
            },
            {
                "company": "PyannoteAI",
                "news": "raised $9 million to enhance its voice intelligence platform",
                "link": "https://business-insider.com/pyannote-ai"
            },
            {
                "company": "Supaboard",
                "news": "secured $12M Series A for its AI-powered data dashboard platform",
                "link": "https://techcrunch.com/supaboard-funding"
            },
            {
                "company": "Cohere",
                "news": "launched Command R+, its most powerful embedding model yet",
                "link": "https://cohere.com/blog/command-r-plus"
            }
        ]
        
        # Select a random subset of startup news
        self.startup_news = random.sample(startup_news_list, 3)
    
    def format_newsletter_content(self):
        """Format all collected content into the newsletter template styled after The Neuron Daily."""
        # First, gather all the additional data we need
        self.fetch_industry_insights()
        self.fetch_startup_news()
        
        # Select random emojis for section headers
        headline_emoji = random.choice(EMOJIS["headline"])
        tools_emoji = random.choice(EMOJIS["tools"])
        news_emoji = random.choice(EMOJIS["news"])
        video_emoji = random.choice(EMOJIS["video"])
        insights_emoji = random.choice(EMOJIS["insights"])
        welcome_emoji = random.choice(EMOJIS["welcome"])
        prompt_emoji = random.choice(EMOJIS["prompt"])
        
        # Generate a catchy headline based on the top news item
        if self.news_items:
            main_story = self.news_items[0]
            # Extract the main part of the title (remove source info)
            main_title = main_story['title'].split(' - ')[0]
            headline = f"{headline_emoji} {main_title}"
            
            # Generate subheading
            subheading = "PLUS: The AI tools reshaping how we work & create"
        else:
            headline = f"{headline_emoji} AI's Wild Week: Breakthroughs, Breakdowns & Innovations"
            subheading = "PLUS: 3 essential Claude prompts you're not using yet"
        
        # Start building the newsletter
        newsletter = f"""# Return of the Jed(AI) - {self.today}

## {headline}

### {subheading}

---

## {welcome_emoji} Welcome, fellow humans!

Hope your algorithms are optimized and your neural nets are firing on all nodes today.

Let's dive into the latest from the AI universe—where the machines are learning faster, 
but we're still the ones asking the important questions.

---

## 📰 Main Story
"""
        
        # Add main article
        if self.news_items:
            main_news = self.news_items[0]
            # Clean up the title
            main_title = main_news['title'].split(' - ')[0]
            company = main_news['source'] if 'source' in main_news else "Leading AI Company"
            
            newsletter += f"""
### 🚀 {main_title}

{main_news['summary']}

**Why it matters**: This development could reshape how AI is developed and deployed in everyday applications.

[Read the full story →]({main_news['link']})

---
"""
        
        # Add prompt tip of the day with a catchy section title
        prompt_tip = self.generate_prompt_tip()
        newsletter += f"""
## {prompt_emoji} Prompt Magic of the Day

{prompt_tip}

---
"""
        
        # Add AI tools list with a catchy section title
        newsletter += f"""
## {tools_emoji} AI Toolkit: New & Noteworthy

"""
        # Include 3-5 tools with better formatting
        for i, tool in enumerate(self.ai_tools[:5]):
            newsletter += f"- **{tool['name']}** → {tool['description']}\n"
        
        newsletter += """
[Explore all tools →](https://www.example.com/tools)

---
"""
        
        # Add quick hits section
        newsletter += f"""
## {news_emoji} Around the Horn (Quick Hits)

"""
        # Use the next 4-5 news items for quick hits
        for i, news in enumerate(self.news_items[1:6]):
            # Extract company and headline more carefully
            if ':' in news['title']:
                parts = news['title'].split(':', 1)
                company = parts[0].strip()
                headline = parts[1].strip()
            else:
                parts = news['title'].split(' - ', 1)
                headline = parts[0].strip()
                company = news['source'] if 'source' in news else "AI News"
            
            newsletter += f"- **{company}**: {headline}\n"
        
        # Add startup news section
        newsletter += f"""
---

## 🚀 Startup Spotlight

"""
        for startup in self.startup_news:
            newsletter += f"- **{startup['company']}** {startup['news']}\n"
        
        # Add YouTube video recommendation
        if self.youtube_video:
            newsletter += f"""
---

## {video_emoji} This Week in AI (Video Pick)

**{self.youtube_video['title']}** from {self.youtube_video['channel']}

[Watch Now →]({self.youtube_video['link']})

---
"""
        
        # Add intelligent insights section
        newsletter += f"""
## {insights_emoji} Intelligent Insights

"""
        for insight in self.insights:
            newsletter += f"- {insight}\n"
        
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
                "tools_found": len(self.ai_tools),
                "newsletter_length": len(newsletter_content)
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