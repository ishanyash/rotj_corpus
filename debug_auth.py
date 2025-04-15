#!/usr/bin/env python3
"""
Google Docs API Authentication Debugger

This script helps diagnose issues with Google Docs API authentication
by testing your service account credentials and document access.

Usage:
  python debug_auth.py

Environment variables:
  GOOGLE_CREDENTIALS - The service account JSON credentials (required)
  DOCUMENT_ID - The Google Doc ID to test access (required)
"""

import os
import json
import sys
import traceback
from googleapiclient.discovery import build
from google.oauth2 import service_account

def main():
    print("\n----- Google Docs API Authentication Debugger -----\n")
    
    # Check environment variables
    doc_id = os.environ.get('DOCUMENT_ID')
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    
    if not doc_id:
        print("❌ ERROR: DOCUMENT_ID environment variable is not set.")
        print("   Set this to the ID of your Google Doc (the long string in the URL).\n")
        return False
        
    if not creds_json:
        print("❌ ERROR: GOOGLE_CREDENTIALS environment variable is not set.")
        print("   This should contain the full JSON of your service account key.\n")
        return False
        
    print(f"✓ Found DOCUMENT_ID: {doc_id}")
    print(f"✓ Found GOOGLE_CREDENTIALS environment variable")
    
    # Validate credentials JSON
    try:
        creds_dict = json.loads(creds_json)
        print(f"✓ Credentials JSON is valid")
        
        # Check key fields in credentials
        client_email = creds_dict.get('client_email')
        if client_email:
            print(f"✓ Service account email: {client_email}")
        else:
            print("❌ Warning: 'client_email' field missing from credentials")
            
        project_id = creds_dict.get('project_id')
        if project_id:
            print(f"✓ Project ID: {project_id}")
        else:
            print("❌ Warning: 'project_id' field missing from credentials")
            
    except json.JSONDecodeError as e:
        print("❌ ERROR: GOOGLE_CREDENTIALS is not valid JSON")
        print(f"   Error: {str(e)}")
        if creds_json and len(creds_json) > 50:
            # Show a snippet of the credentials (first 40 chars)
            print(f"   Credentials start with: {creds_json[:40]}...")
        return False
        
    # Create credentials object
    try:
        creds = service_account.Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/documents']
        )
        print("✓ Created credentials object successfully")
    except Exception as e:
        print(f"❌ ERROR: Failed to create credentials object: {str(e)}")
        traceback.print_exc()
        return False
        
    # Build the service
    try:
        docs_service = build('docs', 'v1', credentials=creds)
        print("✓ Built Google Docs API service successfully")
    except Exception as e:
        print(f"❌ ERROR: Failed to build API service: {str(e)}")
        traceback.print_exc()
        return False
        
    # Try to access the document
    try:
        print(f"\nAttempting to access document {doc_id}...")
        document = docs_service.documents().get(documentId=doc_id).execute()
        
        # Success! Get document info
        title = document.get('title', 'Untitled')
        print(f"✓ SUCCESS! Retrieved document: '{title}'")
        
        # Get revision info
        revision = document.get('revisionId', 'unknown')
        print(f"✓ Document revision: {revision}")
        
        # Get document size
        content_length = 0
        if 'body' in document and 'content' in document['body']:
            content_length = document['body']['content'][-1].get('endIndex', 0)
        
        print(f"✓ Document size: {content_length} characters")
        
        # Try a minimal write
        print("\nTesting write permission...")
        test_text = f"Auth test: {os.environ.get('GITHUB_RUN_ID', 'local test')}"
        
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1
                    },
                    'text': test_text + '\n'
                }
            }
        ]
        
        result = docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={'requests': requests}
        ).execute()
        
        print("✓ Write operation successful!")
        
        print("\n✅ All tests passed successfully! Your authentication is working correctly.")
        print(f"   Service account ({client_email}) has proper access to the document.")
        
        # Check document URL
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        print(f"\nDocument URL: {doc_url}")
        print("Make sure this is the document you want to update.")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR accessing document: {str(e)}")
        
        if "404" in str(e):
            print("\nTROUBLESHOOTING:")
            print("1. Double-check your DOCUMENT_ID - it should be the long string from the URL")
            print("   Example: For https://docs.google.com/document/d/abc123xyz/edit")
            print("            The ID is 'abc123xyz'")
            print(f"2. Make sure you've shared this document with {client_email}")
            print("   - Open the document in Google Docs")
            print("   - Click 'Share' in the top-right corner")
            print(f"   - Add {client_email} with 'Editor' permission")
        elif "403" in str(e):
            print("\nTROUBLESHOOTING:")
            print(f"1. Make sure you've shared this document with {client_email}")
            print("   - The service account needs 'Editor' access")
            print("2. Check that the Google Docs API is enabled in your Google Cloud project")
            print(f"   - Go to: https://console.cloud.google.com/apis/library/docs.googleapis.com?project={project_id}")
        else:
            traceback.print_exc()
            
        return False
        
if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)