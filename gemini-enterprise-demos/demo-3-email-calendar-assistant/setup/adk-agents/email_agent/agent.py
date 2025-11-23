"""
Email Agent - Handles email summarization, drafting, and management
Part of Gemini Enterprise Demo #3 - Using Gmail API directly
"""

import os
from google.adk.agents import Agent
from googleapiclient.discovery import build
from google.auth import default
from google.oauth2 import service_account
from typing import List, Dict, Any
import datetime
import base64

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = os.environ.get("LOCATION", "us-central1")

# Gmail API scopes
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]


def _get_gmail_service(user_email: str = None):
    """
    Get authenticated Gmail API service with domain-wide delegation.

    Args:
        user_email: Email of user to impersonate. If None, tries to use default credentials.

    Returns:
        Gmail API service object
    """
    try:
        # Get default credentials (service account in Vertex AI)
        credentials, project = default()

        # If we have a user email and credentials support delegation, impersonate the user
        if user_email and hasattr(credentials, 'with_subject'):
            # This is a service account - use domain-wide delegation
            credentials = credentials.with_subject(user_email)
            credentials = credentials.with_scopes(GMAIL_SCOPES)
        elif hasattr(credentials, 'with_scopes'):
            # Add required scopes
            credentials = credentials.with_scopes(GMAIL_SCOPES)

        service = build('gmail', 'v1', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error getting Gmail service: {e}")
        # Return a service with default credentials as fallback
        credentials, _ = default()
        return build('gmail', 'v1', credentials=credentials)


def _parse_email(message) -> Dict[str, Any]:
    """Parse Gmail API message into email object"""
    headers = message.get('payload', {}).get('headers', [])

    # Extract headers
    subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
    from_addr = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
    date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

    # Get snippet
    snippet = message.get('snippet', '')

    # Get labels
    labels = message.get('labelIds', [])

    return {
        "id": message['id'],
        "from": from_addr,
        "subject": subject,
        "snippet": snippet,
        "date": date,
        "labels": labels,
        "thread_id": message.get('threadId', '')
    }


def _build_time_query(time_range: str) -> str:
    """Build time-based Gmail query filter"""
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


# Tool functions - These are automatically wrapped by ADK as FunctionTools
def check_agent_health() -> Dict[str, Any]:
    """
    Check agent health and authentication status.

    Returns:
        Diagnostic information about the agent's configuration
    """
    diagnostics = {
        "agent_name": "email_agent",
        "status": "checking",
        "checks": {}
    }

    try:
        # Check if we can get default credentials
        credentials, project = default()
        diagnostics["checks"]["credentials"] = {
            "status": "✓ Found",
            "project": project,
            "type": type(credentials).__name__
        }

        # Check if credentials support delegation
        if hasattr(credentials, 'with_subject'):
            diagnostics["checks"]["delegation_support"] = {
                "status": "✓ Service account credentials support domain-wide delegation",
                "note": "Can impersonate users if delegation is configured in Workspace Admin"
            }
        else:
            diagnostics["checks"]["delegation_support"] = {
                "status": "⚠ Credentials do not support delegation",
                "note": "This is expected if running locally with user credentials"
            }

        # Check Gmail API accessibility
        try:
            test_service = _get_gmail_service()
            diagnostics["checks"]["gmail_api"] = {
                "status": "✓ Gmail API client created",
                "note": "API is accessible, but user impersonation may still fail without delegation"
            }
        except Exception as api_error:
            diagnostics["checks"]["gmail_api"] = {
                "status": f"✗ Error: {str(api_error)}",
                "note": "Gmail API may not be enabled or accessible"
            }

        diagnostics["status"] = "healthy"
        diagnostics["recommendation"] = "Agent is ready. For Gemini Enterprise Plus: pass user_email parameter to tool functions."

    except Exception as e:
        diagnostics["status"] = "unhealthy"
        diagnostics["error"] = str(e)
        diagnostics["recommendation"] = "Check Vertex AI service account has Gmail API access"

    return diagnostics


def summarize_emails(time_range: str = "today", user_email: str = None) -> Dict[str, Any]:
    """
    Summarize unread emails and prioritize by importance.

    Args:
        time_range: "today", "this_week", "last_24h"
        user_email: Email address of user to query (optional, for domain-wide delegation)

    Returns:
        Summary with priorities, urgent items, and recommended actions
    """
    try:
        service = _get_gmail_service(user_email=user_email)

        # Build query
        query = f"is:unread {_build_time_query(time_range)}"

        # Search emails
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=50
        ).execute()

        messages = results.get('messages', [])

        # Get full message details
        emails = []
        for msg in messages[:50]:  # Limit to 50
            full_msg = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            emails.append(_parse_email(full_msg))

        summary = {
            "total_unread": len(emails),
            "urgent": _filter_urgent(emails),
            "important": _filter_important(emails),
            "can_wait": _filter_can_wait(emails),
            "recommended_actions": _generate_recommendations(emails)
        }

        return summary

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in summarize_emails: {error_details}")
        return {
            "error": str(e),
            "error_type": type(e).__name__,
            "message": f"Failed to access Gmail. Error: {str(e)}. This agent needs: (1) Service account with domain-wide delegation, (2) Gmail API enabled, (3) User email to impersonate. Currently user_email={user_email}",
            "total_unread": 0,
            "urgent": [],
            "important": [],
            "can_wait": [],
            "recommended_actions": [],
            "troubleshooting": "Check Vertex AI service account has domain-wide delegation in Google Workspace Admin Console with Gmail API scopes"
        }


def draft_email_response(
    email_id: str,
    tone: str = "professional",
    key_points: List[str] = None,
    user_email: str = None
) -> Dict[str, Any]:
    """
    Generate a draft email response based on context.

    Args:
        email_id: The email to respond to
        tone: "professional", "casual", "formal"
        key_points: Optional list of points to include
        user_email: Email address of user to query (optional, for domain-wide delegation)

    Returns:
        Dict containing the draft email and context
    """
    try:
        service = _get_gmail_service(user_email=user_email)

        # Get email details
        message = service.users().messages().get(
            userId='me',
            id=email_id,
            format='full'
        ).execute()

        email = _parse_email(message)

        # Get thread for context
        thread = service.users().threads().get(
            userId='me',
            id=email['thread_id']
        ).execute()

        thread_messages = [_parse_email(msg) for msg in thread.get('messages', [])]

        return {
            "status": "context_retrieved",
            "email_context": email,
            "thread_context": thread_messages,
            "tone": tone,
            "key_points": key_points or [],
            "instruction": f"Please draft a {tone} email response addressing the key points provided."
        }

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to retrieve email context"
        }


def search_emails(
    query: str,
    date_range: str = None,
    from_sender: str = None,
    has_attachment: bool = None,
    user_email: str = None
) -> List[Dict[str, Any]]:
    """
    Search emails with natural language query.

    Args:
        query: Natural language search query
        date_range: Optional date filter (YYYY/MM/DD)
        from_sender: Optional sender filter
        has_attachment: Optional attachment filter
        user_email: Email address of user to query (optional, for domain-wide delegation)

    Returns:
        List of matching emails
    """
    try:
        service = _get_gmail_service(user_email=user_email)

        # Build Gmail query
        gmail_query = query
        if date_range:
            gmail_query += f" after:{date_range}"
        if from_sender:
            gmail_query += f" from:{from_sender}"
        if has_attachment:
            gmail_query += " has:attachment"

        # Search
        results = service.users().messages().list(
            userId='me',
            q=gmail_query,
            maxResults=20
        ).execute()

        messages = results.get('messages', [])

        # Get full details
        emails = []
        for msg in messages:
            full_msg = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            emails.append(_parse_email(full_msg))

        return emails

    except Exception as e:
        return [{
            "error": str(e),
            "message": "Failed to search Gmail"
        }]


def categorize_and_label(email_ids: List[str], user_email: str = None) -> Dict[str, List[str]]:
    """
    Automatically categorize and label emails.

    Args:
        email_ids: List of email IDs to categorize
        user_email: Email address of user to query (optional, for domain-wide delegation)

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

    try:
        service = _get_gmail_service(user_email=user_email)

        for email_id in email_ids:
            message = service.users().messages().get(
                userId='me',
                id=email_id,
                format='full'
            ).execute()

            email = _parse_email(message)
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

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to categorize emails"
        }


# Create the agent - ADK automatically wraps functions as FunctionTools
root_agent = Agent(
    name="email_agent",
    model="gemini-2.5-pro",
    instruction="You are an email management agent. Help users summarize emails, draft responses, search their inbox, and categorize messages. Use the available tools to query Gmail data directly and generate intelligent responses. Always prioritize urgent emails and provide actionable recommendations. If a tool returns an error, explain the error to the user in a helpful way.",
    description="AI-powered email management assistant that helps users efficiently manage their inbox through intelligent email summarization, automated prioritization, smart response drafting, and context-aware categorization. Uses Gmail API for direct access to email data.",
    tools=[check_agent_health, summarize_emails, draft_email_response, search_emails, categorize_and_label]
)
