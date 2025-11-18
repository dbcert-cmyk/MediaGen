"""
Firestore Schema Setup for Demo #3
Creates collections and loads mock data for user preferences and learning
"""

from google.cloud import firestore
from datetime import datetime, timedelta
import json


def setup_firestore_schema(project_id: str):
    """
    Initialize Firestore database with demo data

    Args:
        project_id: Google Cloud project ID
    """
    db = firestore.Client(project=project_id)

    print("Setting up Firestore collections...")

    # 1. User Preferences Collection
    setup_user_preferences(db)

    # 2. Email Patterns Collection (learned behaviors)
    setup_email_patterns(db)

    # 3. Meeting Preferences Collection
    setup_meeting_preferences(db)

    # 4. Follow-up Tasks Collection
    setup_followup_tasks(db)

    print("✅ Firestore setup complete!")


def setup_user_preferences(db: firestore.Client):
    """Create user_preferences collection"""
    print("Creating user_preferences collection...")

    users_ref = db.collection('user_preferences')

    demo_user_prefs = {
        "user_id": "demo-user@company.com",
        "email_settings": {
            "auto_summarize": True,
            "priority_senders": [
                "sarah.chen@acmecorp.com",
                "cto@company.com",
                "hr@company.com"
            ],
            "auto_label": True,
            "suggested_responses": True,
            "notification_threshold": "important_only"
        },
        "calendar_settings": {
            "auto_decline_conflicts": False,
            "prefer_morning_meetings": True,
            "max_meetings_per_day": 5,
            "required_break_minutes": 15,
            "default_meeting_duration": 30,
            "working_hours": {
                "start": "09:00",
                "end": "17:00",
                "timezone": "America/Los_Angeles"
            },
            "focus_time_blocks": [
                {
                    "day": "Tuesday",
                    "start": "14:00",
                    "end": "16:00",
                    "recurring": True
                },
                {
                    "day": "Thursday",
                    "start": "14:00",
                    "end": "16:00",
                    "recurring": True
                }
            ]
        },
        "productivity_settings": {
            "daily_briefing_time": "08:00",
            "end_of_day_summary": True,
            "weekly_review": True,
            "auto_follow_ups": True
        },
        "learning_preferences": {
            "track_response_patterns": True,
            "suggest_templates": True,
            "learn_from_actions": True
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }

    users_ref.document("demo-user").set(demo_user_prefs)
    print(f"  ✓ Created preferences for demo-user@company.com")


def setup_email_patterns(db: firestore.Client):
    """Create email_patterns collection for learned behaviors"""
    print("Creating email_patterns collection...")

    patterns_ref = db.collection('email_patterns')

    patterns = [
        {
            "pattern_id": "urgent_keywords",
            "user_id": "demo-user@company.com",
            "pattern_type": "urgency_detection",
            "keywords": ["urgent", "asap", "eod", "deadline", "critical", "important"],
            "confidence_score": 0.92,
            "learned_from_count": 145,
            "last_updated": datetime.now()
        },
        {
            "pattern_id": "meeting_request_pattern",
            "user_id": "demo-user@company.com",
            "pattern_type": "meeting_detection",
            "keywords": ["schedule", "meet", "call", "sync", "discuss", "available"],
            "typical_response": "Let me check my calendar and propose some times",
            "confidence_score": 0.88,
            "learned_from_count": 87,
            "last_updated": datetime.now()
        },
        {
            "pattern_id": "status_update_pattern",
            "user_id": "demo-user@company.com",
            "pattern_type": "status_update",
            "from_patterns": ["sarah.chen@", "cto@"],
            "typical_response_template": "Here's the current status:\n\n[status details]\n\nNext steps:\n[action items]",
            "confidence_score": 0.85,
            "learned_from_count": 62,
            "last_updated": datetime.now()
        },
        {
            "pattern_id": "quick_question_pattern",
            "user_id": "demo-user@company.com",
            "pattern_type": "quick_question",
            "keywords": ["quick question", "briefly", "fyi", "heads up"],
            "average_response_time_minutes": 15,
            "confidence_score": 0.91,
            "learned_from_count": 203,
            "last_updated": datetime.now()
        }
    ]

    for pattern in patterns:
        patterns_ref.document(pattern["pattern_id"]).set(pattern)
        print(f"  ✓ Created pattern: {pattern['pattern_id']}")


def setup_meeting_preferences(db: firestore.Client):
    """Create meeting_preferences collection"""
    print("Creating meeting_preferences collection...")

    meeting_prefs_ref = db.collection('meeting_preferences')

    preferences = [
        {
            "pref_id": "preferred_meeting_times",
            "user_id": "demo-user@company.com",
            "preference_type": "time_slots",
            "data": {
                "most_productive_hours": ["10:00-11:00", "14:00-15:00"],
                "avoid_hours": ["08:00-09:00", "16:00-17:00"],
                "preferred_days": ["Tuesday", "Wednesday", "Thursday"],
                "avoid_days": ["Monday_morning", "Friday_afternoon"]
            },
            "confidence_score": 0.87,
            "learned_from_meetings": 156,
            "last_updated": datetime.now()
        },
        {
            "pref_id": "meeting_type_duration",
            "user_id": "demo-user@company.com",
            "preference_type": "duration_by_type",
            "data": {
                "1_on_1": 30,
                "team_sync": 15,
                "client_demo": 60,
                "planning_session": 120,
                "quick_sync": 15
            },
            "confidence_score": 0.93,
            "learned_from_meetings": 178,
            "last_updated": datetime.now()
        },
        {
            "pref_id": "recurring_meeting_preferences",
            "user_id": "demo-user@company.com",
            "preference_type": "recurring_patterns",
            "data": {
                "daily_standup": {
                    "preferred_time": "09:00",
                    "max_duration": 15,
                    "preferred_days": ["MO", "TU", "WE", "TH", "FR"]
                },
                "weekly_1_on_1s": {
                    "preferred_time": "15:30",
                    "duration": 30,
                    "preferred_day": "Monday"
                }
            },
            "confidence_score": 0.95,
            "last_updated": datetime.now()
        },
        {
            "pref_id": "attendee_preferences",
            "user_id": "demo-user@company.com",
            "preference_type": "attendee_patterns",
            "data": {
                "frequent_collaborators": [
                    {
                        "email": "sarah.chen@acmecorp.com",
                        "meeting_frequency": "weekly",
                        "preferred_duration": 30,
                        "topics": ["budget", "planning", "team_updates"]
                    },
                    {
                        "email": "alex.thompson@company.com",
                        "meeting_frequency": "daily",
                        "preferred_duration": 15,
                        "topics": ["project_updates", "code_review"]
                    }
                ]
            },
            "confidence_score": 0.89,
            "last_updated": datetime.now()
        }
    ]

    for pref in preferences:
        meeting_prefs_ref.document(pref["pref_id"]).set(pref)
        print(f"  ✓ Created preference: {pref['pref_id']}")


def setup_followup_tasks(db: firestore.Client):
    """Create follow_up_tasks collection"""
    print("Creating follow_up_tasks collection...")

    tasks_ref = db.collection('follow_up_tasks')

    now = datetime.now()

    tasks = [
        {
            "task_id": "followup_001",
            "user_id": "demo-user@company.com",
            "task_type": "email_response",
            "priority": "high",
            "related_email_id": "email_001",
            "description": "Respond to Sarah about Q4 budget - deadline EOD",
            "due_date": now,
            "auto_generated": True,
            "status": "pending",
            "created_at": now - timedelta(hours=2),
            "suggested_action": "Send Q4 budget spreadsheet"
        },
        {
            "task_id": "followup_002",
            "user_id": "demo-user@company.com",
            "task_type": "meeting_prep",
            "priority": "medium",
            "related_event_id": "event_007",
            "description": "Review Q1_Roadmap_Draft.pdf before Product Roadmap Planning",
            "due_date": now + timedelta(days=3, hours=-2),
            "auto_generated": True,
            "status": "pending",
            "created_at": now - timedelta(days=1),
            "suggested_action": "Block 30 min to review document"
        },
        {
            "task_id": "followup_003",
            "user_id": "demo-user@company.com",
            "task_type": "meeting_followup",
            "priority": "medium",
            "related_event_id": "event_005",
            "description": "Send meeting notes and action items after API Integration Kickoff",
            "due_date": now + timedelta(days=1, hours=2),
            "auto_generated": True,
            "status": "pending",
            "created_at": now,
            "suggested_action": "Auto-generate notes from meeting transcript"
        },
        {
            "task_id": "followup_004",
            "user_id": "demo-user@company.com",
            "task_type": "decision_required",
            "priority": "medium",
            "related_email_id": "email_010",
            "description": "Decide sprint 24 priorities for Kevin",
            "due_date": now + timedelta(days=2),
            "auto_generated": True,
            "status": "pending",
            "created_at": now - timedelta(hours=4),
            "suggested_action": "Review backlog and respond with priority"
        },
        {
            "task_id": "followup_005",
            "user_id": "demo-user@company.com",
            "task_type": "calendar_action",
            "priority": "low",
            "related_event_id": "event_007",
            "description": "Accept or decline Product Roadmap Planning invite",
            "due_date": now + timedelta(days=2),
            "auto_generated": True,
            "status": "pending",
            "created_at": now - timedelta(days=1),
            "suggested_action": "Accept - this aligns with your priorities"
        }
    ]

    for task in tasks:
        tasks_ref.document(task["task_id"]).set(task)
        print(f"  ✓ Created task: {task['task_id']}")


def export_schema_to_json(project_id: str, output_file: str = "firestore_export.json"):
    """Export Firestore data to JSON for backup/reference"""
    db = firestore.Client(project=project_id)

    export_data = {
        "user_preferences": [],
        "email_patterns": [],
        "meeting_preferences": [],
        "follow_up_tasks": []
    }

    # Export each collection
    for collection_name in export_data.keys():
        docs = db.collection(collection_name).stream()
        for doc in docs:
            data = doc.to_dict()
            # Convert datetime objects to strings
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
            export_data[collection_name].append(data)

    with open(output_file, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)

    print(f"✅ Exported Firestore data to {output_file}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python firestore_schema.py <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]

    print(f"Setting up Firestore for project: {project_id}")
    print("=" * 60)

    setup_firestore_schema(project_id)
    export_schema_to_json(project_id)

    print("\n" + "=" * 60)
    print("Setup complete! You can now use the Firestore collections.")
    print("\nCollections created:")
    print("  - user_preferences (user settings and preferences)")
    print("  - email_patterns (learned email behaviors)")
    print("  - meeting_preferences (calendar optimization data)")
    print("  - follow_up_tasks (automated follow-ups)")
