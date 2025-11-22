"""
Email Agent - Handles email summarization, drafting, and management
Part of Gemini Enterprise Demo #3
"""

import os
from google.adk.agents import Agent
from google.cloud import discoveryengine_v1
from typing import List, Dict, Any
import datetime

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = os.environ.get("LOCATION", "us-central1")
GMAIL_DATASTORE = f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-gmail-datastore"


# Helper functions
def _build_time_query(time_range: str) -> str:
    """Build time-based query filter"""
    today = datetime.datetime.now()

    if time_range == "today":
        return f"after:{today.strftime('%Y/%m/%d')}"
    elif time_range == "this_week":
        week_start = today - datetime.timedelta(days=today.weekday())
        return f"after:{week_start.strftime('%Y/%m/%d')}"
    elif time_range == "last_24h":
        yesterday = today - datetime.timedelta(days=1)
        return f"after:{yesterday.strftime('%Y/%m/%d')}"
    return ""


def _parse_email(search_result) -> Dict[str, Any]:
    """Parse search result into email object"""
    doc = search_result.document
    return {
        "id": doc.id,
        "from": doc.derived_struct_data.get("from", ""),
        "subject": doc.derived_struct_data.get("subject", ""),
        "snippet": doc.derived_struct_data.get("snippet", ""),
        "date": doc.derived_struct_data.get("date", ""),
        "labels": doc.derived_struct_data.get("labels", [])
    }


def _filter_urgent(emails: List[Dict]) -> List[Dict]:
    """Filter urgent emails"""
    urgent_keywords = ["urgent", "asap", "deadline", "important", "critical"]
    return [
        e for e in emails
        if any(kw in e["subject"].lower() or kw in e["snippet"].lower()
               for kw in urgent_keywords)
    ]


def _filter_important(emails: List[Dict]) -> List[Dict]:
    """Filter important but not urgent emails"""
    important_senders = ["ceo@", "board@", "executives@"]
    return [
        e for e in emails
        if any(sender in e["from"].lower() for sender in important_senders)
        and e not in _filter_urgent(emails)
    ]


def _filter_can_wait(emails: List[Dict]) -> List[Dict]:
    """Filter emails that can wait"""
    all_emails = set(e["id"] for e in emails)
    urgent_ids = set(e["id"] for e in _filter_urgent(emails))
    important_ids = set(e["id"] for e in _filter_important(emails))

    can_wait_ids = all_emails - urgent_ids - important_ids
    return [e for e in emails if e["id"] in can_wait_ids]


def _generate_recommendations(emails: List[Dict]) -> List[str]:
    """Generate action recommendations"""
    recommendations = []

    urgent = _filter_urgent(emails)
    if urgent:
        recommendations.append(f"Respond to {len(urgent)} urgent email(s) first")

    meeting_invites = [e for e in emails if "invite" in e["subject"].lower()]
    if meeting_invites:
        recommendations.append(f"Accept/decline {len(meeting_invites)} meeting invite(s)")

    return recommendations


def _get_email_context(email_id: str) -> Dict[str, Any]:
    """Retrieve full email context including thread"""
    # In production, this would query the Gmail API
    # For demo, return mock data
    return {
        "id": email_id,
        "from": "sender@example.com",
        "subject": "Re: Project Update",
        "body": "Email body content...",
        "thread_context": "Previous email context..."
    }


# Tool functions - These are automatically wrapped by ADK as FunctionTools
def summarize_emails(time_range: str = "today") -> Dict[str, Any]:
    """
    Summarize unread emails and prioritize by importance.

    Args:
        time_range: "today", "this_week", "last_24h"

    Returns:
        Summary with priorities, urgent items, and recommended actions
    """
    # Query Gemini Enterprise data store
    client = discoveryengine_v1.SearchServiceClient()

    # Build search query
    query = _build_time_query(time_range)

    request = discoveryengine_v1.SearchRequest(
        serving_config=f"{GMAIL_DATASTORE}/servingConfigs/default_search",
        query=query,
        page_size=50
    )

    response = client.search(request)

    # Analyze emails with Gemini
    emails = [_parse_email(result) for result in response.results]

    summary = {
        "total_unread": len(emails),
        "urgent": _filter_urgent(emails),
        "important": _filter_important(emails),
        "can_wait": _filter_can_wait(emails),
        "recommended_actions": _generate_recommendations(emails)
    }

    return summary


def draft_email_response(
    email_id: str,
    tone: str = "professional",
    key_points: List[str] = None
) -> Dict[str, Any]:
    """
    Generate a draft email response based on context.

    Args:
        email_id: The email to respond to
        tone: "professional", "casual", "formal"
        key_points: Optional list of points to include

    Returns:
        Dict containing the draft email and context
    """
    # Retrieve email context
    email_context = _get_email_context(email_id)

    # Return context for the agent's LLM to generate the draft
    return {
        "status": "context_retrieved",
        "email_context": email_context,
        "tone": tone,
        "key_points": key_points or [],
        "instruction": f"Please draft a {tone} email response addressing the key points provided."
    }


def search_emails(
    query: str,
    date_range: str = None,
    from_sender: str = None,
    has_attachment: bool = None
) -> List[Dict[str, Any]]:
    """
    Search emails with natural language query.

    Args:
        query: Natural language search query
        date_range: Optional date filter
        from_sender: Optional sender filter
        has_attachment: Optional attachment filter

    Returns:
        List of matching emails
    """
    client = discoveryengine_v1.SearchServiceClient()

    # Build enhanced query with filters
    enhanced_query = query
    if date_range:
        enhanced_query += f" after:{date_range}"
    if from_sender:
        enhanced_query += f" from:{from_sender}"
    if has_attachment:
        enhanced_query += " has:attachment"

    request = discoveryengine_v1.SearchRequest(
        serving_config=f"{GMAIL_DATASTORE}/servingConfigs/default_search",
        query=enhanced_query,
        page_size=20
    )

    response = client.search(request)

    results = [_parse_email(result) for result in response.results]
    return results


def categorize_and_label(email_ids: List[str]) -> Dict[str, List[str]]:
    """
    Automatically categorize and label emails.

    Args:
        email_ids: List of email IDs to categorize

    Returns:
        Dictionary mapping categories to email IDs
    """
    categories = {
        "urgent_action_required": [],
        "review_requested": [],
        "informational": [],
        "meeting_invites": [],
        "follow_ups": []
    }

    for email_id in email_ids:
        email = _get_email_context(email_id)

        # Categorization using simple heuristics
        subject_lower = email['subject'].lower()
        if any(kw in subject_lower for kw in ["urgent", "asap", "deadline"]):
            categories["urgent_action_required"].append(email_id)
        elif "review" in subject_lower:
            categories["review_requested"].append(email_id)
        elif "meeting" in subject_lower or "invite" in subject_lower:
            categories["meeting_invites"].append(email_id)
        elif "follow" in subject_lower:
            categories["follow_ups"].append(email_id)
        else:
            categories["informational"].append(email_id)

    return categories


# Create the agent - ADK automatically wraps functions as FunctionTools
root_agent = Agent(
    name="email_agent",
    model="gemini-2.5-pro",
    instruction="You are an email management agent. Help users summarize emails, draft responses, search their inbox, and categorize messages. Use the available tools to query Gmail data and generate intelligent responses. Always prioritize urgent emails and provide actionable recommendations.",
    description="AI-powered email management assistant that helps users efficiently manage their inbox through intelligent email summarization, automated prioritization, smart response drafting, and context-aware categorization. Integrates with Gmail data to provide actionable insights and recommendations.",
    tools=[summarize_emails, draft_email_response, search_emails, categorize_and_label]
)
