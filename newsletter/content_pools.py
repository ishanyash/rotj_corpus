"""Dynamic content sources and expanded fallback pools for tools, videos, insights, and prompt tips."""

import html
import random
import datetime
import feedparser

from . import config
from .fetchers import fetch_feed_with_retry, _log, _clean_summary
from .history import was_published, record_published


# ---------------------------------------------------------------------------
# AI Tools
# ---------------------------------------------------------------------------

FALLBACK_TOOLS = [
    {'name': 'Claude', 'link': 'https://claude.ai', 'description': "Anthropic's advanced AI assistant with deep reasoning, coding, and analysis capabilities."},
    {'name': 'ChatGPT', 'link': 'https://chat.openai.com', 'description': "OpenAI's conversational AI with GPT-4 powering search, coding, and creative tasks."},
    {'name': 'Gemini', 'link': 'https://gemini.google.com', 'description': "Google's multimodal AI for text, image, and code generation integrated across Workspace."},
    {'name': 'Midjourney', 'link': 'https://midjourney.com', 'description': 'Industry-leading text-to-image generation with photorealistic quality and artistic control.'},
    {'name': 'Cursor', 'link': 'https://cursor.sh', 'description': 'AI-first code editor with built-in assistant for understanding, editing, and generating code.'},
    {'name': 'Perplexity', 'link': 'https://perplexity.ai', 'description': 'AI-powered search engine that provides sourced answers with real-time web access.'},
    {'name': 'Replit', 'link': 'https://replit.com', 'description': 'Browser-based IDE with AI coding assistant for building and deploying apps instantly.'},
    {'name': 'Runway', 'link': 'https://runwayml.com', 'description': 'Creative AI suite for video generation, image editing, and motion design.'},
    {'name': 'ElevenLabs', 'link': 'https://elevenlabs.io', 'description': 'Realistic AI voice generation and cloning for content creation and accessibility.'},
    {'name': 'Notion AI', 'link': 'https://notion.so', 'description': 'AI writing and organization assistant built into the Notion workspace.'},
    {'name': 'Jasper', 'link': 'https://jasper.ai', 'description': 'AI content platform for marketing teams to generate copy, blogs, and social posts.'},
    {'name': 'Supaboard', 'link': 'https://supaboard.co', 'description': 'Transform complex data into instant dashboards with natural language queries.'},
    {'name': 'Vapi', 'link': 'https://vapi.ai', 'description': 'Build voice AI agents that handle complex calls and integrate with your tools.'},
    {'name': 'Adaptive', 'link': 'https://adaptive.security', 'description': 'Protect against GenAI social engineering attacks with deepfake security simulations.'},
    {'name': 'Mem AI', 'link': 'https://mem.ai', 'description': 'AI-powered second brain that auto-organizes notes and surfaces relevant information.'},
    {'name': 'Stability AI', 'link': 'https://stability.ai', 'description': 'Open-source generative AI for images, video, and 3D content creation.'},
    {'name': 'Hugging Face', 'link': 'https://huggingface.co', 'description': 'The GitHub of machine learning — host, share, and deploy models and datasets.'},
    {'name': 'Vercel v0', 'link': 'https://v0.dev', 'description': 'AI-powered UI generation tool that creates React components from text descriptions.'},
    {'name': 'Suno', 'link': 'https://suno.com', 'description': 'AI music creation platform that generates full songs from text prompts.'},
    {'name': 'Udio', 'link': 'https://udio.com', 'description': 'Create studio-quality music with AI — lyrics, vocals, and instrumentation from text.'},
    {'name': 'Pika', 'link': 'https://pika.art', 'description': 'AI video generation and editing with text-to-video and image-to-video capabilities.'},
    {'name': 'Luma AI', 'link': 'https://lumalabs.ai', 'description': '3D capture and generation with photorealistic neural radiance fields.'},
    {'name': 'Gamma', 'link': 'https://gamma.app', 'description': 'AI-powered presentation and document creation — beautiful slides from a text prompt.'},
    {'name': 'Descript', 'link': 'https://descript.com', 'description': 'AI video and podcast editor — edit media by editing text with overdub voice cloning.'},
    {'name': 'Codeium', 'link': 'https://codeium.com', 'description': 'Free AI code completion and chat assistant supporting 70+ programming languages.'},
    {'name': 'GitHub Copilot', 'link': 'https://github.com/features/copilot', 'description': 'AI pair programmer integrated into VS Code and JetBrains for code suggestions.'},
    {'name': 'Lovable', 'link': 'https://lovable.dev', 'description': 'Build full-stack web apps from natural language descriptions with AI.'},
    {'name': 'Bolt', 'link': 'https://bolt.new', 'description': 'AI-powered full-stack web development in the browser with instant deployment.'},
    {'name': 'Windsurf', 'link': 'https://windsurf.com', 'description': 'AI-powered IDE by Codeium with deep codebase understanding and multi-file editing.'},
    {'name': 'NotebookLM', 'link': 'https://notebooklm.google.com', 'description': "Google's AI research assistant that synthesizes your documents into insights and podcasts."},
]


def fetch_ai_tools(history):
    """Fetch AI tools from Product Hunt RSS, falling back to expanded static pool."""
    _log("Fetching AI tools")
    tools = []

    for feed_url in config.TOOL_FEEDS:
        feed = fetch_feed_with_retry(feed_url)
        if not feed:
            continue
        for entry in feed.entries[:15]:
            title = html.unescape(entry.title) if hasattr(entry, 'title') else ""
            if not title:
                continue
            tool = {
                'name': title,
                'link': entry.link if hasattr(entry, 'link') else "#",
                'description': _clean_summary(getattr(entry, 'summary', '')),
            }
            if not was_published(tool['name'], history):
                tools.append(tool)

    if len(tools) >= 5:
        _log(f"Found {len(tools)} tools from RSS feeds")
        return tools[:5]

    # Fallback: use expanded static pool, filtered by history
    _log("Using fallback tool pool")
    fallback = [t for t in FALLBACK_TOOLS if not was_published(t['name'], history)]
    random.shuffle(fallback)
    tools.extend(fallback)
    return tools[:5]


# ---------------------------------------------------------------------------
# YouTube Videos
# ---------------------------------------------------------------------------

FALLBACK_VIDEOS = [
    {'title': "The Future of AI: 2025 Predictions", 'link': "https://www.youtube.com/watch?v=rQJmDWB9Zwk", 'channel': "Two Minute Papers"},
    {'title': "How Claude Changes Everything", 'link': "https://www.youtube.com/watch?v=E8cfrUV8yiE", 'channel': "AI Explained"},
    {'title': "New Breakthroughs in LLM Research", 'link': "https://www.youtube.com/watch?v=kTPTZ5gsR8g", 'channel': "Yannic Kilcher"},
    {'title': "The AI Revolution in Open Source", 'link': "https://www.youtube.com/watch?v=TqHwwMUZGf4", 'channel': "Lex Fridman"},
    {'title': "AI Tools That Will Blow Your Mind", 'link': "https://www.youtube.com/watch?v=JhCl-GeT4jw", 'channel': "Matt Wolfe"},
    {'title': "The Insane Engineering of AI Data Centers", 'link': "https://www.youtube.com/watch?v=ht6-LmdaEbQ", 'channel': "Real Engineering"},
    {'title': "What Most People Get Wrong About AI", 'link': "https://www.youtube.com/watch?v=5dZ_lvDgevk", 'channel': "Veritasium"},
    {'title': "I Built an AI Agent That Does Everything", 'link': "https://www.youtube.com/watch?v=sal78ACtGTc", 'channel': "Fireship"},
    {'title': "The Rise of AI Agents Explained", 'link': "https://www.youtube.com/watch?v=F8NKVhkZZWI", 'channel': "AI Explained"},
    {'title': "Open Source AI is Winning", 'link': "https://www.youtube.com/watch?v=Rk3nTUfRZmo", 'channel': "Yannic Kilcher"},
    {'title': "How AI is Reshaping Software Engineering", 'link': "https://www.youtube.com/watch?v=1bUy-1hGZpI", 'channel': "Fireship"},
    {'title': "The Truth About AI Replacing Programmers", 'link': "https://www.youtube.com/watch?v=x2_wpMkiJcI", 'channel': "Theo"},
    {'title': "Building Your First AI Agent", 'link': "https://www.youtube.com/watch?v=7E_bHg9hX9c", 'channel': "Matt Wolfe"},
    {'title': "Why Transformers Changed Everything", 'link': "https://www.youtube.com/watch?v=wjZofJX0v4M", 'channel': "3Blue1Brown"},
    {'title': "The Math Behind Neural Networks", 'link': "https://www.youtube.com/watch?v=aircAruvnKk", 'channel': "3Blue1Brown"},
    {'title': "AI Art: Creative Revolution or Theft?", 'link': "https://www.youtube.com/watch?v=tjSxFAGP9Ss", 'channel': "Corridor Crew"},
    {'title': "Running LLMs Locally: Complete Guide", 'link': "https://www.youtube.com/watch?v=J8TgKxomS2g", 'channel': "NetworkChuck"},
    {'title': "AI Music is Getting Scary Good", 'link': "https://www.youtube.com/watch?v=pQ8S4FKcRKo", 'channel': "Rick Beato"},
    {'title': "The AI Chip Wars Explained", 'link': "https://www.youtube.com/watch?v=DcYLT37ImBY", 'channel': "ColdFusion"},
    {'title': "DeepSeek: The Open Source Challenger", 'link': "https://www.youtube.com/watch?v=T5Sgg4M3NK0", 'channel': "AI Explained"},
]


def fetch_youtube_video(history):
    """Fetch latest AI video from YouTube channel RSS feeds."""
    _log("Fetching YouTube recommendation")
    candidates = []

    for feed_url in config.YOUTUBE_CHANNEL_FEEDS:
        feed = fetch_feed_with_retry(feed_url, max_retries=2)
        if not feed:
            continue
        for entry in feed.entries[:3]:
            title = html.unescape(entry.title) if hasattr(entry, 'title') else ""
            if not title:
                continue
            video = {
                'title': title,
                'link': entry.link if hasattr(entry, 'link') else "#",
                'channel': feed.feed.get('title', feed.feed.get('author', 'Unknown')),
            }
            if not was_published(video['title'], history):
                candidates.append(video)

    if candidates:
        video = candidates[0]  # Most recent unwatched
        _log(f"Selected video from RSS: {video['title']}")
        return video

    # Fallback
    _log("Using fallback video pool")
    fallback = [v for v in FALLBACK_VIDEOS if not was_published(v['title'], history)]
    if fallback:
        return random.choice(fallback)

    # All exhausted — return any
    return random.choice(FALLBACK_VIDEOS)


# ---------------------------------------------------------------------------
# Insights from AI Research Blogs
# ---------------------------------------------------------------------------

FALLBACK_INSIGHTS = [
    "AI models consistently make the same logical errors as humans when not prompted to use step-by-step reasoning.",
    "Hospitals using AI for patient screening report a 23% reduction in misdiagnoses compared to traditional triage.",
    "Multilingual AI models consistently outperform monolingual ones, even for English-only tasks.",
    "AI voice cloning can now be achieved with just 3 seconds of audio, down from 30 seconds two years ago.",
    "Professional voice actors are creating deliberately poisoned training data to fight AI cloning.",
    "Fine-tuning LLMs on creative writing produces more diverse outputs than using only academic literature.",
    "The energy cost of training a single large language model has decreased 50% year over year since 2022.",
    "Small language models under 10B parameters can now match GPT-3.5 performance on most benchmarks.",
    "AI-generated code now accounts for over 25% of new code at major tech companies.",
    "Retrieval-augmented generation reduces LLM hallucination rates by up to 70% in knowledge-heavy tasks.",
    "AI weather prediction models now outperform traditional physics-based forecasting for 10-day outlooks.",
    "Open-source AI models have closed the gap with proprietary ones, trailing by less than 5% on most benchmarks.",
    "Chain-of-thought prompting improves math reasoning accuracy by 40-60% across all model sizes.",
    "AI-powered drug discovery has reduced early-stage research timelines from 4 years to under 18 months.",
    "The cost of running inference on large language models dropped 90% between 2023 and 2025.",
    "Synthetic data now trains over 60% of computer vision models deployed in production.",
    "AI coding assistants increase developer productivity by 30-55% depending on task complexity.",
    "Multimodal models that process text, images, and audio together learn representations no single-mode model can.",
    "Constitutional AI training methods reduce harmful outputs by 80% without sacrificing helpfulness.",
    "Edge AI models running on smartphones now perform tasks that required cloud GPUs just two years ago.",
    "AI-based protein structure prediction has accelerated biological research across 190 countries.",
    "Prompt injection attacks remain the #1 security vulnerability in LLM-powered applications.",
    "The average AI startup reaches product-market fit 40% faster than non-AI startups in the same category.",
    "Reinforcement learning from human feedback (RLHF) is being replaced by newer techniques like DPO and RLAIF.",
    "AI image detectors achieve only 60-70% accuracy on the latest generation models, down from 90% two years ago.",
    "Mixture-of-experts architectures use 10x less compute than dense models of equivalent capability.",
    "AI-generated content now makes up an estimated 10% of all new internet text published daily.",
    "Federated learning allows AI training on sensitive medical data without any patient information leaving hospitals.",
    "The transformer architecture, invented in 2017, still dominates AI — no successor has displaced it at scale.",
    "AI models trained with reasoning traces score 2-3x higher on complex math and logic benchmarks.",
]


def fetch_insights(history):
    """Fetch real insights from AI research blog RSS feeds, with fallback."""
    _log("Fetching insights")
    insights = []

    for feed_url in config.INSIGHT_FEEDS:
        feed = fetch_feed_with_retry(feed_url, max_retries=2)
        if not feed:
            continue
        for entry in feed.entries[:5]:
            title = html.unescape(entry.title) if hasattr(entry, 'title') else ""
            if not title:
                continue
            if not was_published(title, history):
                insights.append({
                    'text': title,
                    'source': feed.feed.get('title', 'AI Research'),
                    'link': entry.link if hasattr(entry, 'link') else "#",
                })

    if len(insights) >= 4:
        random.shuffle(insights)
        _log(f"Found {len(insights)} insights from RSS feeds")
        return insights[:4]

    # Supplement with fallback insights
    _log("Supplementing with fallback insights")
    fallback = [
        {'text': i, 'source': 'AI Research', 'link': None}
        for i in FALLBACK_INSIGHTS
        if not was_published(i, history)
    ]
    random.shuffle(fallback)
    insights.extend(fallback)
    return insights[:4]


# ---------------------------------------------------------------------------
# Prompt Tips (expanded static pool with history-based rotation)
# ---------------------------------------------------------------------------

ALL_PROMPT_TIPS = [
    {
        "intro": "Mastering Step-by-Step Reasoning",
        "prompt": "Please analyze [topic/problem] step by step. First outline your approach, then work through each step showing your reasoning. Consider at least 3 different perspectives before reaching your conclusion.",
        "explanation": "Structured prompts activate deeper reasoning, encouraging methodical analysis rather than rushing to conclusions.",
    },
    {
        "intro": "Unleash Creative Writing",
        "prompt": "I need a creative story about [topic]. Before writing, create a character profile with background, motivations, and flaws. Then outline a 3-act structure with conflict and resolution. Now write the story.",
        "explanation": "Forcing the AI to plan before executing results in richer characters and more coherent plots.",
    },
    {
        "intro": "Turn AI into a Coding Tutor",
        "prompt": "Act as a coding mentor teaching me [language/concept]. First explain the core concept in simple terms with an analogy. Then show a basic code example. Finally, give me a simple exercise to try.",
        "explanation": "Perfect for learning programming concepts step-by-step with the right amount of challenge.",
    },
    {
        "intro": "Supercharge Your Research",
        "prompt": "I'm researching [topic]. Identify 3 distinct perspectives. For each: 1) Summarize core arguments, 2) Note strongest evidence, 3) Identify weaknesses, 4) List key scholars/sources.",
        "explanation": "This structured approach ensures more balanced, thorough research summaries.",
    },
    {
        "intro": "AI Fact-Checking Mode",
        "prompt": "Please fact check each claim in the above output. Assume there are mistakes — don't stop until you've checked every fact and found all errors.",
        "explanation": "This prompt makes the AI meticulously comb through each claim, catching errors it would otherwise miss.",
    },
    {
        "intro": "The 'Explain Like I'm Five' Ladder",
        "prompt": "Explain [concept] at 5 different levels: 1) For a 5-year-old, 2) For a high schooler, 3) For a college student, 4) For a professional in the field, 5) For a world expert.",
        "explanation": "This reveals different layers of understanding and helps you find the explanation level that clicks for you.",
    },
    {
        "intro": "The Devil's Advocate Prompt",
        "prompt": "I believe [your position]. Now argue the strongest possible case AGAINST this position. Be thorough, use evidence, and don't hold back. Then summarize the 3 most compelling counterpoints.",
        "explanation": "Forces the AI to steelman the opposing view, which strengthens your own thinking and reveals blind spots.",
    },
    {
        "intro": "Code Review Like a Senior Engineer",
        "prompt": "Review this code as a senior engineer would. Focus on: 1) Bugs and edge cases, 2) Performance issues, 3) Security vulnerabilities, 4) Readability improvements. Be specific with line numbers.",
        "explanation": "Giving the AI a specific persona and checklist produces dramatically more useful code reviews.",
    },
    {
        "intro": "The 'Teach Me by Testing Me' Pattern",
        "prompt": "I want to learn [topic]. Ask me 5 progressively harder questions about it. After each of my answers, tell me what I got right, what I got wrong, and explain the correct answer.",
        "explanation": "Active recall through Q&A is one of the most effective learning techniques, and AI makes it interactive.",
    },
    {
        "intro": "Decision Matrix Generator",
        "prompt": "I need to decide between [option A] and [option B]. Create a weighted decision matrix with 8 relevant criteria. Score each option 1-10 on each criterion. Show the final weighted scores.",
        "explanation": "Transforms fuzzy decisions into structured comparisons with clear winners and tradeoff visibility.",
    },
    {
        "intro": "The 'Before and After' Rewriter",
        "prompt": "Here's my draft: [paste text]. Rewrite it to be: 1) 50% shorter, 2) More engaging, 3) Clearer in structure. Show the original and revised versions side by side with annotations.",
        "explanation": "Side-by-side comparison with annotations teaches you what makes writing stronger.",
    },
    {
        "intro": "Prompt Chaining for Complex Tasks",
        "prompt": "Let's solve this in phases. Phase 1: [gather information]. Phase 2: [analyze patterns]. Phase 3: [generate solution]. Phase 4: [validate and refine]. Complete each phase fully before moving on.",
        "explanation": "Breaking complex tasks into explicit phases prevents the AI from rushing and produces higher-quality output.",
    },
    {
        "intro": "The System Prompt Hack",
        "prompt": "You are an expert [role] with 20 years of experience. Your communication style is [concise/detailed/casual]. You always [specific behavior]. You never [specific anti-behavior].",
        "explanation": "Custom persona definitions dramatically change output quality by anchoring the AI's behavior to specific expertise.",
    },
    {
        "intro": "Socratic Questioning Mode",
        "prompt": "Don't give me the answer directly. Instead, guide me to the answer using the Socratic method. Ask me thought-provoking questions that lead me to discover the solution myself.",
        "explanation": "Turns the AI into a thinking partner rather than an answer machine — great for deeper learning.",
    },
    {
        "intro": "The Output Format Trick",
        "prompt": "Respond in the following format: [SUMMARY] one paragraph overview [KEY POINTS] bulleted list of main takeaways [ACTION ITEMS] numbered list of next steps [QUESTIONS] things I should consider.",
        "explanation": "Specifying the exact output structure ensures you get consistently organized, actionable responses.",
    },
    {
        "intro": "Few-Shot Learning in Prompts",
        "prompt": "Here are 3 examples of what I want: [example 1], [example 2], [example 3]. Now create 5 more in the exact same style, tone, and format.",
        "explanation": "Showing examples is far more effective than describing what you want — the AI pattern-matches beautifully.",
    },
    {
        "intro": "The 'What Am I Missing?' Audit",
        "prompt": "Here's my plan for [project/task]. What am I missing? What could go wrong? What assumptions am I making that might be wrong? Be brutally honest.",
        "explanation": "This is like having a critical friend review your work — catches blind spots you can't see yourself.",
    },
    {
        "intro": "Recursive Summarization",
        "prompt": "Summarize this text in 3 versions: 1) A single tweet (280 chars), 2) A paragraph (100 words), 3) A full summary (300 words). Each should stand alone and capture the key message.",
        "explanation": "Forces the AI to identify what truly matters at each level of detail — useful for communication.",
    },
    {
        "intro": "The Constraint Creativity Boost",
        "prompt": "Solve [problem] but with these constraints: no [obvious solution], must use [specific approach], and the solution must be implementable in [timeframe]. Constraints breed creativity.",
        "explanation": "Adding constraints paradoxically increases creativity by forcing the AI to explore non-obvious solutions.",
    },
    {
        "intro": "Rubber Duck Debugging with AI",
        "prompt": "I'm stuck on a bug. Let me explain what I've tried: [explanation]. Don't solve it yet — first, ask me 5 clarifying questions that might help me realize what I'm missing.",
        "explanation": "Often the act of answering clarifying questions leads you to the solution before the AI even needs to suggest one.",
    },
    {
        "intro": "The Meta-Prompt",
        "prompt": "I want to [goal]. Write me the best possible prompt that I could give to an AI to achieve this goal. Include context, constraints, format, and examples.",
        "explanation": "Using AI to write better prompts for AI creates a powerful feedback loop for prompt engineering.",
    },
    {
        "intro": "Analogical Reasoning",
        "prompt": "Explain [complex concept] using an analogy from [familiar domain]. Then explain where the analogy breaks down and what aspects it doesn't capture.",
        "explanation": "Analogies with explicit limitations teach concepts faster while preventing misconceptions.",
    },
    {
        "intro": "The Iterative Refinement Loop",
        "prompt": "Generate a first draft of [content]. Then critique your own draft listing 5 specific weaknesses. Then rewrite addressing all 5 weaknesses. Show all three versions.",
        "explanation": "Self-critique and revision produces dramatically better output than a single-pass generation.",
    },
    {
        "intro": "Data Storytelling Prompt",
        "prompt": "Here's raw data: [paste data]. Tell a story with this data. What trends emerge? What's surprising? What actionable insights can someone extract? Present it as a narrative, not a report.",
        "explanation": "Transforms dry data into compelling narratives — perfect for presentations and reports.",
    },
    {
        "intro": "The Pre-Mortem Analysis",
        "prompt": "Imagine [project/decision] has failed spectacularly 6 months from now. Write a post-mortem explaining the 5 most likely reasons for failure and what could have been done to prevent each.",
        "explanation": "Pre-mortems identify risks before they materialize — far more effective than optimistic planning alone.",
    },
]


def get_prompt_tip(history):
    """Return a prompt tip that hasn't been shown in the last 90 days."""
    _log("Selecting prompt tip")
    for tip in ALL_PROMPT_TIPS:
        if not was_published(tip['intro'], history):
            return tip

    # All tips exhausted — pick a random one
    return random.choice(ALL_PROMPT_TIPS)


# ---------------------------------------------------------------------------
# "Why It Matters" Commentary Generator
# ---------------------------------------------------------------------------

def generate_why_it_matters(title, summary="", source=""):
    """Generate contextual 'Why it matters' commentary based on article content."""
    text = (title + " " + summary + " " + source).lower()

    if any(w in text for w in ['funding', 'raises', 'valuation', 'investment', 'series', 'billion', 'million']):
        templates = [
            "This funding signals growing investor confidence in this AI segment, which could accelerate product development and competition.",
            "Major investment rounds like this reshape the competitive landscape, often leading to faster releases across the industry.",
            "Capital flows reveal where the smart money sees AI's next big opportunities — and this bet is telling.",
        ]
    elif any(w in text for w in ['open source', 'open-source', 'release', 'launches', 'free', 'available']):
        templates = [
            "Open releases democratize access to advanced AI, enabling smaller teams and indie developers to build on cutting-edge tech.",
            "When major players release tools freely, it lowers barriers to entry and sparks community-driven innovation.",
            "Accessibility moves like this accelerate the entire ecosystem — what was enterprise-only yesterday becomes everyone's tool tomorrow.",
        ]
    elif any(w in text for w in ['safety', 'regulation', 'policy', 'government', 'law', 'ban', 'rules', 'compliance']):
        templates = [
            "As AI governance frameworks take shape, early regulatory decisions set precedents that define what's permissible for years.",
            "Policy developments directly affect which AI tools reach consumers and how companies deploy models at scale.",
            "The regulatory landscape is the invisible hand shaping AI's future — these decisions matter more than most technical breakthroughs.",
        ]
    elif any(w in text for w in ['research', 'paper', 'study', 'breakthrough', 'discover', 'benchmark', 'state-of-the-art']):
        templates = [
            "Research breakthroughs like this typically take 12-18 months to reach products, but they define the next generation of AI tools.",
            "Fundamental research shapes the capabilities that eventually appear in the tools millions of people use daily.",
            "Today's research paper is tomorrow's product feature — keeping an eye on the cutting edge reveals where AI is heading.",
        ]
    elif any(w in text for w in ['partner', 'integrat', 'collaborat', 'acqui', 'merger', 'deal']):
        templates = [
            "Strategic partnerships reshape the ecosystem, determining which AI capabilities become mainstream and accessible.",
            "Integration moves signal a maturing market where reach and interoperability matter as much as raw model performance.",
            "These alliances redraw the competitive map — what matters isn't just who has the best model, but who has the best distribution.",
        ]
    else:
        templates = [
            "This reflects AI's rapid evolution, where each week brings shifts that would have seemed impossible a year ago.",
            "For professionals and enthusiasts alike, developments like this are crucial for understanding where the industry is heading.",
            "AI is moving from research labs into everyday workflows at unprecedented speed — this is another proof point.",
            "The pace of change in AI means today's headline becomes tomorrow's baseline. Staying informed is a competitive advantage.",
        ]

    return random.choice(templates)
