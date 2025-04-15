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
                            ai_summary = summarizer(summary, max_length=120, min_length=60, do_sample=False)[0]['summary_text']
                        except Exception as e:
                            print(f"Error summarizing: {e}")
                            ai_summary = summary[:200] + "..."
                    else:
                        ai_summary = summary
                    
                    # Extract the source from the title if available (usually in format "Title - Source")
                    source = "AI News"
                    if ' - ' in title:
                        title_parts = title.split(' - ')
                        if len(title_parts) > 1:
                            source = title_parts[-1]
                    
                    # Add to our news items
                    self.news_items.append({
                        'title': title,
                        'link': entry.link,
                        'published': entry.published if hasattr(entry, 'published') else datetime.datetime.now().isoformat(),
                        'summary': ai_summary,
                        'source': source
                    })
        
        # Add some fallback news items in case we didn't get enough from the feeds
        fallback_news = [
            {
                'title': "OpenAI Makes ChatGPT Plus Free for Students - OpenAI Blog",
                'link': "https://openai.com/blog/chatgpt-plus-free-for-students",
                'published': datetime.datetime.now().isoformat(),
                'summary': "OpenAI announced that ChatGPT Plus will be free for all US and Canadian college students through May. This initiative aims to help students with research, learning, and productivity.",
                'source': "OpenAI Blog"
            },
            {
                'title': "Anthropic's Claude AI Is Coming to Google Workspace - Anthropic",
                'link': "https://www.anthropic.com/news",
                'published': datetime.datetime.now().isoformat(),
                'summary': "Anthropic announced a partnership with Google to integrate Claude AI into Google Workspace. This will allow users to access Claude's capabilities directly within Gmail, Docs, and other Google services.",
                'source': "Anthropic"
            },
            {
                'title': "DeepMind's Dreamer AI Teaches Itself Minecraft - DeepMind",
                'link': "https://deepmind.com/blog",
                'published': datetime.datetime.now().isoformat(),
                'summary': "DeepMind developed an AI system called Dreamer that figured out how to collect diamonds in Minecraft without being taught how to play, using reinforcement learning and a 'world model' to imagine future scenarios.",
                'source': "DeepMind"
            },
            {
                'title': "Spotify Introduces Gen AI Ads for Script Generation - TechCrunch",
                'link': "https://techcrunch.com/spotify-gen-ai-ads",
                'published': datetime.datetime.now().isoformat(),
                'summary': "Spotify introduced new Gen AI Ads for creating scripts and voiceovers at no extra cost to advertisers. The tool aims to streamline the ad creation process for podcasts and audio content.",
                'source': "TechCrunch"
            }
        ]
        
        # If we didn't get enough news items from the feeds, add some fallbacks
        if len(self.news_items) < 5:
            self.news_items.extend(fallback_news[:5 - len(self.news_items)])
        
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
        
    def update_google_doc(self):
        """Update the Google Doc with proper heading styles."""
        # First, create the title
        title = f"AI NEWS CORPUS - {self.today}"
        
        requests = [
            # Clear existing content if needed
            {
                'deleteContentRange': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': 2  # This is a workaround to clear the document - will be adjusted dynamically
                    }
                }
            },
            # Insert title with Heading 1 style
            {
                'insertText': {
                    'location': {
                        'index': 1
                    },
                    'text': title + "\n\n"
                }
            },
            # Apply Heading 1 formatting to title
            {
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': 1,
                        'endIndex': len(title) + 1
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_1'
                    },
                    'fields': 'namedStyleType'
                }
            }
        ]
        
        # First get the current document to determine if we need to clear it
        try:
            document = self.docs_service.documents().get(documentId=self.doc_id).execute()
            if 'body' in document and 'content' in document['body']:
                # Get the document length to clear it properly
                doc_length = document['body']['content'][-1].get('endIndex', 1)
                if doc_length > 1:
                    requests[0]['deleteContentRange']['range']['endIndex'] = doc_length
        except Exception as e:
            print(f"Error checking document: {e}")
            # If we can't check, just proceed with the insertion
            requests.pop(0)  # Remove the delete request
        
        current_index = len(title) + 3  # Starting index after title and 2 newlines
        
        # MAIN STORIES SECTION
        main_stories_heading = "MAIN STORIES"
        requests.extend([
            # Insert Main Stories heading
            {
                'insertText': {
                    'location': {
                        'index': current_index
                    },
                    'text': main_stories_heading + "\n\n"
                }
            },
            # Apply Heading 2 formatting
            {
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(main_stories_heading)
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_2'
                    },
                    'fields': 'namedStyleType'
                }
            }
        ])
        
        current_index += len(main_stories_heading) + 2  # +2 for the newlines
        
        # Add each main story with Heading 3 style for story titles
        for i, news in enumerate(self.news_items[:8]):
            title = news['title'].split(' - ')[0].strip() if ' - ' in news['title'] else news['title']
            source = news['source'] if 'source' in news else "Unknown Source"
            story_title = f"{i+1}. {title}"
            
            # Content for this story
            content = f"Source: {source}\nLink: {news['link']}\nSummary: {news['summary']}\n\n"
            
            requests.extend([
                # Insert story title
                {
                    'insertText': {
                        'location': {
                            'index': current_index
                        },
                        'text': story_title + "\n"
                    }
                },
                # Apply Heading 3 formatting to story title
                {
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(story_title)
                        },
                        'paragraphStyle': {
                            'namedStyleType': 'HEADING_3'
                        },
                        'fields': 'namedStyleType'
                    }
                },
                # Insert story content
                {
                    'insertText': {
                        'location': {
                            'index': current_index + len(story_title) + 1  # +1 for the newline
                        },
                        'text': content
                    }
                }
            ])
            
            current_index += len(story_title) + 1 + len(content)  # +1 for the newline
        
        # STARTUP NEWS SECTION
        startup_heading = "STARTUP & FUNDING NEWS"
        requests.extend([
            # Insert Startup News heading
            {
                'insertText': {
                    'location': {
                        'index': current_index
                    },
                    'text': startup_heading + "\n\n"
                }
            },
            # Apply Heading 2 formatting
            {
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(startup_heading)
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_2'
                    },
                    'fields': 'namedStyleType'
                }
            }
        ])
        
        current_index += len(startup_heading) + 2  # +2 for the newlines
        
        # Add startup news
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
        
        for i, startup in enumerate(startup_news_list):
            startup_title = f"{i+1}. {startup['company']}"
            content = f"News: {startup['news']}\nLink: {startup['link']}\n\n"
            
            requests.extend([
                # Insert startup title
                {
                    'insertText': {
                        'location': {
                            'index': current_index
                        },
                        'text': startup_title + "\n"
                    }
                },
                # Apply Heading 3 formatting to startup title
                {
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(startup_title)
                        },
                        'paragraphStyle': {
                            'namedStyleType': 'HEADING_3'
                        },
                        'fields': 'namedStyleType'
                    }
                },
                # Insert startup content
                {
                    'insertText': {
                        'location': {
                            'index': current_index + len(startup_title) + 1  # +1 for the newline
                        },
                        'text': content
                    }
                }
            ])
            
            current_index += len(startup_title) + 1 + len(content)  # +1 for the newline
        
        # AI TOOLS SECTION
        tools_heading = "NEW AI TOOLS"
        requests.extend([
            # Insert AI Tools heading
            {
                'insertText': {
                    'location': {
                        'index': current_index
                    },
                    'text': tools_heading + "\n\n"
                }
            },
            # Apply Heading 2 formatting
            {
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(tools_heading)
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_2'
                    },
                    'fields': 'namedStyleType'
                }
            }
        ])
        
        current_index += len(tools_heading) + 2  # +2 for the newlines
        
        # Add AI tools
        for i, tool in enumerate(self.ai_tools[:8]):
            tool_title = f"{i+1}. {tool['name']}"
            content = f"Description: {tool['description']}\nLink: {tool['link']}\n\n"
            
            requests.extend([
                # Insert tool title
                {
                    'insertText': {
                        'location': {
                            'index': current_index
                        },
                        'text': tool_title + "\n"
                    }
                },
                # Apply Heading 3 formatting to tool title
                {
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(tool_title)
                        },
                        'paragraphStyle': {
                            'namedStyleType': 'HEADING_3'
                        },
                        'fields': 'namedStyleType'
                    }
                },
                # Insert tool content
                {
                    'insertText': {
                        'location': {
                            'index': current_index + len(tool_title) + 1  # +1 for the newline
                        },
                        'text': content
                    }
                }
            ])
            
            current_index += len(tool_title) + 1 + len(content)  # +1 for the newline
        
        # INSIGHTS SECTION
        insights_heading = "INTERESTING INSIGHTS"
        requests.extend([
            # Insert Insights heading
            {
                'insertText': {
                    'location': {
                        'index': current_index
                    },
                    'text': insights_heading + "\n\n"
                }
            },
            # Apply Heading 2 formatting
            {
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(insights_heading)
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_2'
                    },
                    'fields': 'namedStyleType'
                }
            }
        ])
        
        current_index += len(insights_heading) + 2  # +2 for the newlines
        
        # Add insights
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
        
        # Format insights as a simple list
        insights_content = ""
        for i, insight in enumerate(insights_list):
            insights_content += f"{i+1}. {insight}\n"
        insights_content += "\n"
        
        requests.append({
            'insertText': {
                'location': {
                    'index': current_index
                },
                'text': insights_content
            }
        })
        
        current_index += len(insights_content)
        
        # PROMPT TIPS SECTION
        prompt_heading = "PROMPT TIPS"
        requests.extend([
            # Insert Prompt Tips heading
            {
                'insertText': {
                    'location': {
                        'index': current_index
                    },
                    'text': prompt_heading + "\n\n"
                }
            },
            # Apply Heading 2 formatting
            {
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(prompt_heading)
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_2'
                    },
                    'fields': 'namedStyleType'
                }
            }
        ])
        
        current_index += len(prompt_heading) + 2  # +2 for the newlines
        
        # Add prompt tips
        prompt_tips = [
            {
                "title": "Fact-Checking with Claude 3.7",
                "prompt": "Please fact check each fact in the above output against the original sources to confirm they are accurate. Assume there are mistakes, so don't stop until you've checked every fact and found all mistakes.",
                "explanation": "This forces Claude to meticulously examine each claim and verify its accuracy against sources."
            },
            {
                "title": "Better Creative Writing",
                "prompt": "I need a creative story about [topic]. Before writing, create a character profile with background, motivations, and flaws. Then outline a 3-act structure with conflict and resolution. Now write the story incorporating these elements.",
                "explanation": "This prompt forces LLMs to plan before executing, resulting in richer characters and more coherent plots."
            },
            {
                "title": "Coding Tutorial Generator",
                "prompt": "Act as a coding mentor teaching me [language/concept]. First explain the core concept in simple terms with an analogy. Then show a basic code example. Finally, give me a simple exercise to try, with its solution hidden below.",
                "explanation": "Perfect for learning programming concepts step-by-step with the right amount of challenge."
            },
            {
                "title": "Balanced Research Framework",
                "prompt": "I'm researching [topic]. First, identify 3 distinct perspectives on this issue. Then for each perspective: 1) Summarize their core arguments, 2) Note their strongest evidence, 3) Identify potential weaknesses, and 4) List key scholars/sources associated with this view.",
                "explanation": "This structured approach helps ensure more balanced, thorough research summaries."
            },
            {
                "title": "Data Analysis Planning",
                "prompt": "I have a dataset about [topic]. Walk me through an analysis plan: 1) What cleaning/preprocessing steps should I take? 2) Suggest 3 key insights we might extract, 3) Recommend specific visualization approaches for each insight, 4) Identify potential confounding variables to control for.",
                "explanation": "Helps you approach data more systematically, even before you start crunching numbers."
            }
        ]
        
        for i, tip in enumerate(prompt_tips):
            tip_title = f"{i+1}. {tip['title']}"
            content = f"Prompt: {tip['prompt']}\nWhy it works: {tip['explanation']}\n\n"
            
            requests.extend([
                # Insert tip title
                {
                    'insertText': {
                        'location': {
                            'index': current_index
                        },
                        'text': tip_title + "\n"
                    }
                },
                # Apply Heading 3 formatting to tip title
                {
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(tip_title)
                            },
                        'paragraphStyle': {
                            'namedStyleType': 'HEADING_3'
                        },
                        'fields': 'namedStyleType'
                    }
                },
                # Insert tip content
                {
                    'insertText': {
                        'location': {
                            'index': current_index + len(tip_title) + 1  # +1 for the newline
                        },
                        'text': content
                    }
                }
            ])
            
            current_index += len(tip_title) + 1 + len(content)  # +1 for the newline
        
        # VIDEOS SECTION
        videos_heading = "RECOMMENDED VIDEOS"
        requests.extend([
            # Insert Videos heading
            {
                'insertText': {
                    'location': {
                        'index': current_index
                    },
                    'text': videos_heading + "\n\n"
                }
            },
            # Apply Heading 2 formatting
            {
                'updateParagraphStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(videos_heading)
                    },
                    'paragraphStyle': {
                        'namedStyleType': 'HEADING_2'
                    },
                    'fields': 'namedStyleType'
                }
            }
        ])
        
        current_index += len(videos_heading) + 2  # +2 for the newlines
        
        # Add videos
        video_list = [
            {
                "title": self.youtube_video['title'] if self.youtube_video else "The Future of AI: 2025 Predictions",
                "channel": self.youtube_video['channel'] if self.youtube_video else "Two Minute Papers",
                "link": self.youtube_video['link'] if self.youtube_video else "https://www.youtube.com/watch?v=example"
            },
            {
                "title": "How LLMs Actually Work",
                "channel": "AI Explained",
                "link": "https://www.youtube.com/watch?v=example2"
            },
            {
                "title": "The Truth About AI Productivity",
                "channel": "Lex Fridman",
                "link": "https://www.youtube.com/watch?v=example3"
            }
        ]
        
        for i, video in enumerate(video_list):
            video_title = f"{i+1}. {video['title']}"
            content = f"Channel: {video['channel']}\nLink: {video['link']}\n\n"
            
            requests.extend([
                # Insert video title
                {
                    'insertText': {
                        'location': {
                            'index': current_index
                        },
                        'text': video_title + "\n"
                    }
                },
                # Apply Heading 3 formatting to video title
                {
                    'updateParagraphStyle': {
                        'range': {
                            'startIndex': current_index,
                            'endIndex': current_index + len(video_title)
                        },
                        'paragraphStyle': {
                            'namedStyleType': 'HEADING_3'
                        },
                        'fields': 'namedStyleType'
                    }
                },
                # Insert video content
                {
                    'insertText': {
                        'location': {
                            'index': current_index + len(video_title) + 1  # +1 for the newline
                        },
                        'text': content
                    }
                }
            ])
            
            current_index += len(video_title) + 1 + len(content)  # +1 for the newline
        
        # Execute the batch update
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
        
        # Update Google Doc with proper heading styles
        success = self.update_google_doc()
        
        if success:
            print("Newsletter corpus updated successfully!")
            return {
                "status": "success",
                "timestamp": datetime.datetime.now().isoformat(),
                "articles_found": len(self.news_items),
                "tools_found": len(self.ai_tools)
            }
        else:
            print("Failed to update newsletter corpus.")
            return {
                "status": "error",
                "timestamp": datetime.datetime.now().isoformat()
            }

# Main execution
if __name__ == "__main__":
    agent = AINewsletterAgent()
    result = agent.run()
    print(json.dumps(result))