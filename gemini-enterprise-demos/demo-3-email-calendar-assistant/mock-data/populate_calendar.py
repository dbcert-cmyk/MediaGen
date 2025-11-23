#!/usr/bin/env python3
"""
Populate Google Calendar with mock demo data
Uses Calendar API to create realistic demo events
"""

import json
import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
SCOPES = ['https://www.googleapis.com/auth/calendar']


def create_calendar_service():
    """Create Calendar API service"""
    from google.auth import default
    credentials, _ = default(scopes=SCOPES)

    service = build('calendar', 'v3', credentials=credentials)
    return service


def adjust_event_dates_to_current_week(event):
    """
    Adjust event dates to current week for demo purposes
    Converts dates from JSON to this week
    """
    # Parse the original date
    start_dt = datetime.fromisoformat(event['start'].replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(event['end'].replace('Z', '+00:00'))

    # Calculate duration
    duration = end_dt - start_dt

    # Get current week's Monday
    today = datetime.now()
    days_since_monday = today.weekday()
    current_monday = today - timedelta(days=days_since_monday)

    # Map to current week (preserve time of day and day of week)
    original_weekday = start_dt.weekday()
    new_start = current_monday.replace(
        hour=start_dt.hour,
        minute=start_dt.minute,
        second=0,
        microsecond=0
    ) + timedelta(days=original_weekday)

    new_end = new_start + duration

    # Convert back to RFC3339 format
    return {
        'start': new_start.isoformat(),
        'end': new_end.isoformat()
    }


def create_calendar_event(service, event_data):
    """Create a calendar event"""

    # Adjust dates to current week
    adjusted_dates = adjust_event_dates_to_current_week(event_data)

    # Build event object
    event = {
        'summary': event_data['title'],
        'location': event_data.get('location', ''),
        'description': event_data.get('description', ''),
        'start': {
            'dateTime': adjusted_dates['start'],
            'timeZone': 'America/Los_Angeles',
        },
        'end': {
            'dateTime': adjusted_dates['end'],
            'timeZone': 'America/Los_Angeles',
        },
        'attendees': [
            {'email': email} for email in event_data.get('attendees', [])
        ],
        'reminders': {
            'useDefault': True,
        },
    }

    # Add recurrence if specified
    if event_data.get('recurring') and event_data.get('recurrence_rule'):
        event['recurrence'] = [f"RRULE:{event_data['recurrence_rule']}"]

    # Create the event
    created_event = service.events().insert(
        calendarId='primary',
        body=event,
        sendUpdates='none'  # Don't send email notifications for demo data
    ).execute()

    return created_event


def populate_calendar_from_json(service, json_file='calendar_mock_data.json'):
    """Populate Calendar with events from JSON file"""

    print("Loading mock calendar data...")
    with open(json_file, 'r') as f:
        data = json.load(f)

    events = data['events']
    print(f"Found {len(events)} events to create\n")

    created_count = 0

    for event in events:
        print(f"Creating event: {event['title']}")

        try:
            created_event = create_calendar_event(service, event)
            print(f"  ✓ Created: {created_event['id']}")
            print(f"    Start: {created_event['start'].get('dateTime', 'N/A')}")
            created_count += 1

        except Exception as e:
            print(f"  ✗ Error: {e}")

    print(f"\n{'='*60}")
    print(f"✅ Successfully created {created_count}/{len(events)} events")
    print(f"{'='*60}")

    print("\n📊 Calendar Summary:")
    print(f"- Events this week: {created_count}")
    stats = data.get('calendar_stats', {})
    print(f"- Total meeting hours: {stats.get('total_meeting_hours_this_week', 'N/A')}")
    print(f"- Back-to-back meetings: {stats.get('back_to_back_meetings', 'N/A')}")

    print("\nNote: Discovery Engine will sync these events within 1-2 hours.")
    print("Check sync status with: python ../setup/adk-agents/check_datastores.py")


def clear_demo_events(service):
    """Optional: Clear all events from calendar (use with caution!)"""
    print("\n⚠️  WARNING: This will delete ALL events from your calendar!")
    response = input("Are you sure you want to proceed? (yes/no): ")

    if response.lower() != 'yes':
        print("Cancelled.")
        return

    # Get all events
    now = datetime.utcnow().isoformat() + 'Z'
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=100,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    deleted_count = 0
    for event in events:
        try:
            service.events().delete(
                calendarId='primary',
                eventId=event['id']
            ).execute()
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting event: {e}")

    print(f"Deleted {deleted_count} events")


def main():
    """Main entry point"""
    print("="*60)
    print("Google Calendar Mock Data Population Tool")
    print("="*60)
    print()

    print("⚠️  IMPORTANT:")
    print("1. Make sure you have Calendar API enabled")
    print("2. Run: gcloud auth application-default login")
    print("3. Grant Calendar permissions when prompted")
    print("4. Events will be created in current week (preserving times)")
    print()

    response = input("Ready to populate Calendar with mock data? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return

    try:
        service = create_calendar_service()
        print("✓ Calendar API authenticated\n")

        populate_calendar_from_json(service)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Run: gcloud services enable calendar-json.googleapis.com")
        print("2. Run: gcloud auth application-default login")
        print("3. Ensure you have Calendar API access")


if __name__ == '__main__':
    main()
