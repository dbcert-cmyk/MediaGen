"""
Meeting Prep Agent - Automatically prepares for upcoming meetings
Part of Gemini Enterprise Demo #3
"""

import os
from google.adk.agents import Agent
from google.cloud import discoveryengine_v1, storage
from typing import List, Dict, Any
import datetime
from dateutil import parser as date_parser

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = os.environ.get("LOCATION", "us-central1")
GMAIL_DATASTORE = f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-gmail-datastore"
DRIVE_DATASTORE = f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-drive-datastore"
CALENDAR_DATASTORE = f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-calendar-datastore"


# Helper functions
def _get_meeting_details(meeting_id: str) -> Dict[str, Any]:
    """Retrieve meeting details from Calendar data store"""
    # In production, query Calendar data store
    # For demo, return mock data
    return {
        "id": meeting_id,
        "title": "Client Demo - Enterprise Features",
        "start": "2025-11-18T14:00:00-08:00",
        "end": "2025-11-18T15:00:00-08:00",
        "duration": 60,
        "attendees": [
            "demo-user@company.com",
            "maria.rodriguez@company.com",
            "client@prospectcorp.com"
        ],
        "organizer": "maria.rodriguez@company.com",
        "description": "Demo of enterprise AI capabilities"
    }


def _find_related_emails(meeting: Dict) -> List[Dict]:
    """Find emails related to the meeting"""
    client = discoveryengine_v1.SearchServiceClient()

    # Extract keywords from meeting title and attendees
    keywords = meeting["title"].split()
    attendee_emails = [a.split("@")[0] for a in meeting.get("attendees", [])]

    # Search email data store
    query = " OR ".join(keywords + attendee_emails)

    request = discoveryengine_v1.SearchRequest(
        serving_config=f"{GMAIL_DATASTORE}/servingConfigs/default_search",
        query=query,
        page_size=10
    )

    response = client.search(request)

    emails = []
    for result in response.results:
        doc = result.document
        emails.append({
            "id": doc.id,
            "from": doc.derived_struct_data.get("from", ""),
            "subject": doc.derived_struct_data.get("subject", ""),
            "date": doc.derived_struct_data.get("date", ""),
            "snippet": doc.derived_struct_data.get("snippet", "")
        })

    return emails


def _find_relevant_documents(meeting: Dict) -> List[Dict]:
    """Find documents related to the meeting"""
    client = discoveryengine_v1.SearchServiceClient()

    # Search Drive data store
    query = meeting["title"]

    request = discoveryengine_v1.SearchRequest(
        serving_config=f"{DRIVE_DATASTORE}/servingConfigs/default_search",
        query=query,
        page_size=5
    )

    response = client.search(request)

    documents = []
    for result in response.results:
        doc = result.document
        documents.append({
            "id": doc.id,
            "name": doc.derived_struct_data.get("name", ""),
            "type": doc.derived_struct_data.get("mimeType", ""),
            "url": doc.derived_struct_data.get("webViewLink", ""),
            "modified": doc.derived_struct_data.get("modifiedTime", "")
        })

    return documents


def _get_participant_context(meeting: Dict) -> List[Dict]:
    """Get context about meeting participants"""
    participants = []

    for attendee in meeting.get("attendees", []):
        # Search for recent interactions with this person
        context = {
            "email": attendee,
            "recent_meetings": _get_recent_meetings_with(attendee),
            "recent_emails": _get_recent_emails_with(attendee),
            "role": _infer_role(attendee)
        }
        participants.append(context)

    return participants


def _generate_agenda(meeting: Dict) -> str:
    """Generate suggested agenda based on context"""
    # Return agenda template for the agent's LLM to fill in
    return f"""
Generate a meeting agenda for:

Title: {meeting['title']}
Duration: {meeting.get('duration', 60)} minutes
Description: {meeting.get('description', 'N/A')}

Based on the title and description, create a time-boxed agenda with:
1. Opening (5 min)
2. Main topics (with time allocations)
3. Q&A
4. Next steps (5 min)

Be specific and actionable.
"""


def _generate_talking_points(meeting: Dict) -> List[str]:
    """Generate suggested talking points"""
    # Return basic talking points - agent's LLM can expand these
    return [
        f"Key topics for {meeting['title']}",
        "Review meeting objectives",
        "Discuss action items",
        "Confirm next steps"
    ]


def _predict_questions(meeting: Dict) -> List[str]:
    """Predict questions that might be asked"""
    # Return basic question prompts
    return [
        f"Common questions about {meeting['title']}",
        "Technical implementation questions",
        "Timeline and resource questions"
    ]


def _get_previous_action_items(meeting: Dict) -> List[Dict]:
    """Get action items from previous related meetings"""
    # In production, search for previous meetings with same participants
    # and extract action items from notes
    return []


def _classify_meeting_type(title: str) -> str:
    """Classify meeting type from title"""
    title_lower = title.lower()

    if any(kw in title_lower for kw in ["1:1", "1-on-1", "one-on-one"]):
        return "one-on-one"
    elif any(kw in title_lower for kw in ["standup", "daily", "scrum"]):
        return "daily_standup"
    elif any(kw in title_lower for kw in ["demo", "presentation", "showcase"]):
        return "demo"
    elif any(kw in title_lower for kw in ["planning", "roadmap", "strategy"]):
        return "planning"
    elif any(kw in title_lower for kw in ["review", "retro", "retrospective"]):
        return "review"
    else:
        return "general_discussion"


def _had_agenda(meeting_id: str) -> bool:
    """Check if meeting had an agenda"""
    # In production, check if agenda doc was created in Drive
    return False


def _get_action_items_from_meeting(meeting_id: str) -> List[Dict]:
    """Extract action items from meeting notes"""
    # In production, parse meeting notes document
    return []


def _get_recent_meetings_with(attendee: str) -> List[Dict]:
    """Get recent meetings with specific attendee"""
    return []


def _get_recent_emails_with(attendee: str) -> List[Dict]:
    """Get recent email exchanges with attendee"""
    return []


def _infer_role(email: str) -> str:
    """Infer person's role from email domain and name"""
    if "client" in email or "prospect" in email:
        return "External - Client/Prospect"
    elif any(title in email for title in ["ceo", "cto", "vp"]):
        return "Executive"
    else:
        return "Team Member"


# Tool functions - These are automatically wrapped by ADK as FunctionTools
def prepare_for_meeting(
    meeting_id: str,
    prep_time_hours: int = 24
) -> Dict[str, Any]:
    """
    Prepare comprehensive brief for a meeting.

    Args:
        meeting_id: Calendar event ID
        prep_time_hours: How many hours before meeting to prepare

    Returns:
        Complete meeting prep package
    """
    # Get meeting details
    meeting = _get_meeting_details(meeting_id)

    # Gather context from multiple sources
    prep_package = {
        "meeting_info": meeting,
        "related_emails": _find_related_emails(meeting),
        "relevant_documents": _find_relevant_documents(meeting),
        "participant_context": _get_participant_context(meeting),
        "suggested_agenda": _generate_agenda(meeting),
        "talking_points": _generate_talking_points(meeting),
        "potential_questions": _predict_questions(meeting),
        "action_items_from_last_time": _get_previous_action_items(meeting)
    }

    return prep_package


def create_meeting_agenda(
    meeting_title: str,
    duration_minutes: int,
    participants: List[str],
    objectives: List[str] = None
) -> str:
    """
    Create a structured meeting agenda.

    Args:
        meeting_title: Title of the meeting
        duration_minutes: Meeting duration
        participants: List of attendee emails
        objectives: Optional list of meeting objectives

    Returns:
        Formatted agenda document
    """
    # Analyze meeting type and participants
    meeting_type = _classify_meeting_type(meeting_title)

    # Generate time-boxed agenda template
    agenda_template = f"""
Create a professional meeting agenda for:

Meeting: {meeting_title}
Duration: {duration_minutes} minutes
Participants: {len(participants)} people
Type: {meeting_type}

Objectives:
{chr(10).join(f'- {obj}' for obj in (objectives or ['Discuss and align on key topics']))}

Create a time-boxed agenda with:
1. Welcome and context setting
2. Main discussion topics (allocate time proportionally)
3. Decisions to be made
4. Action items and next steps
5. Wrap-up

Make it practical and actionable.
"""

    return agenda_template


def analyze_meeting_effectiveness(
    meeting_id: str
) -> Dict[str, Any]:
    """
    Analyze a past meeting for effectiveness.

    Args:
        meeting_id: ID of past meeting to analyze

    Returns:
        Analysis with improvement suggestions
    """
    meeting = _get_meeting_details(meeting_id)

    analysis = {
        "meeting_info": {
            "title": meeting["title"],
            "duration_planned": meeting["duration"],
            "attendees_count": len(meeting.get("attendees", []))
        },
        "effectiveness_score": 0,
        "strengths": [],
        "areas_for_improvement": [],
        "recommendations": []
    }

    # Check if agenda was created
    if _had_agenda(meeting_id):
        analysis["strengths"].append("Had a structured agenda")
        analysis["effectiveness_score"] += 20
    else:
        analysis["areas_for_improvement"].append("No formal agenda")
        analysis["recommendations"].append("Create agenda before next meeting")

    # Check if action items were documented
    action_items = _get_action_items_from_meeting(meeting_id)
    if action_items:
        analysis["strengths"].append(f"Documented {len(action_items)} action items")
        analysis["effectiveness_score"] += 25
    else:
        analysis["areas_for_improvement"].append("No action items documented")
        analysis["recommendations"].append("Use meeting notes template to capture actions")

    # Check follow-up rate
    if action_items:
        completed = len([a for a in action_items if a.get("status") == "completed"])
        completion_rate = (completed / len(action_items)) * 100
        analysis["action_item_completion_rate"] = completion_rate

        if completion_rate >= 80:
            analysis["strengths"].append(f"High action item completion ({completion_rate}%)")
            analysis["effectiveness_score"] += 30
        else:
            analysis["areas_for_improvement"].append(f"Low completion rate ({completion_rate}%)")
            analysis["recommendations"].append("Set clearer owners and deadlines")

    # Check meeting duration adherence
    if meeting.get("ended_on_time"):
        analysis["strengths"].append("Stayed within allocated time")
        analysis["effectiveness_score"] += 15
    else:
        analysis["areas_for_improvement"].append("Ran over time")
        analysis["recommendations"].append("Better time management or longer duration")

    # Check participant engagement
    if meeting.get("participation_rate", 0) >= 75:
        analysis["strengths"].append("High participant engagement")
        analysis["effectiveness_score"] += 10

    return analysis


def schedule_prep_time(
    meeting_id: str,
    prep_duration_minutes: int = 30,
    hours_before_meeting: int = 2
) -> Dict[str, Any]:
    """
    Block calendar time for meeting prep.

    Args:
        meeting_id: Meeting to prep for
        prep_duration_minutes: How long prep should take
        hours_before_meeting: When to schedule prep

    Returns:
        Created prep block details
    """
    meeting = _get_meeting_details(meeting_id)
    meeting_start = date_parser.parse(meeting["start"])

    # Calculate prep time
    prep_start = meeting_start - datetime.timedelta(hours=hours_before_meeting)
    prep_end = prep_start + datetime.timedelta(minutes=prep_duration_minutes)

    prep_block = {
        "title": f"📝 Prep: {meeting['title']}",
        "start": prep_start.isoformat(),
        "end": prep_end.isoformat(),
        "description": f"Preparation time for {meeting['title']}\n\nTasks:\n- Review related materials\n- Prepare talking points\n- Review participant backgrounds",
        "attendees": [meeting.get("organizer", "")],
        "color": "yellow",  # Distinguish prep blocks visually
        "related_meeting_id": meeting_id
    }

    return prep_block


# Create the agent - ADK automatically wraps functions as FunctionTools
root_agent = Agent(
    name="meeting_prep_agent",
    display_name="Meeting Preparation Agent",
    model="gemini-2.5-pro",
    instruction="You are a meeting preparation agent. Help users prepare for upcoming meetings by gathering related emails and documents, creating agendas, generating talking points, and providing participant context. Use available tools to search across Gmail, Calendar, and Drive data stores. Ensure users are well-prepared and confident for every meeting.",
    description="Comprehensive meeting preparation assistant that ensures productive meetings by automatically gathering relevant context from emails and documents, creating structured agendas, generating talking points, and providing participant insights. Searches across Gmail, Calendar, and Drive to deliver complete preparation materials.",
    tools=[prepare_for_meeting, create_meeting_agenda, analyze_meeting_effectiveness, schedule_prep_time]
)
