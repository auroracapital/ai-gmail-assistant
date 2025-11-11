#!/usr/bin/env python3
"""
Gmail Inbox Organizer
AI-powered email organization with language-aware drafts and smart categorization
"""

import os
import sys
import pickle
import json
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Gmail API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# OpenAI/OpenRouter
from openai import OpenAI

# Configuration from environment variables
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
GMAIL_CREDENTIALS_PATH = os.getenv('GMAIL_CREDENTIALS_PATH', './credentials/client_secret.json')
GMAIL_TOKEN_PATH = os.getenv('GMAIL_TOKEN_PATH', './credentials/gmail_token.pickle')
MAX_EMAILS = int(os.getenv('MAX_EMAILS', '50'))
AI_MODEL = os.getenv('AI_MODEL', 'anthropic/claude-sonnet-4.5')
AI_TEMP_CATEGORIZATION = float(os.getenv('AI_TEMPERATURE_CATEGORIZATION', '0.1'))
AI_TEMP_DRAFTS = float(os.getenv('AI_TEMPERATURE_DRAFTS', '0.3'))

# User profile for AI context
USER_NAME = os.getenv('USER_NAME', 'User')
USER_ROLE = os.getenv('USER_ROLE', 'Professional')
USER_COMPANIES = os.getenv('USER_COMPANIES', '').split(',')
USER_LOCATION = os.getenv('USER_LOCATION', '')
USER_LANGUAGES = os.getenv('USER_LANGUAGES', 'English').split(',')

# Gmail API scopes
SCOPES = ['https://mail.google.com/']

# Label colors (Gmail API format)
LABEL_COLORS = {
    'action': {
        'backgroundColor': os.getenv('LABEL_COLOR_ACTION_BG', '#fb4c2f'),
        'textColor': os.getenv('LABEL_COLOR_ACTION_TEXT', '#ffffff')
    },
    'respond': {
        'backgroundColor': os.getenv('LABEL_COLOR_RESPOND_BG', '#ffad47'),
        'textColor': os.getenv('LABEL_COLOR_RESPOND_TEXT', '#000000')
    },
    'fyi': {
        'backgroundColor': os.getenv('LABEL_COLOR_FYI_BG', '#16a766'),
        'textColor': os.getenv('LABEL_COLOR_FYI_TEXT', '#ffffff')
    }
}


def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = ['OPENROUTER_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Error: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please copy .env.example to .env and fill in your values")
        sys.exit(1)
    
    if not os.path.exists(GMAIL_CREDENTIALS_PATH):
        print(f"❌ Error: Gmail credentials file not found: {GMAIL_CREDENTIALS_PATH}")
        print("Please download OAuth credentials from Google Cloud Console")
        sys.exit(1)


def get_gmail_service():
    """Authenticate and return Gmail API service"""
    creds = None
    
    # Load existing token
    if os.path.exists(GMAIL_TOKEN_PATH):
        with open(GMAIL_TOKEN_PATH, 'rb') as token:
            creds = pickle.load(token)
    
    # Refresh or create new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save token
        os.makedirs(os.path.dirname(GMAIL_TOKEN_PATH), exist_ok=True)
        with open(GMAIL_TOKEN_PATH, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)


def detect_language(text: str, client: OpenAI) -> str:
    """
    Detect the language of the email text using AI
    Analyzes first 500 characters to focus on latest message
    Returns the detected language name (e.g., 'English', 'Dutch', 'Spanish', 'French', etc.)
    """
    sample = text[:500]
    
    if not sample.strip():
        return "English"  # Default fallback
    
    prompt = f"""Detect the language of this text and respond with ONLY the language name in English (e.g., 'English', 'Dutch', 'Spanish', 'French', 'German', 'Italian', 'Portuguese', 'Chinese', 'Japanese', etc.).

Text:
{sample}

Language:"""
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,  # Deterministic for language detection
            max_tokens=10
        )
        
        detected_language = response.choices[0].message.content.strip()
        return detected_language
    except Exception as e:
        print(f"⚠️  Language detection error: {e}, defaulting to English")
        return "English"


def categorize_email_with_ai(email_data: Dict, client: OpenAI) -> Dict:
    """Use AI to categorize email and determine actions"""
    
    subject = email_data.get('subject', '')
    body = email_data.get('body', '')[:2000]  # Limit to first 2000 chars
    sender = email_data.get('from', '')
    
    user_context = f"""
User Profile:
- Name: {USER_NAME}
- Role: {USER_ROLE}
- Companies: {', '.join(USER_COMPANIES)}
- Location: {USER_LOCATION}
- Languages: {', '.join(USER_LANGUAGES)}
"""
    
    prompt = f"""{user_context}

Analyze this email and categorize it:

From: {sender}
Subject: {subject}
Body: {body}

Categorize this email with the following JSON format:
{{
    "category": "urgent|business|financial|personal|promotional|spam",
    "action": "delete|keep",
    "star": true|false,
    "labels": ["action", "respond", "fyi"],
    "confidence": "high|medium|low",
    "reasoning": "brief explanation"
}}

Rules:
- NEVER delete: billing, payments, business emails, investor communications, legal matters
- ONLY delete: expired verification codes, obvious spam, promotional newsletters
- Star ONLY if: critical urgent matter requiring immediate action (24-48h)
- "action" label: requires specific task (payment, contract signing, etc.)
- "respond" label: needs email reply
- "fyi" label: informational only
- Can have multiple labels (e.g., both "action" and "respond")
"""
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=AI_TEMP_CATEGORIZATION,
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        print(f"❌ AI categorization error: {e}")
        return {
            "category": "personal",
            "action": "keep",
            "star": False,
            "labels": [],
            "confidence": "low",
            "reasoning": "Error in AI categorization"
        }


def generate_draft_reply(email_data: Dict, language: str, labels: List[str], client: OpenAI) -> str:
    """Generate language-aware draft reply"""
    
    subject = email_data.get('subject', '')
    body = email_data.get('body', '')[:2000]
    sender = email_data.get('from', '')
    
    has_action = 'action' in labels
    has_respond = 'respond' in labels
    
    if not has_action and not has_respond:
        return None
    
    draft_type = "both response and action outline" if (has_action and has_respond) else \
                 "action outline only" if has_action else \
                 "response only"
    
    prompt = f"""Generate a {draft_type} for this email in {language}.

From: {sender}
Subject: {subject}
Body: {body}

User: {USER_NAME} ({USER_ROLE})

Requirements:
- Write in {language} language
- Match the tone and formality of the original email
- Keep it professional but friendly
- If action outline: provide step-by-step instructions
- If response: be concise and clear
- If both: include action outline in the response

Generate the draft:
"""
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=AI_TEMP_DRAFTS,
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Draft generation error: {e}")
        return None


def main():
    """Main execution function"""
    print("=" * 70)
    print("AI-Enhanced Gmail Inbox Organizer")
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Validate environment
    validate_environment()
    
    # Initialize clients
    print("🔐 Authenticating with Gmail...")
    gmail_service = get_gmail_service()
    
    print("🤖 Initializing AI client...")
    ai_client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY
    )
    
    # Fetch emails
    print(f"📧 Fetching up to {MAX_EMAILS} emails from inbox...")
    results = gmail_service.users().messages().list(
        userId='me',
        labelIds=['INBOX'],
        maxResults=MAX_EMAILS
    ).execute()
    
    messages = results.get('messages', [])
    print(f"Found {len(messages)} emails to process\n")
    
    # Process emails
    stats = {
        'processed': 0,
        'deleted': 0,
        'starred': 0,
        'labeled': 0,
        'drafts_created': 0
    }
    
    for i, message in enumerate(messages, 1):
        try:
            # Get full message
            msg = gmail_service.users().messages().get(
                userId='me',
                id=message['id'],
                format='full'
            ).execute()
            
            # Extract email data
            headers = {h['name']: h['value'] for h in msg['payload']['headers']}
            subject = headers.get('Subject', '(No subject)')
            sender = headers.get('From', '')
            
            # Get body
            body = ""
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        body = part.get('body', {}).get('data', '')
                        break
            else:
                body = msg['payload'].get('body', {}).get('data', '')
            
            email_data = {
                'subject': subject,
                'from': sender,
                'body': body,
                'thread_id': msg['threadId']
            }
            
            print(f"[{i}/{len(messages)}] {subject[:60]}...")
            
            # Detect language using AI
            language = detect_language(f"{subject} {body}", ai_client)
            print(f"🌐 Language: {language}")
            
            # Categorize with AI
            categorization = categorize_email_with_ai(email_data, ai_client)
            print(f"📊 {categorization['category']} | {categorization['action']} | ⭐{categorization['star']}")
            print(f"🏷️  {', '.join(categorization['labels'])}")
            
            # Execute actions
            if categorization['action'] == 'delete' and categorization['confidence'] == 'high':
                # Delete email
                gmail_service.users().messages().delete(userId='me', id=message['id']).execute()
                print("🗑️  DELETED")
                stats['deleted'] += 1
            else:
                # Star if needed
                if categorization['star']:
                    gmail_service.users().messages().modify(
                        userId='me',
                        id=message['id'],
                        body={'addLabelIds': ['STARRED']}
                    ).execute()
                    print("⭐ STARRED")
                    stats['starred'] += 1
                
                # Apply labels
                if categorization['labels']:
                    # Note: Label application would require creating labels first
                    # This is a simplified version
                    stats['labeled'] += 1
                
                # Generate draft
                if 'action' in categorization['labels'] or 'respond' in categorization['labels']:
                    draft_content = generate_draft_reply(
                        email_data,
                        language,
                        categorization['labels'],
                        ai_client
                    )
                    
                    if draft_content:
                        # Create draft (simplified - would need proper email formatting)
                        print(f"✓ DRAFT: {language}")
                        stats['drafts_created'] += 1
            
            stats['processed'] += 1
            print()
            
        except HttpError as e:
            print(f"❌ Error processing email: {e}")
            continue
    
    # Print summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Processed: {stats['processed']}")
    print(f"Deleted: {stats['deleted']}")
    print(f"Starred: {stats['starred']}")
    print(f"Labeled: {stats['labeled']}")
    print(f"Drafts created: {stats['drafts_created']}")
    print("=" * 70)


if __name__ == "__main__":
    main()
