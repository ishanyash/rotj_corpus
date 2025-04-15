# Return of the Jed(AI) Newsletter Agent

An automated agent that gathers the latest AI news and updates a Google Doc daily for the "Return of the Jed(AI)" newsletter.

## Features

- Scrapes latest AI news from Google News RSS feeds
- Finds trending AI tools from Product Hunt
- Discovers AI-related YouTube videos
- Formats content according to the newsletter template
- Updates a Google Doc automatically via the Google Docs API
- Runs daily via GitHub Actions

## Setup Instructions

### Prerequisites

1. A Google Cloud account
2. A Google Doc to serve as your newsletter corpus
3. A GitHub repository to host this code

### Step 1: Set Up Google Cloud

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Docs API
4. Create a Service Account with the following permissions:
   - `https://www.googleapis.com/auth/documents`
5. Create and download a JSON key for this service account

### Step 2: Prepare Your Google Doc

1. Create a new Google Doc
2. Share it with the email address of your service account (with Editor permissions)
3. Note the Document ID from the URL (the long string between `/d/` and `/edit`)

### Step 3: Set Up GitHub Repository

1. Create a new repository or clone this one
2. Add the following secrets in your repository settings:
   - `GOOGLE_CREDENTIALS`: The entire contents of your service account JSON key
   - `DOCUMENT_ID`: The ID of your Google Doc

### Step 4: Configure and Deploy

1. Customize the `newsletter_agent.py` file if needed
2. Push the code to your repository
3. The GitHub Actions workflow will run automatically at the scheduled time
4. You can also trigger it manually via the Actions tab

## Local Testing

To test the agent locally:

```bash
# Clone the repository
git clone <your-repo-url>
cd <repo-folder>

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_CREDENTIALS='{"type":"service_account",...}'  # Your service account JSON
export DOCUMENT_ID='your-doc-id'

# Run the agent
python newsletter_agent.py
```

## Customization

You can customize the agent by:

- Modifying the RSS feeds in `fetch_ai_news()`
- Changing the newsletter template in `format_newsletter_content()`
- Adding more sources for AI tools and videos
- Adjusting the schedule in the GitHub Actions workflow file

## Free Tier Limitations

This implementation uses free APIs and services, with some limitations:

- Google News RSS has rate limits
- The summarization model is lightweight
- YouTube video discovery is basic without the YouTube API
- Product Hunt parsing is simplified

For a more robust solution, consider upgrading to use paid APIs or services.