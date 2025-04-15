import os
import json
import requests
import feedparser
import datetime
import random
import traceback
import sys
from datetime import timedelta
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
import re
import html
from transformers import pipeline

# Set up basic logging
def log(message, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{level}] {timestamp} - {message}")

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
        log("Initializing AI Newsletter Agent")
        self.doc_id = os.environ.get('DOCUMENT_ID')
        if not self.doc_id:
            log("ERROR: DOCUMENT_ID environment variable is not set", "ERROR")
            sys.exit(1)
            
        log(f"Using document ID: {self.doc_id}")
        
        # Initialize variables
        self.news_items = []
        self.ai_tools = []
        self.youtube_video = None
        self.startup_news = []
        self.insights = []
        self.today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        # Connect to Google Docs
        self.setup_google_docs()
        
        # Initialize the summarizer (using a lightweight model for the free tier)
        # Only load it when needed to save memory
        self.summarizer = None
        
    def setup_google_docs(self):
        """Set up Google Docs API client with better error handling."""
        log("Setting up Google Docs API client")
        
        creds_json = os.environ.get('GOOGLE_CREDENTIALS')
        if not creds_json:
            log("ERROR: GOOGLE_CREDENTIALS environment variable is not set", "ERROR")
            sys.exit(1)
        
        try:
            creds_dict = json.loads(creds_json)
            log(f"Using service account: {creds_dict.get('client_email', 'unknown')}")
            
            creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=['https://www.googleapis.com/auth/documents']
            )
            
            self.docs_service = build('docs', 'v1', credentials=creds)
            log("Google Docs API client initialized successfully")
            
            # Test the connection by getting document info
            try:
                document = self.docs_service.documents().get(documentId=self.doc_id).execute()
                log(f"Successfully connected to document: '{document.get('title', 'Untitled')}'")
            except Exception as e:
                log(f"ERROR: Failed to access document: {str(e)}", "ERROR")
                if "404" in str(e):
                    log("The document ID may be incorrect or the service account doesn't have access", "ERROR")
                sys.exit(1)
                
        except json.JSONDecodeError:
            log("ERROR: GOOGLE_CREDENTIALS is not valid JSON", "ERROR")
            # Print a limited view of the credentials for debugging
            if creds_json:
                log(f"Credentials start with: {creds_json[:20]}...", "ERROR")
            sys.exit(1)
        except Exception as e:
            log(f"ERROR: Failed to set up Google Docs API: {str(e)}", "ERROR")
            traceback.print_exc()
            sys.exit(1)
        
    def load_summarizer(self):
        """Load the summarizer model only when needed."""
        if not self.summarizer:
            log("Loading summarization model...")
            try:
                self.summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
                log("Summarization model loaded successfully")
            except Exception as e:
                log(f"ERROR: Failed to load summarization model: {str(e)}", "ERROR")
                # Continue without summarization capabilities
                pass
                
    def fetch_ai_news(self):
        """Fetch AI news from Google News RSS feed with improved error handling."""
        log("Fetching AI news...")
        
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
                log(f"Parsing feed: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                if not feed.entries:
                    log(f"No entries found in feed: {feed_url}")
                    continue
                    
                log(f"Found {len(feed.entries)} entries in feed")
                
                for entry in feed.entries[:5]:  # Get the top 5 entries from each feed
                    try:
                        # Basic cleaning
                        title = html.unescape(entry.title) if hasattr(entry, 'title') else "Untitled"
                        
                        # Check if this is relevant to AI
                        ai_related_terms = ['artificial intelligence', 'ai', 'machine learning', 'openai', 
                                           'anthropic', 'claude', 'gpt', 'llm', 'deep learning', 'neural network']
                        
                        is_relevant = any(term in title.lower() for term in ai_related_terms)
                        
                        if is_relevant:
                            # Get the summary and clean it up
                            if hasattr(entry, 'summary'):
                                summary = html.unescape(entry.summary)
                                # Remove HTML tags
                                summary = re.sub(r'<.*?>', '', summary)
                            else:
                                summary = "No summary available."
                            
                            # Use the transformer model to create a better summary if the article has content
                            enhanced_summary = summary
                            if len(summary) > 100:
                                try:
                                    # Load the summarizer if needed
                                    self.load_summarizer()
                                    
                                    if self.summarizer:
                                        # Limit input length to avoid out-of-memory issues
                                        if len(summary) > 1024:
                                            text_to_summarize = summary[:1024]
                                        else:
                                            text_to_summarize = summary
                                            
                                        # Generate better summary
                                        ai_summary = self.summarizer(text_to_summarize, 
                                                                  max_length=200, 
                                                                  min_length=100, 
                                                                  do_sample=False)[0]['summary_text']
                                        
                                        enhanced_summary = ai_summary
                                except Exception as e:
                                    log(f"Warning: Error summarizing: {str(e)}", "WARNING")
                                    # Fall back to original summary or trimmed text
                                    enhanced_summary = summary[:500] + "..."
                            
                            # Extract the source from the title if available (usually in format "Title - Source")
                            source = "AI News"
                            if ' - ' in title:
                                title_parts = title.split(' - ')
                                if len(title_parts) > 1:
                                    source = title_parts[-1]
                                    title = ' - '.join(title_parts[:-1])  # Remove source from title
                            
                            # Add to our news items
                            self.news_items.append({
                                'title': title,
                                'link': entry.link if hasattr(entry, 'link') else "",
                                'published': entry.published if hasattr(entry, 'published') else datetime.datetime.now().isoformat(),
                                'summary': enhanced_summary,
                                'source': source
                            })
                            
                            log(f"Added news item: {title}")
                    except Exception as e:
                        log(f"Error processing entry: {str(e)}", "WARNING")
                        continue
                        
            except Exception as e:
                log(f"Error fetching feed {feed_url}: {str(e)}", "WARNING")
                continue
        
        log(f"Fetched {len(self.news_items)} AI news items")
        
        # If we got fewer than 5 news items, add some fallbacks
        if len(self.news_items) < 5:
            log("Adding fallback news items")
            self.add_fallback_news()
        
        # Sort by publication date, newest first
        self.news_items.sort(key=lambda x: x['published'], reverse=True)
        
    def add_fallback_news(self):
        """Add fallback news items if we didn't get enough from feeds."""
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
            }
        ]
        
        # Add only as many fallbacks as needed to reach 5 news items
        needed_fallbacks = max(0, 5 - len(self.news_items))
        self.news_items.extend(fallback_news[:needed_fallbacks])
        
    def fetch_ai_tools(self):
        """Fetch new AI tools from Product Hunt and other sources."""
        log("Fetching AI tools...")
        
        # For the free tier, we'll use a simple approach with Product Hunt RSS
        ph_feed_url = 'https://www.producthunt.com/feed?category=artificial-intelligence'
        try:
            feed = feedparser.parse(ph_feed_url)
            
            if not feed.entries:
                log("No entries found in Product Hunt feed")
            else:
                log(f"Found {len(feed.entries)} tools in Product Hunt feed")
                
            for entry in feed.entries[:7]:  # Get more entries for better selection
                try:
                    # Clean up the title and summary
                    title = html.unescape(entry.title).strip() if hasattr(entry, 'title') else "Untitled Tool"
                    summary = ""
                    if hasattr(entry, 'summary'):
                        summary = html.unescape(entry.summary).strip()
                        # Remove HTML tags
                        summary = re.sub(r'<.*?>', '', summary)
                    
                    # Truncate and format the description
                    description = summary[:150] + "..." if len(summary) > 150 else summary
                    
                    # Ensure we have a link
                    link = entry.link if hasattr(entry, 'link') else "https://producthunt.com"
                    
                    self.ai_tools.append({
                        'name': title,
                        'link': link,
                        'description': description
                    })
                    
                    log(f"Added tool: {title}")
                except Exception as e:
                    log(f"Error processing tool entry: {str(e)}", "WARNING")
                    continue
                    
        except Exception as e:
            log(f"Error fetching Product Hunt feed: {str(e)}", "WARNING")
        
        log(f"Fetched {len(self.ai_tools)} AI tools")
        
        # If we didn't get enough tools, add some fallbacks
        if len(self.ai_tools) < 5:
            log("Adding fallback tools")
            self.add_fallback_tools()
        
        # Shuffle to mix real and fallback tools
        random.shuffle(self.ai_tools)
        
    def add_fallback_tools(self):
        """Add fallback AI tools."""
        fallback_tools = [
            {
                'name': 'Claude 3.7',
                'link': 'https://claude.ai',
                'description': 'Anthropic\'s most advanced AI assistant with enhanced reasoning capabilities and improved context window, now with 200K tokens.'
            },
            {
                'name': 'Midjourney v7',
                'link': 'https://midjourney.com',
                'description': 'Create stunning photorealistic images with the latest text-to-image model featuring improved composition, lighting, and prompt understanding.'
            },
            {
                'name': 'Supaboard',
                'link': 'https://supaboard.co',
                'description': 'Transform complex data into instant dashboards and actionable insights with natural language queries and AI-powered visualization recommendations.'
            },
            {
                'name': 'Vapi',
                'link': 'https://vapi.ai',
                'description': 'Create voice AI agents that sound natural, handle complex calls, and integrate with your existing tools. Now offering 50+ realistic voice options.'
            },
            {
                'name': 'Adaptive',
                'link': 'https://adaptive.security',
                'description': 'Protect your organization from GenAI social engineering attacks by simulating deepfake security threats and training your team to identify them.'
            },
            {
                'name': 'Mem AI',
                'link': 'https://mem.ai',
                'description': 'Your AI-powered second brain that automatically organizes notes, generates summaries, and surfaces relevant information when you need it.'
            },
            {
                'name': 'Cursor',
                'link': 'https://cursor.sh',
                'description': 'The AI-first code editor that helps you understand, edit, and generate code faster with a built-in programming assistant.'
            }
        ]
        
        # Add only as many fallbacks as needed
        needed_fallbacks = max(0, 5 - len(self.ai_tools))
        self.ai_tools.extend(fallback_tools[:needed_fallbacks])
    
    def fetch_youtube_video(self):
        """Fetch a trending AI YouTube video with better error handling."""
        log("Fetching YouTube video recommendations...")
        
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
            log(f"Attempting to fetch video from: {channel_info['channel']}")
            
            response = requests.get(channel_info["url"], timeout=10)
            
            if response.status_code == 200:
                # More robust extraction with improved regex
                video_id_match = re.search(r'watch\?v=([a-zA-Z0-9_-]{11})', response.text)
                
                # Try to extract title using regex for better compatibility
                title = "Latest AI Video"
                title_match = re.search(r'title="([^"]+)"', response.text)
                if title_match:
                    title = title_match.group(1)
                
                if video_id_match:
                    video_id = video_id_match.group(1)
                    
                    self.youtube_video = {
                        'title': title[:80] + ("..." if len(title) > 80 else ""),
                        'link': f"https://www.youtube.com/watch?v={video_id}",
                        'channel': channel_info["channel"]
                    }
                    
                    log(f"Found video: {self.youtube_video['title']}")
                    return
                else:
                    log("Could not find a valid video ID")
            else:
                log(f"Failed to fetch channel page: HTTP {response.status_code}")
                
        except Exception as e:
            log(f"Error fetching YouTube video: {str(e)}", "WARNING")
            
        # Fallback with predefined options if fetching fails
        self.use_fallback_video()
        
    def use_fallback_video(self):
        """Use fallback video if fetching fails."""
        log("Using fallback YouTube video")
        
        fallback_videos = [
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
        
        self.youtube_video = random.choice(fallback_videos)
        log(f"Selected fallback video: {self.youtube_video['title']}")
        
    def format_newsletter_content(self):
        """Format the content for the Return of the Jed(AI) newsletter."""
        log("Formatting newsletter content")
        
        # Generate a catchy headline based on top news
        headline = self.generate_headline()
        
        # Generate a subheading/teaser
        subheading = self.generate_subheading()
        
        # Random emoji selection for sections
        emoji = lambda category: random.choice(EMOJIS.get(category, ["✨"]))
        
        # Format the newsletter content
        formatted_content = f"""# Return of the Jed(AI): AI Newsletter

## {emoji('headline')} {headline}
### PLUS: {subheading}

### 👋 Welcome, humans!

Happy {self.today}! 

Hope your algorithms are optimized and your neural networks are firing on all nodes today.

Today we're diving into the latest AI happenings across the galaxy - from groundbreaking research to cool new tools that might just make your life easier (or at least more interesting).

Let's jump to hyperspace!

## 📰 Today's Main Story

"""
        
        # Add the main story (first news item)
        if self.news_items:
            main_story = self.news_items[0]
            story_title = main_story['title']
            
            # Create a catchy subheading for the main story
            main_subheading = self.generate_story_subheading(main_story)
            
            formatted_content += f"### {emoji('insights')} {main_subheading}\n\n"
            formatted_content += f"**{story_title}**\n\n"
            
            # Add full text if available, otherwise use summary
            story_content = main_story.get('summary', 'No details available.')
                
            formatted_content += f"{story_content}\n\n"
            formatted_content += f"Source: {main_story.get('source', 'Unknown')}\n"
            formatted_content += f"[Read more →]({main_story.get('link', '')})\n\n"
        
        # Add prompt tip section
        prompt_tip = self.generate_prompt_tip()
        
        formatted_content += f"""## {emoji('prompt')} AI Whispering: Prompt Tip of the Day

{prompt_tip['title']}

```
{prompt_tip['prompt']}
```

**Why it works:** {prompt_tip['explanation']}

## {emoji('tools')} AI Tool Spotlight: Try These Today

"""
        
        # Add 3-5 AI tools
        tool_count = min(5, len(self.ai_tools))
        for i in range(tool_count):
            tool = self.ai_tools[i]
            formatted_content += f"- **{tool['name']}** → {tool['description']}\n  [Check it out]({tool['link']})\n"
            
        formatted_content += f"\n## {emoji('news')} Around the Horn: Quick Hits\n\n"
        
        # Add secondary news items as quick hits
        for i, news in enumerate(self.news_items[1:6]):  # Use items 2-6 (skipping the main story)
            source = news.get('source', 'Unknown')
            title_text = news['title']
            # Truncate if too long
            if len(title_text) > 80:
                title_text = title_text[:77] + "..."
            formatted_content += f"- **{source}:** {title_text}\n  [Read more]({news.get('link', '')})\n"
            
        # Add YouTube recommendation
        if self.youtube_video:
            formatted_content += f"\n## {emoji('video')} Watch This: YouTube Pick\n\n"
            formatted_content += f"**{self.youtube_video['title']}** by {self.youtube_video['channel']}\n"
            formatted_content += f"[Watch on YouTube →]({self.youtube_video['link']})\n"
            
        # Add interesting insights section
        insights = self.generate_insights()
        formatted_content += f"\n## {emoji('insights')} Neural Firings: Interesting Insights\n\n"
        
        for insight in insights[:5]:  # Limit to 5 insights
            formatted_content += f"- {insight}\n"
            
        # Add closing and CTA
        formatted_content += f"""
## 👋 That's All, Folks!

That's all for today, humans. May your data be clean and your models well-tuned.

The best way to support this newsletter? Share it with a fellow tech enthusiast!

👉 [Subscribe] | [Visit our site] | [Share with a friend]

"""
        
        return formatted_content
        
    def generate_headline(self):
        """Generate a catchy headline based on top news."""
        if not self.news_items:
            return "The AI Universe Is Expanding Faster Than Ever"
            
        # Use the top story for inspiration
        top_story = self.news_items[0]
        title = top_story.get('title', '')
        
        # Create headline variations based on the content
        headlines = [
            f"AI Revolution: {title.split(':')[0] if ':' in title else title.split(' - ')[0]}",
            "Breaking Barriers: How AI Is Redefining What's Possible",
            f"From Sci-Fi to Reality: {title.split(':')[0] if ':' in title else title.split(' - ')[0]}",
            "The Future Is Now: This Week's Game-Changing AI Developments",
            f"Mind = Blown: {title.split(':')[0] if ':' in title else title}"
        ]
        
        return random.choice(headlines)
        
    def generate_subheading(self):
        """Generate a subheading/teaser."""
        subheadings = [
            "The prompt engineering trick top AI researchers don't want you to know",
            "Why these 3 AI tools should be in every developer's arsenal",
            "How to make AI work FOR you, not the other way around",
            "The surprising way Claude 3.7 is outperforming its competitors",
            "Meet the startup threatening OpenAI's dominance overnight",
            "The one AI capability that's evolving faster than anyone predicted"
        ]
        
        return random.choice(subheadings)
        
    def generate_story_subheading(self, story):
        """Generate a catchy subheading for a story."""
        title = story.get('title', '')
        source = story.get('source', '')
        
        # Extract key terms that might be useful
        ai_terms = ['AI', 'GPT', 'Claude', 'neural', 'algorithm', 'Anthropic', 'OpenAI', 
                    'machine learning', 'model', 'LLM', 'AGI', 'intelligence']
                    
        # Check if any terms are in the title
        term_in_title = any(term.lower() in title.lower() for term in ai_terms)
        
        # Generate subheading options
        if 'OpenAI' in title or 'GPT' in title:
            return "OpenAI's Latest Move Has Everyone Talking"
        elif 'Anthropic' in title or 'Claude' in title:
            return "Claude Just Leveled Up The AI Game"
        elif 'Google' in title or 'DeepMind' in title:
            return "Google's AI Ambitions Take A Bold Turn"
        elif 'research' in title.lower() or 'study' in title.lower():
            return "New Research That Changes Everything"
        elif 'launch' in title.lower() or 'release' in title.lower() or 'announce' in title.lower():
            return "Just Launched: The Next Big Thing In AI"
        else:
            return "AI Breakthrough You Need To Know About"
            
    def generate_prompt_tip(self):
        """Generate a prompt tip for the newsletter."""
        prompt_tips = [
            {
                "title": "🧠 Expert Mode Reasoning with Claude 3.7",
                "prompt": "Please analyze [topic/problem] step by step. First outline your approach, then work through each step showing your reasoning. Consider at least 3 different perspectives or methods before reaching your conclusion.",
                "explanation": "This structured prompt activates Claude's deeper reasoning capabilities, encouraging methodical analysis rather than rushing to conclusions."
            },
            {
                "title": "🎨 Create Professional-Quality Content Outlines",
                "prompt": "Create a detailed content outline for [article/video/presentation] about [topic]. Include: 1) An attention-grabbing hook, 2) Main sections with key points for each, 3) Data points or statistics to include, 4) A compelling conclusion, and 5) 3-5 engaging questions for audience interaction.",
                "explanation": "This template helps generate comprehensive content frameworks that consider audience engagement from start to finish."
            },
            {
                "title": "🔍 Detect Hidden Biases in Analysis",
                "prompt": "Analyze this [article/report/argument] about [topic]. First, summarize the main claims. Then identify potential biases in: data selection, methodology, framing, and language choices. Finally, suggest 3 questions someone should ask to develop a more balanced understanding.",
                "explanation": "Helps uncover subtle biases in information sources, perfect for research, news consumption, or evaluating business proposals."
            },
            {
                "title": "🖥️ Debug Code Like a Senior Developer",
                "prompt": "Debug this code: [paste code]. First, explain what this code is trying to do. Then identify potential issues, examining: 1) Logic errors, 2) Edge cases, 3) Performance concerns, and 4) Best practices violations. For each issue, explain the problem and suggest a fix.",
                "explanation": "This prompt transforms basic error identification into comprehensive code review that addresses root causes, not just symptoms."
            },
            {
                "title": "💡 Turn Vague Ideas Into Concrete Projects",
                "prompt": "Help me develop this idea: [your idea]. 1) Ask me 5 clarifying questions, wait for my answers. 2) Define the core value proposition. 3) Outline the minimum viable product features. 4) Identify 3-5 potential challenges and solutions. 5) Suggest next action steps to move forward.",
                "explanation": "This converts abstract concepts into actionable plans through a guided discovery process."
            }
        ]
        
        return random.choice(prompt_tips)
        
    def generate_insights(self):
        """Generate interesting insights for the newsletter."""
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
            "Research shows multilingual AI models consistently outperform monolingual ones, even for English-only tasks.",
            "A new benchmark shows most advanced AI models still struggle with logical reasoning problems that average 12-year-olds can solve.",
            "ChatGPT Plus subscribers reportedly dropped 25% after the recent price increase to $24.99/month.",
            "Universities report 42% of professors have caught students submitting AI-generated essays without disclosure.",
            "Several major animation studios are now using AI to generate initial storyboards, cutting pre-production time by 50%.",
            "A startup claims to have created an AI that can predict stock market movements with 71% accuracy based on social media sentiment.",
            "Top venture capital firms are now using AI to screen initial startup pitches before they reach human investors."
        ]
        
        # Shuffle the list and return it
        random.shuffle(insights)
        return insights
        
    def update_google_doc(self):
        """Update the Google Doc with the formatted newsletter content."""
        log("Updating Google Doc with newsletter content")
        
        try:
            # Format the newsletter content
            formatted_content = self.format_newsletter_content()
            
            # First, check the current document
            try:
                document = self.docs_service.documents().get(documentId=self.doc_id).execute()
                log(f"Retrieved document: '{document.get('title', 'Untitled')}'")
                
                # Get the document length to clear it properly
                doc_length = 1  # Default
                if 'body' in document and 'content' in document['body']:
                    # Get the document length
                    doc_length = document['body']['content'][-1].get('endIndex', 1)
                    log(f"Document length: {doc_length} characters")
                
                # Create requests to update the document
                requests = []
                
                # If document has content, clear it first
                if doc_length > 1:
                    requests.append({
                        'deleteContentRange': {
                            'range': {
                                'startIndex': 1,
                                'endIndex': doc_length
                            }
                        }
                    })
                    
                # Insert the formatted content
                requests.append({
                    'insertText': {
                        'location': {
                            'index': 1
                        },
                        'text': formatted_content
                    }
                })
                
                # Execute the batch update
                result = self.docs_service.documents().batchUpdate(
                    documentId=self.doc_id,
                    body={'requests': requests}
                ).execute()
                
                log("Document updated successfully")
                return True
                
            except Exception as e:
                log(f"Error getting or updating document: {str(e)}", "ERROR")
                traceback.print_exc()
                return False
                
        except Exception as e:
            log(f"Error formatting newsletter content: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
            
    def run(self):
        """Run the complete newsletter generation process."""
        log("Starting AI Newsletter Agent...")
        
        try:
            # Fetch all content
            self.fetch_ai_news()
            self.fetch_ai_tools()
            self.fetch_youtube_video()
            
            # Update Google Doc with formatted content
            success = self.update_google_doc()
            
            if success:
                log("Newsletter corpus updated successfully!")
                return {
                    "status": "success",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "articles_found": len(self.news_items),
                    "tools_found": len(self.ai_tools)
                }
            else:
                log("Failed to update newsletter corpus.", "ERROR")
                return {
                    "status": "error",
                    "timestamp": datetime.datetime.now().isoformat()
                }
        except Exception as e:
            log(f"Error in newsletter generation process: {str(e)}", "ERROR")
            traceback.print_exc()
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }

# Main execution
if __name__ == "__main__":
    agent = AINewsletterAgent()
    result = agent.run()
    print(json.dumps(result))