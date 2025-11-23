#!/usr/bin/env python3
"""
Local test of Email and Calendar agents before deployment
"""

import sys
import os

# Add agent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'email_agent'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'calendar_agent'))

print("="*80)
print("Local Agent Testing - Email and Calendar Agents")
print("="*80)
print()

# Test Email Agent
print("\n" + "="*80)
print("Testing Email Agent")
print("="*80)

try:
    from email_agent.agent import summarize_emails, search_emails

    print("\n1. Testing summarize_emails...")
    result = summarize_emails(time_range="today")

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        print(f"   Message: {result.get('message', '')}")
    else:
        print(f"✅ Success!")
        print(f"   Total unread: {result.get('total_unread', 0)}")
        print(f"   Urgent: {len(result.get('urgent', []))}")
        print(f"   Important: {len(result.get('important', []))}")
        print(f"   Can wait: {len(result.get('can_wait', []))}")

        if result.get('urgent'):
            print(f"\n   Sample urgent email:")
            urgent = result['urgent'][0]
            print(f"      From: {urgent.get('from', 'N/A')}")
            print(f"      Subject: {urgent.get('subject', 'N/A')}")

    print("\n2. Testing search_emails...")
    result = search_emails(query="meeting")

    if isinstance(result, list) and len(result) > 0:
        if "error" in result[0]:
            print(f"❌ Error: {result[0]['error']}")
        else:
            print(f"✅ Success! Found {len(result)} emails")
            if result:
                print(f"   Sample result:")
                print(f"      From: {result[0].get('from', 'N/A')}")
                print(f"      Subject: {result[0].get('subject', 'N/A')}")
    else:
        print(f"✅ No results found (but no error)")

except Exception as e:
    print(f"❌ Email Agent Failed: {e}")
    import traceback
    traceback.print_exc()

# Test Calendar Agent
print("\n\n" + "="*80)
print("Testing Calendar Agent")
print("="*80)

try:
    from calendar_agent.agent import get_daily_schedule, optimize_calendar

    print("\n1. Testing get_daily_schedule...")
    result = get_daily_schedule(user_email="me")

    if "error" in result:
        print(f"❌ Error: {result['error']}")
        print(f"   Message: {result.get('message', '')}")
    else:
        print(f"✅ Success!")
        print(f"   Date: {result.get('date', 'N/A')}")
        print(f"   Total meetings: {result.get('total_meetings', 0)}")

        meetings = result.get('meetings', [])
        if meetings:
            print(f"\n   Sample meeting:")
            meeting = meetings[0]
            print(f"      Title: {meeting.get('title', 'N/A')}")
            print(f"      Time: {meeting.get('time', 'N/A')}")
            print(f"      Location: {meeting.get('location', 'N/A')}")

    print("\n2. Testing optimize_calendar...")
    result = optimize_calendar(user_email="me", time_range="this_week")

    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"✅ Success!")
        print(f"   Total meetings: {result.get('total_meetings', 0)}")
        print(f"   Total hours: {result.get('total_hours', 0)}")
        print(f"   Recommendations: {len(result.get('recommendations', []))}")

        if result.get('recommendations'):
            print(f"\n   First recommendation:")
            rec = result['recommendations'][0]
            print(f"      Type: {rec.get('type', 'N/A')}")
            print(f"      Priority: {rec.get('priority', 'N/A')}")
            print(f"      Message: {rec.get('message', 'N/A')}")

except Exception as e:
    print(f"❌ Calendar Agent Failed: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n\n" + "="*80)
print("SUMMARY")
print("="*80)
print()
print("✅ If both agents work above, you can deploy them!")
print()
print("Deployment commands:")
print("  python deploy_agent.py email_agent --staging-bucket gs://adk-agent-staging-458318")
print("  python deploy_agent.py calendar_agent --staging-bucket gs://adk-agent-staging-458318")
print()
