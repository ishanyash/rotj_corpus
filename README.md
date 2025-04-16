# Return of the Jed(AI) Newsletter Agent

An automated agent that gathers the latest AI news and updates a Google Doc daily with the "Return of the Jed(AI)" newsletter.

## Features

- 🔍 Scrapes latest AI news from Google News RSS feeds
- 🛠️ Features trending AI tools 
- 🎬 Includes AI-related YouTube video recommendations
- 📝 Formats content according to a pop-culture inspired newsletter template
- 📄 Updates a Google Doc automatically via the Google Docs API
- ⏱️ Runs daily via GitHub Actions (completely free)

## How It Works

1. **Content Collection**: The agent gathers content from free sources including Google News RSS feeds.
2. **Content Processing**: It formats news articles, AI tools, and insights into a consistent, engaging style.
3. **Document Update**: The formatted newsletter content is written to your Google Doc.
4. **Automation**: Everything runs on a schedule via GitHub Actions, with no server costs.

## Setup Instructions

### Step 1: Set Up Google Cloud

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Google Docs API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Docs API"
   - Click "Enable"
4. Create a Service Account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Give it a name like "newsletter-agent"
   - Click "Create and Continue"
   - Skip role assignment (we'll grant access directly to the document)
   - Click "Done"
5. Create a JSON key for this service account:
   - Click on the service account you just created
   - Go to the "Keys" tab
   - Click "Add Key" > "Create new key"
   - Select "JSON" format
   - Click "Create" to download the key file

### Step 2: Prepare Your Google Doc

1. Create a new Google Doc
2. Note the Document ID from the URL:
   - For example, in `https://docs.google.com/document/d/abc123xyz/edit`
   - The Document ID is `abc123xyz`
3. Share the document with your service account:
   - Click the "Share" button
   - Enter the email address of your service account (found in the JSON key)
   - Make sure to give it "Editor" permissions
   - Uncheck "Notify people" (optional)
   - Click "Share"

### Step 3: Set Up GitHub Repository

1. Create a new repository with these files
2. Add the following secrets in your repository settings:
   - `GOOGLE_CREDENTIALS`: The entire contents of your service account JSON key file
   - `DOCUMENT_ID`: The ID of your Google Doc

To add secrets:
- Go to your repository on GitHub
- Click "Settings" > "Secrets and variables" > "Actions"
- Click "New repository secret"
- Add each secret with its name and value

### Step 4: Configure and Deploy

1. Update any settings in `updated_newsletter_agent.py` if desired
2. The GitHub Actions workflow will run automatically at the scheduled time (7 AM UTC by default)
3. You can also trigger it manually via the Actions tab

## Troubleshooting

### Authentication Issues

If you're getting authentication errors, make sure:

1. Your service account JSON key is correctly copied into the `GOOGLE_CREDENTIALS` secret
2. The Google Docs API is enabled in your Google Cloud project
3. You've shared the document with the service account email
4. The document ID is correct

Run the debugging script to check authentication:

```bash
export GOOGLE_CREDENTIALS='{"type":"service_account",...}'  # Your service account JSON
export DOCUMENT_ID='your-doc-id'
python debug_auth.py
```

### GitHub Actions Not Running

If the GitHub Actions workflow isn't running:

1. Make sure it's enabled in the "Actions" tab
2. Check that the YAML file is valid
3. Try triggering the workflow manually

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

# Run the debugging script first
python debug_auth.py

# Run the agent
python updated_newsletter_agent.py
```

## Customization

You can customize the agent by:

- Modifying the `format_newsletter()` method for a different newsletter layout
- Adding or changing the news sources in `fetch_ai_news()`
- Updating the AI tools in `fetch_ai_tools()`
- Adding more YouTube channels in `add_youtube_recommendation()`
- Changing the schedule in the GitHub Actions workflow file

## License

MIT License - Feel free to modify and use as needed.

## Support

If you encounter any issues, please open an issue in this repository.