#!/usr/bin/env python3
"""
Populate Gmail with mock demo data
Uses Gmail API to create realistic demo emails
"""

import json
import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
USER_EMAIL = "demo-user@company.com"  # Change this to your actual test Gmail account
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


def create_gmail_service():
    """Create Gmail API service"""
    # For demo, we'll use application default credentials
    # In production, you'd use service account with domain-wide delegation
    from google.auth import default
    credentials, _ = default(scopes=SCOPES)

    service = build('gmail', 'v1', credentials=credentials)
    return service


def create_message(sender, to, subject, body, labels=None):
    """Create email message"""
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = to
    message['Subject'] = subject

    msg_body = MIMEText(body, 'plain')
    message.attach(msg_body)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    msg_dict = {'raw': raw}
    if labels:
        # Map friendly labels to Gmail label IDs
        label_mapping = {
            'INBOX': 'INBOX',
            'IMPORTANT': 'IMPORTANT',
            'UNREAD': 'UNREAD'
        }
        msg_dict['labelIds'] = [label_mapping.get(l, l) for l in labels]

    return msg_dict


def populate_emails_from_json(service, json_file='gmail_mock_data.json'):
    """Populate Gmail with emails from JSON file"""

    print("Loading mock email data...")
    with open(json_file, 'r') as f:
        data = json.load(f)

    emails = data['emails']
    print(f"Found {len(emails)} emails to create\n")

    created_count = 0

    for email in emails:
        print(f"Creating email: {email['subject']}")

        try:
            # Create the message
            message = create_message(
                sender=email['from'],
                to=email['to'],
                subject=email['subject'],
                body=email['body'],
                labels=email.get('labels', ['INBOX'])
            )

            # Insert the message
            result = service.users().messages().insert(
                userId='me',
                body=message
            ).execute()

            print(f"  ✓ Created: {result['id']}")
            created_count += 1

            # Mark as unread if specified
            if email.get('is_unread', False):
                service.users().messages().modify(
                    userId='me',
                    id=result['id'],
                    body={'addLabelIds': ['UNREAD']}
                ).execute()

        except Exception as e:
            print(f"  ✗ Error: {e}")

    print(f"\n{'='*60}")
    print(f"✅ Successfully created {created_count}/{len(emails)} emails")
    print(f"{'='*60}")

    print("\nNote: Discovery Engine will sync these emails within 1-2 hours.")
    print("Check sync status with: python ../setup/adk-agents/check_datastores.py")


def main():
    """Main entry point"""
    print("="*60)
    print("Gmail Mock Data Population Tool")
    print("="*60)
    print()

    print("⚠️  IMPORTANT:")
    print("1. Make sure you have Gmail API enabled")
    print("2. Run: gcloud auth application-default login")
    print("3. Grant Gmail permissions when prompted")
    print()

    response = input("Ready to populate Gmail with mock data? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return

    try:
        service = create_gmail_service()
        print("✓ Gmail API authenticated\n")

        populate_emails_from_json(service)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Run: gcloud services enable gmail.googleapis.com")
        print("2. Run: gcloud auth application-default login")
        print("3. Ensure you have Gmail API access")


if __name__ == '__main__':
    main()
