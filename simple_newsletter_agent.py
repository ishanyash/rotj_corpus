import os
import json
import requests
import feedparser
import datetime
import random
import re
import html
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Set up basic logging
def log(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {timestamp} - {message}")

# Emojis for section headers
EMOJIS = {
    "headline": ["🤖", "🚀", "🔥", "✨", "💡", "🌟", "🎮", "💻", "🧠", "🔮", "👁️", "🌐", "📱", "🤯"],
    "tools": ["🧰", "🔧", "🛠️", "⚙️", "🔨", "🔍", "🔎", "🎯", "🎨", "✏️", "🔌", "💾", "📂", "📋"],
    "news": ["🌀", "📰", "🗞️", "📢", "📣", "📡", "📻", "📺", "📝", "📌", "📍", "🔔", "🔊", "🗣️"],
    "video": ["🎧", "🎬", "📹", "🎥", "📽️", "🎞️", "📺", "🎙️", "🎤", "📀", "💿", "📡", "📺", "🎦"],
    "insights": ["🧠", "💭", "🔍", "💡", "⚡", "🔎", "🧐", "🤔", "👀", "📊", "📈", "📉", "📗", "👁️"],
    "welcome": ["👋", "✌️", "🙌", "👏", "👐", "🤝", "🖐️", "🤟", "👍", "🎯", "🎆", "🌈", "🌞", "🌠"],
    "prompt": ["💬", "🗯️", "💭", "💡", "✏️", "📝", "⌨️", "🖋️", "📋", "🤔", "👨‍💻", "📊", "🧮", "🧩"]
}

class NewsletterAgent:
    def __init__(self):
        log("Initializing Newsletter Agent")
        # Get credentials from environment variables
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        self.doc_id = os.environ.get('DOCUMENT_ID')
        
        if not creds_json or not self.doc_id:
            log("Missing environment variables. Make sure GOOGLE_CREDENTIALS and DOCUMENT_ID are set.", "ERROR")
            raise ValueError("Missing required environment variables")
            
        # Initialize API client
        try:
            creds_dict = json.loads(creds_json)
            creds = service_account.Credentials.from_service_account_info(
                creds_dict, 
                scopes=['https://www.googleapis.com/auth/documents']
            )
            self.docs_service = build('docs', 'v1', credentials=creds)
            log("Google Docs API client initialized")
        except Exception as e:
            log(f"Failed to initialize Google Docs API client: {str(e)}", "ERROR")
            raise
            
        # Initialize data containers
        self.news_items = []
        self.ai_tools = []
        self.youtube_video = None
        self.today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
    def fetch_ai_news(self):
        """Fetch AI news from Google News RSS feed."""
        log("Fetching AI news")
        
        # Define AI and tech related RSS feeds
        feeds = [
            'https://news.google.com/rss/search?q=artificial+intelligence+when:1d&hl=en-US&gl=US&ceid=US:en',
            'https://news.google.com/rss/search?q=machine+learning+when:1d&hl=en-US&gl=US&ceid=US:en',
            'https://news.google.com/rss/search?q=openai+when:1d&hl=en-US&gl=US&ceid=US:en',
            'https://news.google.com/rss/search?q=anthropic+claude+when:1d&hl=en-US&gl=US&ceid=US:en',
            'https://news.google.com/rss/search?q=generative+ai+when:1d&hl=en-US&gl=US&ceid=US:en'
        ]
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:3]:  # Get top 3 entries from each feed
                    # Basic cleaning
                    title = html.unescape(entry.title) if hasattr(entry, 'title') else "Untitled"
                    
                    # Check if this is relevant to AI
                    ai_related_terms = ['artificial intelligence', 'ai', 'machine learning', 'openai', 
                                       'anthropic', 'claude', 'gpt', 'llm', 'deep learning']
                    
                    is_relevant = any(term in title.lower() for term in ai_related_terms)
                    
                    if is_relevant:
                        # Get the summary and clean it up
                        if hasattr(entry, 'summary'):
                            summary = html.unescape(entry.summary)
                            # Remove HTML tags
                            summary = re.sub(r'<.*?>', '', summary)
                        else:
                            summary = "No summary available."
                        
                        # Trim summary if too long
                        if len(summary) > 300:
                            summary = summary[:297] + "..."
                        
                        # Extract the source from the title if available
                        source = "AI News"
                        if ' - ' in title:
                            title_parts = title.split(' - ')
                            if len(title_parts) > 1:
                                source = title_parts[-1]
                                title = ' - '.join(title_parts[:-1])
                        
                        # Add to our news items
                        self.news_items.append({
                            'title': title,
                            'link': entry.link if hasattr(entry, 'link') else "#",
                            'published': entry.published if hasattr(entry, 'published') else datetime.datetime.now().isoformat(),
                            'summary': summary,
                            'source': source
                        })
                        
            except Exception as e:
                log(f"Error fetching feed {feed_url}: {str(e)}", "WARNING")
                continue
        
        # If we didn't get enough news, add fallbacks
        if len(self.news_items) < 5:
            log("Adding fallback news items")
            self.add_fallback_news()
        
        # Sort by publication date, newest first
        self.news_items.sort(key=lambda x: x['published'], reverse=True)
        log(f"Collected {len(self.news_items)} news items")
        
    def add_fallback_news(self):
        """Add fallback news items."""
        fallback_news = [
            {
                'title': "OpenAI Makes ChatGPT Plus Free for Students",
                'link': "https://openai.com/blog/chatgpt-plus-free-for-students",
                'published': datetime.datetime.now().isoformat(),
                'summary': "OpenAI announced that ChatGPT Plus will be free for all US and Canadian college students through May. This initiative aims to help students with research, learning, and productivity.",
                'source': "OpenAI Blog"
            },
            {
                'title': "Anthropic's Claude AI Is Coming to Google Workspace",
                'link': "https://www.anthropic.com/news",
                'published': datetime.datetime.now().isoformat(),
                'summary': "Anthropic announced a partnership with Google to integrate Claude AI into Google Workspace. This will allow users to access Claude's capabilities directly within Gmail, Docs, and other Google services.",
                'source': "Anthropic"
            },
            {
                'title': "DeepMind's Dreamer AI Teaches Itself Minecraft",
                'link': "https://deepmind.com/blog",
                'published': datetime.datetime.now().isoformat(),
                'summary': "DeepMind developed an AI system called Dreamer that figured out how to collect diamonds in Minecraft without being taught how to play, using reinforcement learning and a 'world model' to imagine future scenarios.",
                'source': "DeepMind"
            },
            {
                'title': "Spotify Introduces Gen AI Ads for Script Generation",
                'link': "https://techcrunch.com/spotify-gen-ai-ads",
                'published': datetime.datetime.now().isoformat(),
                'summary': "Spotify introduced new Gen AI Ads for creating scripts and voiceovers at no extra cost to advertisers. The tool aims to streamline the ad creation process for podcasts and audio content.",
                'source': "TechCrunch"
            },
            {
                'title': "Runway Raises $308M for AI Video Generation",
                'link': "https://techcrunch.com/runway-funding",
                'published': datetime.datetime.now().isoformat(),
                'summary': "Runway, the startup behind popular text-to-video and image-to-video generation tools, has raised $308 million in new funding at a $1.8 billion valuation to continue developing its AI video technology.",
                'source': "TechCrunch"
            }
        ]
        
        # Add only as many fallbacks as needed
        needed = max(0, 5 - len(self.news_items))
        self.news_items.extend(fallback_news[:needed])
        
    def fetch_ai_tools(self):
        """Add AI tools to feature in the newsletter."""
        log("Adding AI tools")
        
        # Use predefined tools instead of trying to scrape
        tools = [
            {
                'name': 'Claude 3.7',
                'link': 'https://claude.ai',
                'description': 'Anthropic\'s most advanced AI assistant with enhanced reasoning capabilities and improved context window.'
            },
            {
                'name': 'Midjourney v7',
                'link': 'https://midjourney.com',
                'description': 'Create stunning photorealistic images with the latest text-to-image model featuring improved composition and lighting.'
            },
            {
                'name': 'Supaboard',
                'link': 'https://supaboard.co',
                'description': 'Transform complex data into instant dashboards and actionable insights with natural language queries.'
            },
            {
                'name': 'Vapi',
                'link': 'https://vapi.ai',
                'description': 'Create voice AI agents that sound natural, handle complex calls, and integrate with your existing tools.'
            },
            {
                'name': 'Adaptive',
                'link': 'https://adaptive.security',
                'description': 'Protect your organization from GenAI social engineering attacks with deepfake security simulations.'
            },
            {
                'name': 'Mem AI',
                'link': 'https://mem.ai',
                'description': 'Your AI-powered second brain that automatically organizes notes and surfaces relevant information.'
            },
            {
                'name': 'Cursor',
                'link': 'https://cursor.sh',
                'description': 'The AI-first code editor that helps you understand, edit, and generate code faster with a built-in assistant.'
            }
        ]
        
        # Shuffle and use 5 random tools
        random.shuffle(tools)
        self.ai_tools = tools[:5]
        log(f"Added {len(self.ai_tools)} AI tools")
    
    def add_youtube_recommendation(self):
        """Add YouTube video recommendation."""
        log("Adding YouTube recommendation")
        
        videos = [
            {
                'title': "The Future of AI: 2025 Predictions",
                'link': "https://www.youtube.com/watch?v=rQJmDWB9Zwk",
                'channel': "Two Minute Papers"
            },
            {
                'title': "How Claude 3.7 Changes Everything",
                'link': "https://www.youtube.com/watch?v=E8cfrUV8yiE",
                'channel': "AI Explained"
            },
            {
                'title': "New Breakthroughs in LLM Research",
                'link': "https://www.youtube.com/watch?v=kTPTZ5gsR8g",
                'channel': "Yannic Kilcher"
            },
            {
                'title': "The AI Revolution in Open Source",
                'link': "https://www.youtube.com/watch?v=TqHwwMUZGf4",
                'channel': "Lex Fridman"
            }
        ]
        
        self.youtube_video = random.choice(videos)
        log(f"Selected video: {self.youtube_video['title']}")
        
    def generate_insights(self):
        """Generate interesting insights for the newsletter."""
        log("Generating insights")
        
        insights = [
            "Half of OpenAI's security team recently quit over internal disagreements about safety protocols.",
            "Legal scholars are now arguing that training AI on pirated content should qualify as 'fair use' under copyright law.",
            "AI cheats in competitive video games have evolved to be nearly undetectable by conventional anti-cheat software.",
            "Intelligence agencies report a decline in analysts' critical thinking skills as they increasingly rely on AI for initial assessments.",
            "Research shows AI models consistently make the same logical errors as humans when not explicitly prompted to use step-by-step reasoning.",
            "Meta's newest multimodal model can generate videos that fool human reviewers 62% of the time in authenticity tests.",
            "Hospitals using AI for initial patient screening have reported a 23% reduction in misdiagnoses compared to traditional triage.",
            "Microsoft researchers found that fine-tuning LLMs on fanfiction produces more creative and diverse outputs than using only academic literature.",
            "The Pentagon is developing an AI system that can detect AI-generated content by analyzing subtle patterns in text and images.",
            "Professional voice actors are fighting back against AI cloning by creating deliberately poisoned training data.",
            "AI voice cloning can now be achieved with just 3 seconds of audio, down from 30 seconds last year.",
            "Research shows multilingual AI models consistently outperform monolingual ones, even for English-only tasks."
        ]
        
        # Shuffle and return 4 random insights
        random.shuffle(insights)
        return insights[:4]
    
    def generate_prompt_tip(self):
        """Generate a helpful prompt tip for Claude/ChatGPT users."""
        log("Generating prompt tip")
        
        prompts = [
            {
                "intro": "**Mastering Claude 3.7's Reasoning**",
                "prompt": "Please analyze [topic/problem] step by step. First outline your approach, then work through each step showing your reasoning. Consider at least 3 different perspectives before reaching your conclusion.",
                "explanation": "This structured prompt activates Claude's deeper reasoning capabilities, encouraging methodical analysis rather than rushing to conclusions."
            },
            {
                "intro": "**Unleash Creative Writing with Claude**",
                "prompt": "I need a creative story about [topic]. Before writing, create a character profile with background, motivations, and flaws. Then outline a 3-act structure with conflict and resolution. Now write the story incorporating these elements.",
                "explanation": "This prompt forces Claude to plan before executing, resulting in richer characters and more coherent plots."
            },
            {
                "intro": "**Turn Claude into a Coding Tutor**",
                "prompt": "Act as a coding mentor teaching me [language/concept]. First explain the core concept in simple terms with an analogy. Then show a basic code example. Finally, give me a simple exercise to try, with its solution hidden below.",
                "explanation": "Perfect for learning programming concepts step-by-step with the right amount of challenge."
            },
            {
                "intro": "**Supercharge Your Research**",
                "prompt": "I'm researching [topic]. First, identify 3 distinct perspectives on this issue. Then for each perspective: 1) Summarize their core arguments, 2) Note their strongest evidence, 3) Identify potential weaknesses, and 4) List key scholars/sources associated with this view.",
                "explanation": "This structured approach helps ensure more balanced, thorough research summaries."
            },
            {
                "intro": "**Claude's Fact-Checking Mode**",
                "prompt": "Please fact check each claim in the above output against reliable sources. Assume there are mistakes, so don't stop until you've checked every fact and found all mistakes.",
                "explanation": "Once you prompt it, click the diagonal arrow next to the thinking dialogue box to expand its thoughts, and you can watch as it meticulously combs through each fact."
            }
        ]
        
        # Pick a random prompt tip
        return random.choice(prompts)
        
    def format_newsletter(self):
        """Format the Return of the Jed(AI) newsletter content."""
        log("Formatting newsletter content")
        
        # Get a random emoji for each section
        headline_emoji = random.choice(EMOJIS["headline"])
        tools_emoji = random.choice(EMOJIS["tools"])
        news_emoji = random.choice(EMOJIS["news"])
        video_emoji = random.choice(EMOJIS["video"])
        insights_emoji = random.choice(EMOJIS["insights"])
        welcome_emoji = random.choice(EMOJIS["welcome"])
        prompt_emoji = random.choice(EMOJIS["prompt"])
        
        # Generate a catchy headline based on top news
        if self.news_items:
            main_story = self.news_items[0]
            headline = f"{headline_emoji} {main_story['title']}"
            subheading = "PLUS: The AI tools reshaping how we work & create"
        else:
            headline = f"{headline_emoji} AI's Wild Week: Breakthroughs, Breakdowns & Innovations"
            subheading = "PLUS: Claude prompts you're not using yet"
        
        # Get insights
        insights = self.generate_insights()
        
        # Get prompt tip
        prompt_tip = self.generate_prompt_tip()
        
        # Build the newsletter content in markdown format
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
        
        # Add main article (first news item)
        if self.news_items:
            main_news = self.news_items[0]
            company = main_news['source']
            
            newsletter += f"""
### 🚀 {main_news['title']}

{main_news['summary']}

**Why it matters**: This development could reshape how we interact with AI in everyday applications.

[Read the full story →]({main_news['link']})

---
"""
        
        # Add prompt tip
        newsletter += f"""
## {prompt_emoji} Prompt Magic of the Day

{prompt_tip['intro']}

Try this prompt:

```
{prompt_tip['prompt']}
```

{prompt_tip['explanation']}

---
"""
        
        # Add AI tools section
        newsletter += f"""
## {tools_emoji} AI Toolkit: New & Noteworthy

"""
        # Include tools with formatting
        for tool in self.ai_tools:
            newsletter += f"- **{tool['name']}** → {tool['description']}\n"
        
        newsletter += """
[Explore all tools →](https://returnofthejedai.com/tools)

---
"""
        
        # Add quick hits section
        newsletter += f"""
## {news_emoji} Around the Horn (Quick Hits)

"""
        # Use the next 4 news items for quick hits
        for news in self.news_items[1:5]:
            newsletter += f"- **{news['source']}**: {news['title']}\n"
        
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
        for insight in insights:
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
        """Update the Google Doc with the newsletter content."""
        log("Updating Google Doc")
        
        try:
            # First get the document to check current content
            document = self.docs_service.documents().get(documentId=self.doc_id).execute()
            
            # Create a request to update the document
            requests = [
                {
                    'insertText': {
                        'location': {
                            'index': 1  # Insert at beginning of doc
                        },
                        'text': content
                    }
                }
            ]
            
            # Execute the update
            result = self.docs_service.documents().batchUpdate(
                documentId=self.doc_id,
                body={'requests': requests}
            ).execute()
            
            log("Google Doc updated successfully")
            return True
            
        except Exception as e:
            log(f"Error updating document: {str(e)}", "ERROR")
            return False
    
    def run(self):
        """Run the complete newsletter generation process."""
        log("Starting Return of the Jed(AI) Newsletter Agent")
        
        try:
            # Fetch all content
            self.fetch_ai_news()
            self.fetch_ai_tools()
            self.add_youtube_recommendation()
            
            # Format the newsletter
            newsletter_content = self.format_newsletter()
            
            # Update the Google Doc
            success = self.update_google_doc(newsletter_content)
            
            if success:
                log("Newsletter generation and update completed successfully!")
                return {
                    "status": "success",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "message": "Newsletter updated successfully"
                }
            else:
                log("Failed to update newsletter", "ERROR")
                return {
                    "status": "error",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "message": "Failed to update Google Doc"
                }
                
        except Exception as e:
            log(f"Error in newsletter generation process: {str(e)}", "ERROR")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }

# Main execution
if __name__ == "__main__":
    try:
        agent = NewsletterAgent()
        result = agent.run()
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }, indent=2))