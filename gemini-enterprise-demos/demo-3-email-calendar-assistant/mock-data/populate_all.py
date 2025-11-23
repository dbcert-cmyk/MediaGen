#!/usr/bin/env python3
"""
Master script to populate all mock demo data
Runs Gmail, Calendar, and Drive population scripts
"""

import subprocess
import sys
import os

def run_script(script_name, description):
    """Run a population script"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"{'='*60}\n")

    try:
        result = subprocess.run(
            [sys.executable, script_name],
            check=False,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"⚠️  {description} completed with errors")
            return False

    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False


def verify_all_accounts(target_email):
    """Verify we can access Gmail, Calendar, and Drive for target account"""
    print(f"\n{'='*60}")
    print("Verifying Access to All Services")
    print(f"{'='*60}\n")

    errors = []

    # Check Gmail
    try:
        from google.auth import default
        from googleapiclient.discovery import build

        print("📧 Checking Gmail access...")
        gmail_creds, _ = default(scopes=['https://www.googleapis.com/auth/gmail.readonly'])
        gmail_service = build('gmail', 'v1', credentials=gmail_creds)
        gmail_profile = gmail_service.users().getProfile(userId='me').execute()
        gmail_email = gmail_profile['emailAddress']

        if gmail_email.lower() == target_email.lower():
            print(f"   ✓ Gmail: {gmail_email}")
        else:
            print(f"   ❌ Gmail: Authenticated as {gmail_email}, expected {target_email}")
            errors.append(f"Gmail is authenticated as {gmail_email}")
    except Exception as e:
        print(f"   ❌ Gmail Error: {e}")
        errors.append(f"Gmail: {e}")

    # Check Calendar
    try:
        print("\n📅 Checking Calendar access...")
        cal_creds, _ = default(scopes=['https://www.googleapis.com/auth/calendar.readonly'])
        cal_service = build('calendar', 'v3', credentials=cal_creds)
        cal_list = cal_service.calendarList().get(calendarId='primary').execute()
        cal_email = cal_list.get('id', 'Unknown')

        if cal_email.lower() == target_email.lower():
            print(f"   ✓ Calendar: {cal_email}")
        else:
            print(f"   ❌ Calendar: Authenticated as {cal_email}, expected {target_email}")
            errors.append(f"Calendar is authenticated as {cal_email}")
    except Exception as e:
        print(f"   ❌ Calendar Error: {e}")
        errors.append(f"Calendar: {e}")

    # Check Drive
    try:
        print("\n📁 Checking Drive access...")
        drive_creds, _ = default(scopes=['https://www.googleapis.com/auth/drive.readonly'])
        drive_service = build('drive', 'v3', credentials=drive_creds)
        about = drive_service.about().get(fields='user').execute()
        drive_email = about['user']['emailAddress']

        if drive_email.lower() == target_email.lower():
            print(f"   ✓ Drive: {drive_email}")
        else:
            print(f"   ❌ Drive: Authenticated as {drive_email}, expected {target_email}")
            errors.append(f"Drive is authenticated as {drive_email}")
    except Exception as e:
        print(f"   ❌ Drive Error: {e}")
        errors.append(f"Drive: {e}")

    print()
    if errors:
        print(f"{'='*60}")
        print("❌ VERIFICATION FAILED")
        print(f"{'='*60}")
        for error in errors:
            print(f"  • {error}")
        print(f"\nPlease ensure you're authenticated as: {target_email}")
        print("Run: gcloud auth application-default login")
        return False
    else:
        print(f"{'='*60}")
        print("✅ ALL SERVICES VERIFIED")
        print(f"{'='*60}")
        print(f"Mock data will be created in: {target_email}")
        return True


def main():
    """Main entry point"""
    print("="*60)
    print("Populate ALL Mock Demo Data")
    print("="*60)
    print()
    print("This will populate:")
    print("  1. Gmail with 10 sample emails")
    print("  2. Calendar with 10 sample events")
    print("  3. Drive with 10 sample documents")
    print()
    print("⚠️  PREREQUISITES:")
    print("  - APIs enabled (Gmail, Calendar, Drive)")
    print("  - Authenticated: gcloud auth application-default login")
    print("  - Discovery Engine datastores created")
    print()

    # Ask for target email
    print("Which Google Workspace account should receive the mock data?")
    print("(This should match your Discovery Engine datastore connection)")
    target_email = input("Enter email address: ").strip()

    if not target_email:
        print("❌ Error: Email address is required")
        return

    # Verify access to all services
    if not verify_all_accounts(target_email):
        return

    print()
    response = input("Ready to populate ALL demo data? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return

    # Set environment variable for child scripts
    os.environ['DEMO_TARGET_EMAIL'] = target_email

    results = []

    # 1. Populate Gmail
    results.append(run_script('populate_gmail.py', 'Gmail Population'))

    # 2. Populate Calendar
    results.append(run_script('populate_calendar.py', 'Calendar Population'))

    # 3. Populate Drive
    results.append(run_script('populate_drive.py', 'Drive Population'))

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Gmail:    {'✅' if results[0] else '❌'}")
    print(f"Calendar: {'✅' if results[1] else '❌'}")
    print(f"Drive:    {'✅' if results[2] else '❌'}")
    print()

    if all(results):
        print("🎉 All mock data populated successfully!")
        print()
        print("Next Steps:")
        print("1. Wait 1-2 hours for Discovery Engine to sync")
        print("2. Check sync status:")
        print("   cd ../setup/adk-agents")
        print("   python check_datastores.py")
        print("3. Test agents in Gemini Enterprise Plus")
    else:
        print("⚠️  Some scripts encountered errors. Check logs above.")


if __name__ == '__main__':
    main()
