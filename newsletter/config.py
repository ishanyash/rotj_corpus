"""Configuration constants for the newsletter agent."""

import random

# RSS feed URLs for news
NEWS_FEEDS = [
    'https://news.google.com/rss/search?q=artificial+intelligence+when:1d&hl=en-US&gl=US&ceid=US:en',
    'https://news.google.com/rss/search?q=machine+learning+when:1d&hl=en-US&gl=US&ceid=US:en',
    'https://news.google.com/rss/search?q=openai+when:1d&hl=en-US&gl=US&ceid=US:en',
    'https://news.google.com/rss/search?q=anthropic+claude+when:1d&hl=en-US&gl=US&ceid=US:en',
    'https://news.google.com/rss/search?q=generative+ai+when:1d&hl=en-US&gl=US&ceid=US:en',
]

# Product Hunt AI category RSS for dynamic tools
TOOL_FEEDS = [
    'https://www.producthunt.com/feed?category=artificial-intelligence',
]

# YouTube channel RSS feeds for video picks (free, no API key needed)
YOUTUBE_CHANNEL_FEEDS = [
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg',  # Two Minute Papers
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCUyeluBRhGPCW4acMjc9U8w',  # AI Explained
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCZHmQk67mSJgfCCTn7xBfew',  # Yannic Kilcher
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCSHZKyawb77ixDdsGog4iWA',  # Lex Fridman
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCWN3xxRkmTPphYpZKE1hdWg',  # Matt Wolfe
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCLXo7UDZvByw2ixzpQCufnA',  # Fireship
    'https://www.youtube.com/feeds/videos.xml?channel_id=UCsBjURrPoezykLs9EqgamOA',  # Fireship (alt)
]

# RSS feeds for insights from AI research blogs
INSIGHT_FEEDS = [
    'https://blog.google/technology/ai/rss/',
    'https://openai.com/blog/rss/',
    'https://news.mit.edu/rss/topic/artificial-intelligence2',
    'https://techcrunch.com/category/artificial-intelligence/feed/',
]

# AI relevance filter terms
AI_TERMS = [
    'artificial intelligence', 'machine learning', 'openai', 'anthropic',
    'claude', 'chatgpt', 'gpt-4', 'gpt-5', 'llm', 'deep learning',
    'neural network', 'generative ai', 'large language model', 'midjourney',
    'stable diffusion', 'gemini', 'copilot ai', 'transformer model',
    'deepseek', 'mistral', 'llama', 'diffusion model', 'text-to-image',
    'text-to-video', 'ai agent', 'ai model',
]

# Minimum content thresholds
MIN_NEWS_ITEMS = 3
MIN_TOOLS = 3
MIN_INSIGHTS = 2

# Content history settings
HISTORY_MAX_DAYS = 90

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

# Emoji maps for section headers
EMOJIS = {
    "headline": ["🤖", "🚀", "🔥", "✨", "💡", "🌟", "🎮", "💻", "🧠", "🔮", "👁️", "🌐", "📱", "🤯"],
    "tools": ["🧰", "🔧", "🛠️", "⚙️", "🔨", "🔍", "🔎", "🎯", "🎨", "✏️", "🔌", "💾", "📂", "📋"],
    "news": ["🌀", "📰", "🗞️", "📢", "📣", "📡", "📻", "📺", "📝", "📌", "📍", "🔔", "🔊", "🗣️"],
    "video": ["🎧", "🎬", "📹", "🎥", "📽️", "🎞️", "📺", "🎙️", "🎤", "📀", "💿", "📡", "📺", "🎦"],
    "insights": ["🧠", "💭", "🔍", "💡", "⚡", "🔎", "🧐", "🤔", "👀", "📊", "📈", "📉", "📗", "👁️"],
    "welcome": ["👋", "✌️", "🙌", "👏", "👐", "🤝", "🖐️", "🤟", "👍", "🎯", "🎆", "🌈", "🌞", "🌠"],
    "prompt": ["💬", "🗯️", "💭", "💡", "✏️", "📝", "⌨️", "🖋️", "📋", "🤔", "👨‍💻", "📊", "🧮", "🧩"],
}


def random_emoji(category):
    """Get a random emoji for a given category."""
    return random.choice(EMOJIS.get(category, ["🤖"]))
