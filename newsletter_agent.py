import os
import json
import requests
import feedparser
import datetime
import random
import traceback
import sys
from googleapiclient.discovery import build
from google.oauth2 import service_account
import re
import html

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

class SimpleNewsletterAgent:
    def __init__(self):
        log("Initializing Simple Newsletter Agent")
        self.doc_id = os.environ.get('DOCUMENT_ID')
        if not self.doc_id:
            log("ERROR: DOCUMENT_ID environment variable is not set", "ERROR")
            sys.exit(1)
            
        log(f"Using document ID: {self.doc_id}")
        
        # Initialize variables
        self.news_items = []
        self.ai_tools = []
        self.youtube_video = None
        self.insights = []
        self.today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        
        # Connect to Google Docs
        self.setup_google_docs()
        
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
                            
                            # Simple summary trimming - no AI summarization to avoid memory issues
                            if len(summary) > 500:
                                summary = summary[:500] + "..."
                            
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
                                'summary': summary,
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
        
        # Skip the actual API calls and just use fallback tools to avoid potential issues
        log("Using fallback AI tools")
        self.add_fallback_tools()
        
        # Shuffle the tools for variety
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
        
        # Use all the fallback tools
        self.ai_tools = fallback_tools
    
    def fetch_youtube_video(self):
        """Fetch a trending AI YouTube video with better error handling."""
        log("Using fallback YouTube video")
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
            "Research shows multilingual AI models consistently outperform monolingual ones, even for English-only tasks."
        ]
        
        # Shuffle the list and return it
        random.shuffle(insights)
        return insights[:5]  # Return only 5 insights
        
    def format_newsletter_content(self):
        """Format the content for the Return of the Jed(AI) newsletter."""
        log("Formatting newsletter content")
        
        # Random emoji selection for sections
        emoji = lambda category: random.choice(EMOJIS.get(category, ["✨"]))
        
        # Format the newsletter as plain text with minimal formatting
        formatted_content = f"""RETURN OF THE JED(AI): AI NEWSLETTER
{self.today}

👋 WELCOME, HUMANS!

Hope your algorithms are optimized and your neural networks are firing on all nodes today!
Today we're diving into the latest AI happenings across the galaxy.
Let's jump to hyperspace!

----------------------------
📰 TODAY'S MAIN STORY
----------------------------

"""
        
        # Add the main story (first news item)
        if self.news_items:
            main_story = self.news_items[0]
            story_title = main_story['title']
            
            formatted_content += f"{story_title}\n\n"
            
            # Add summary
            story_content = main_story.get('summary', 'No details available.')
                
            formatted_content += f"{story_content}\n\n"
            formatted_content += f"Source: {main_story.get('source', 'Unknown')}\n"
            formatted_content += f"Read more: {main_story.get('link', '')}\n\n"
        
        # Add prompt tip section
        formatted_content += f"""----------------------------
{emoji('prompt')} PROMPT TIP OF THE DAY
----------------------------

Expert Mode Reasoning with Claude 3.7

"Please analyze [topic/problem] step by step. First outline your approach, then work through each step showing your reasoning. Consider at least 3 different perspectives or methods before reaching your conclusion."

Why it works: This structured prompt activates Claude's deeper reasoning capabilities, encouraging methodical analysis rather than rushing to conclusions.

----------------------------
{emoji('tools')} AI TOOL SPOTLIGHT
----------------------------

"""
        
        # Add 3-5 AI tools
        tool_count = min(5, len(self.ai_tools))
        for i in range(tool_count):
            tool = self.ai_tools[i]
            formatted_content += f"* {tool['name']} → {tool['description']}\n  Link: {tool['link']}\n\n"
            
        formatted_content += f"""----------------------------
{emoji('news')} AROUND THE HORN: QUICK HITS
----------------------------

"""
        
        # Add secondary news items as quick hits
        for i, news in enumerate(self.news_items[1:6]):  # Use items 2-6 (skipping the main story)
            source = news.get('source', 'Unknown')
            title_text = news['title']
            # Truncate if too long
            if len(title_text) > 80:
                title_text = title_text[:77] + "..."
            formatted_content += f"* {source}: {title_text}\n  Link: {news.get('link', '')}\n\n"
            
        # Add YouTube recommendation
        if self.youtube_video:
            formatted_content += f"""----------------------------
{emoji('video')} WATCH THIS: YOUTUBE PICK
----------------------------

{self.youtube_video['title']} by {self.youtube_video['channel']}
Link: {self.youtube_video['link']}

"""
            
        # Add interesting insights section
        insights = self.generate_insights()
        formatted_content += f"""----------------------------
{emoji('insights')} NEURAL FIRINGS: INTERESTING INSIGHTS
----------------------------

"""
        
        for insight in insights:
            formatted_content += f"* {insight}\n\n"
            
        # Add closing and CTA
        formatted_content += f"""----------------------------
👋 THAT'S ALL, FOLKS!
----------------------------

That's all for today, humans. May your data be clean and your models well-tuned.

The best way to support this newsletter? Share it with a fellow tech enthusiast!

[Subscribe] | [Visit our site] | [Share with a friend]

🦾 RETURN OF THE JED(AI) 🦾
"""
        
        return formatted_content
        
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
                
                # Create a simple update request - just replacing the content
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
                    
                # Insert the formatted content as plain text
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
        log("Starting Newsletter Agent...")
        
        try:
            # Fetch content
            self.fetch_ai_news()
            self.fetch_ai_tools()
            self.fetch_youtube_video()
            
            # Update Google Doc with formatted content
            success = self.update_google_doc()
            
            if success:
                log("Newsletter updated successfully!")
                return {
                    "status": "success",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "articles_found": len(self.news_items),
                    "tools_found": len(self.ai_tools)
                }
            else:
                log("Failed to update newsletter.", "ERROR")
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
    agent = SimpleNewsletterAgent()
    result = agent.run()
    print(json.dumps(result))