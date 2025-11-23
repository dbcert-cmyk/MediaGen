#!/usr/bin/env python3
"""
Verify which Google Workspace account will receive mock data
"""

from google.auth import default
from googleapiclient.discovery import build

def verify_accounts():
    """Check authenticated accounts for Gmail, Calendar, and Drive"""

    print("="*60)
    print("Verifying Authenticated Google Workspace Accounts")
    print("="*60)
    print()

    try:
        # Check Gmail account
        print("📧 Checking Gmail account...")
        gmail_creds, _ = default(scopes=['https://www.googleapis.com/auth/gmail.readonly'])
        gmail_service = build('gmail', 'v1', credentials=gmail_creds)
        gmail_profile = gmail_service.users().getProfile(userId='me').execute()
        gmail_email = gmail_profile['emailAddress']
        print(f"   ✓ Gmail: {gmail_email}")

    except Exception as e:
        print(f"   ❌ Gmail Error: {e}")
        gmail_email = None

    try:
        # Check Calendar account
        print("\n📅 Checking Calendar account...")
        cal_creds, _ = default(scopes=['https://www.googleapis.com/auth/calendar.readonly'])
        cal_service = build('calendar', 'v3', credentials=cal_creds)
        cal_list = cal_service.calendarList().get(calendarId='primary').execute()
        cal_email = cal_list.get('id', 'Unknown')
        print(f"   ✓ Calendar: {cal_email}")

    except Exception as e:
        print(f"   ❌ Calendar Error: {e}")
        cal_email = None

    try:
        # Check Drive account
        print("\n📁 Checking Drive account...")
        drive_creds, _ = default(scopes=['https://www.googleapis.com/auth/drive.readonly'])
        drive_service = build('drive', 'v3', credentials=drive_creds)
        about = drive_service.about().get(fields='user').execute()
        drive_email = about['user']['emailAddress']
        print(f"   ✓ Drive: {drive_email}")

    except Exception as e:
        print(f"   ❌ Drive Error: {e}")
        drive_email = None

    print("\n" + "="*60)
    print("Summary")
    print("="*60)

    if gmail_email and cal_email and drive_email:
        if gmail_email == cal_email == drive_email:
            print(f"✅ All services use the same account: {gmail_email}")
            print(f"\n🎯 Mock data will be created in: {gmail_email}")
            print("\nNext steps:")
            print("1. Verify this matches your Discovery Engine datastores")
            print("2. Check datastores at: https://console.cloud.google.com/gen-app-builder/data-stores?project=ai-testing-458318")
            print("3. If it matches, run: python populate_all.py")
        else:
            print("⚠️  WARNING: Different accounts detected!")
            print(f"   Gmail: {gmail_email}")
            print(f"   Calendar: {cal_email}")
            print(f"   Drive: {drive_email}")
            print("\nThis might cause issues. Ensure all services use the same account.")
    else:
        print("❌ Authentication failed for some services")
        print("\nRun: gcloud auth application-default login")
        print("Then try again")

    print()

if __name__ == '__main__':
    verify_accounts()
