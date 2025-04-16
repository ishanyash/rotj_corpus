#!/usr/bin/env python3
"""
Debug script to test Google API authentication
"""

import os
import json
import sys
from googleapiclient.discovery import build
from google.oauth2 import service_account

def main():
    print("\n----- Google Docs API Authentication Test -----\n")
    
    # Check environment variables
    doc_id = os.environ.get('DOCUMENT_ID')
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    
    if not doc_id:
        print("❌ ERROR: DOCUMENT_ID environment variable is not set.")
        return False
        
    if not creds_json:
        print("❌ ERROR: GOOGLE_CREDENTIALS environment variable is not set.")
        return False
        
    print(f"✓ Found DOCUMENT_ID: {doc_id}")
    print(f"✓ Found GOOGLE_CREDENTIALS environment variable")
    
    # Validate credentials JSON
    try:
        creds_dict = json.loads(creds_json)
        print(f"✓ Credentials JSON is valid")
        
        client_email = creds_dict.get('client_email')
        if client_email:
            print(f"✓ Service account email: {client_email}")
            
    except json.JSONDecodeError as e:
        print("❌ ERROR: GOOGLE_CREDENTIALS is not valid JSON")
        print(f"   Error: {str(e)}")
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
        return False
        
    # Build the service
    try:
        docs_service = build('docs', 'v1', credentials=creds)
        print("✓ Built Google Docs API service successfully")
    except Exception as e:
        print(f"❌ ERROR: Failed to build API service: {str(e)}")
        return False
        
    # Try to access the document
    try:
        print(f"\nAttempting to access document {doc_id}...")
        document = docs_service.documents().get(documentId=doc_id).execute()
        
        # Success! Get document info
        title = document.get('title', 'Untitled')
        print(f"✓ SUCCESS! Retrieved document: '{title}'")
        
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
        print("\n✅ All tests passed! Your authentication is working correctly.")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR accessing document: {str(e)}")
        
        if "404" in str(e):
            print("\nTROUBLESHOOTING:")
            print("1. Double-check your DOCUMENT_ID - it should be the string from the URL")
            print(f"2. Make sure you've shared this document with {client_email}")
        elif "403" in str(e):
            print("\nTROUBLESHOOTING:")
            print(f"1. Make sure you've shared this document with {client_email}")
            print("2. Check that the Google Docs API is enabled in your Google Cloud project")
            
        return False
        
if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)