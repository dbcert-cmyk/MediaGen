"""
Follow-up Agent - Automates post-meeting and post-email follow-ups
Part of Gemini Enterprise Demo #3
"""

import os
from google.adk.agents import Agent
from google.cloud import firestore
from typing import List, Dict, Any
import datetime

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = os.environ.get("LOCATION", "us-central1")


# Helper functions
def _get_firestore_client():
    """Get Firestore client"""
    return firestore.Client(project=PROJECT_ID)


def _extract_action_items(text: str) -> List[Dict[str, Any]]:
    """Extract action items from text"""
    # Simple extraction for demo
    # In production, use NLP/LLM for better extraction
    action_items = []
    lines = text.split('\n')

    for line in lines:
        line_lower = line.lower().strip()
        if any(indicator in line_lower for indicator in ['todo:', 'action:', '[ ]', 'task:']):
            action_items.append({
                "description": line.strip(),
                "status": "pending",
                "created_at": datetime.datetime.now().isoformat()
            })

    return action_items


def _get_meeting_participants(meeting_id: str) -> List[str]:
    """Get meeting participants"""
    # In production, query Calendar data store
    return ["demo-user@company.com", "participant@company.com"]


def _get_email_thread(email_id: str) -> Dict[str, Any]:
    """Get email thread context"""
    # In production, query Gmail API
    return {
        "id": email_id,
        "subject": "Project Update",
        "participants": ["demo-user@company.com", "teammate@company.com"]
    }


def _calculate_urgency_score(item: Dict) -> int:
    """Calculate urgency score for an action item"""
    score = 0

    # Check deadline
    if item.get("deadline"):
        try:
            deadline = datetime.datetime.fromisoformat(item["deadline"])
            days_until = (deadline - datetime.datetime.now()).days
            if days_until < 0:
                score += 100  # Overdue
            elif days_until < 1:
                score += 80   # Due today
            elif days_until < 3:
                score += 50   # Due soon
            elif days_until < 7:
                score += 20   # Due this week
        except:
            pass

    # Check description for urgency indicators
    description_lower = item.get("description", "").lower()
    if any(kw in description_lower for kw in ["urgent", "critical", "asap", "emergency"]):
        score += 30
    elif any(kw in description_lower for kw in ["important", "priority", "needed"]):
        score += 15

    return score


def _generate_summary_template(meeting_id: str, key_points: List[str]) -> str:
    """Generate meeting summary template"""
    return f"""
Meeting Summary for {meeting_id}

Key Discussion Points:
{chr(10).join(f'- {point}' for point in key_points)}

Action Items:
[To be filled by agent]

Next Steps:
[To be filled by agent]

Follow-up Date: [To be determined]
"""


# Tool functions - These are automatically wrapped by ADK as FunctionTools
def create_meeting_followup(
    meeting_id: str,
    meeting_transcript: str = None,
    send_to_participants: bool = True
) -> Dict[str, Any]:
    """
    Generate post-meeting summary with action items.

    Args:
        meeting_id: Calendar event ID
        meeting_transcript: Optional meeting transcript
        send_to_participants: Whether to email participants

    Returns:
        Meeting follow-up package
    """
    db = _get_firestore_client()

    # Extract action items from transcript
    action_items = []
    if meeting_transcript:
        action_items = _extract_action_items(meeting_transcript)

    # Get meeting participants
    participants = _get_meeting_participants(meeting_id)

    # Create follow-up document
    followup = {
        "meeting_id": meeting_id,
        "created_at": datetime.datetime.now().isoformat(),
        "summary": _generate_summary_template(meeting_id, []),
        "action_items": action_items,
        "participants": participants,
        "status": "draft"
    }

    # Save to Firestore
    doc_ref = db.collection("meeting_followups").add(followup)

    # Save action items
    for item in action_items:
        item["meeting_id"] = meeting_id
        item["assigned_to"] = participants[0] if participants else None
        db.collection("follow_up_tasks").add(item)

    return {
        "followup_id": doc_ref[1].id,
        "meeting_id": meeting_id,
        "action_items_count": len(action_items),
        "participants_count": len(participants),
        "will_send_email": send_to_participants
    }


def track_action_item(
    description: str,
    assigned_to: str,
    deadline: str = None,
    priority: str = "medium",
    source: str = "manual"
) -> Dict[str, Any]:
    """
    Create and track an action item.

    Args:
        description: Action item description
        assigned_to: Email of person responsible
        deadline: ISO format deadline (optional)
        priority: "high", "medium", "low"
        source: "meeting", "email", "manual"

    Returns:
        Created action item details
    """
    db = _get_firestore_client()

    action_item = {
        "description": description,
        "assigned_to": assigned_to,
        "deadline": deadline,
        "priority": priority,
        "source": source,
        "status": "pending",
        "created_at": datetime.datetime.now().isoformat(),
        "reminder_count": 0
    }

    # Calculate urgency score
    action_item["urgency_score"] = _calculate_urgency_score(action_item)

    # Save to Firestore
    doc_ref = db.collection("follow_up_tasks").add(action_item)

    return {
        "item_id": doc_ref[1].id,
        "description": description,
        "assigned_to": assigned_to,
        "deadline": deadline,
        "urgency_score": action_item["urgency_score"]
    }


def get_overdue_tasks(
    assigned_to: str = None,
    days_overdue: int = None
) -> List[Dict[str, Any]]:
    """
    Get list of overdue action items.

    Args:
        assigned_to: Filter by assignee (optional)
        days_overdue: Minimum days overdue (optional)

    Returns:
        List of overdue action items
    """
    db = _get_firestore_client()

    # Query pending tasks
    query = db.collection("follow_up_tasks").where("status", "==", "pending")

    if assigned_to:
        query = query.where("assigned_to", "==", assigned_to)

    overdue_items = []
    now = datetime.datetime.now()

    for doc in query.stream():
        item = doc.to_dict()
        item["id"] = doc.id

        # Check if overdue
        if item.get("deadline"):
            try:
                deadline = datetime.datetime.fromisoformat(item["deadline"])
                if deadline < now:
                    item["days_overdue"] = (now - deadline).days

                    # Apply days_overdue filter
                    if days_overdue is None or item["days_overdue"] >= days_overdue:
                        overdue_items.append(item)
            except:
                pass

    # Sort by urgency
    overdue_items.sort(key=lambda x: x.get("urgency_score", 0), reverse=True)

    return overdue_items


def send_reminder(
    task_id: str,
    reminder_type: str = "gentle",
    custom_message: str = None
) -> Dict[str, Any]:
    """
    Send reminder for an action item.

    Args:
        task_id: ID of the action item
        reminder_type: "gentle", "firm", "urgent"
        custom_message: Optional custom message

    Returns:
        Reminder details
    """
    db = _get_firestore_client()

    # Get task
    doc = db.collection("follow_up_tasks").document(task_id).get()
    if not doc.exists:
        return {"error": "Task not found"}

    task = doc.to_dict()

    # Generate reminder message
    if custom_message:
        message = custom_message
    else:
        if reminder_type == "gentle":
            tone = "Just a friendly reminder about this action item."
        elif reminder_type == "firm":
            tone = "This item requires your attention."
        else:  # urgent
            tone = "URGENT: This item is significantly overdue."

        message = f"""
{tone}

Action Item: {task.get('description', 'N/A')}
Deadline: {task.get('deadline', 'No deadline')}
Priority: {task.get('priority', 'medium')}
"""

    # Log reminder
    db.collection("follow_up_tasks").document(task_id).update({
        "last_reminder": datetime.datetime.now().isoformat(),
        "reminder_count": firestore.Increment(1)
    })

    return {
        "task_id": task_id,
        "reminder_type": reminder_type,
        "message": message,
        "sent_to": task.get("assigned_to", "unassigned"),
        "sent_at": datetime.datetime.now().isoformat()
    }


def generate_productivity_report(
    user_email: str,
    time_range: str = "last_7_days"
) -> Dict[str, Any]:
    """
    Generate productivity report for a user.

    Args:
        user_email: User's email address
        time_range: "last_7_days", "last_30_days", "last_quarter"

    Returns:
        Productivity analytics
    """
    db = _get_firestore_client()

    # Calculate date range
    if time_range == "last_7_days":
        start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    elif time_range == "last_30_days":
        start_date = datetime.datetime.now() - datetime.timedelta(days=30)
    else:  # last_quarter
        start_date = datetime.datetime.now() - datetime.timedelta(days=90)

    # Query tasks
    query = db.collection("follow_up_tasks").where("assigned_to", "==", user_email)

    total_tasks = 0
    completed_tasks = 0
    overdue_tasks = 0
    avg_completion_time = []

    for doc in query.stream():
        task = doc.to_dict()

        # Check if in time range
        try:
            created_at = datetime.datetime.fromisoformat(task.get("created_at", ""))
            if created_at < start_date:
                continue
        except:
            continue

        total_tasks += 1

        if task.get("status") == "completed":
            completed_tasks += 1

            # Calculate completion time
            try:
                completed_at = datetime.datetime.fromisoformat(task.get("completed_at", ""))
                completion_time = (completed_at - created_at).days
                avg_completion_time.append(completion_time)
            except:
                pass

        # Check if overdue
        if task.get("deadline") and task.get("status") != "completed":
            try:
                deadline = datetime.datetime.fromisoformat(task["deadline"])
                if deadline < datetime.datetime.now():
                    overdue_tasks += 1
            except:
                pass

    report = {
        "user": user_email,
        "time_range": time_range,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "pending_tasks": total_tasks - completed_tasks,
        "overdue_tasks": overdue_tasks,
        "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
        "avg_completion_days": sum(avg_completion_time) / len(avg_completion_time) if avg_completion_time else 0,
        "recommendations": []
    }

    # Generate recommendations
    if report["completion_rate"] < 60:
        report["recommendations"].append("Completion rate is below 60%. Consider reviewing task priorities and deadlines.")

    if overdue_tasks > total_tasks * 0.2:
        report["recommendations"].append("More than 20% of tasks are overdue. Consider rescheduling or delegating.")

    if report["avg_completion_days"] > 7:
        report["recommendations"].append("Tasks are taking longer than a week to complete. Break down into smaller items.")

    return report


def check_email_follow_ups(
    days_without_response: int = 3,
    email_filter: str = None
) -> List[Dict[str, Any]]:
    """
    Check for emails that need follow-up.

    Args:
        days_without_response: Days since email was sent
        email_filter: Optional email filter (e.g., "from:client@company.com")

    Returns:
        List of emails needing follow-up
    """
    # In production, query Gmail data store for sent emails
    # Check if responses were received

    # For demo, return mock data
    follow_ups_needed = [
        {
            "email_id": "demo-email-1",
            "subject": "Project proposal",
            "sent_to": "client@prospectcorp.com",
            "sent_at": (datetime.datetime.now() - datetime.timedelta(days=5)).isoformat(),
            "days_since_sent": 5,
            "has_response": False,
            "suggested_action": "Send polite follow-up"
        }
    ]

    return follow_ups_needed


# Create the agent - ADK automatically wraps functions as FunctionTools
root_agent = Agent(
    name="followup_agent",
    model="gemini-2.5-pro",
    instruction="You are a follow-up and task management agent. Help users create meeting summaries with action items, track task completion, send email reminders, and generate productivity reports. Use available tools to manage action items in Firestore and keep users on top of their commitments. Prioritize overdue items and provide proactive recommendations.",
    description="Automated follow-up and task management assistant",
    tools=[create_meeting_followup, track_action_item, get_overdue_tasks, send_reminder, generate_productivity_report, check_email_follow_ups]
)
