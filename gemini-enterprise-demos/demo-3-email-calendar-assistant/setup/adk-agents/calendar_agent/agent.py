"""
Calendar Agent - Handles meeting scheduling and calendar optimization
Part of Gemini Enterprise Demo #3 - Using Google Calendar API directly
"""

import os
from google.adk.agents import Agent
from googleapiclient.discovery import build
from google.auth import default
from google.oauth2 import service_account
from typing import List, Dict, Any, Optional
import datetime
from dateutil import parser as date_parser

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = os.environ.get("LOCATION", "us-central1")

# Calendar API scopes
CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]


def _get_calendar_service(user_email: str = None):
    """
    Get authenticated Google Calendar API service with domain-wide delegation.

    Args:
        user_email: Email of user to impersonate. If None, tries to use default credentials.

    Returns:
        Calendar API service object
    """
    try:
        # Get default credentials (service account in Vertex AI)
        credentials, project = default()

        # If we have a user email and credentials support delegation, impersonate the user
        if user_email and hasattr(credentials, 'with_subject'):
            # This is a service account - use domain-wide delegation
            credentials = credentials.with_subject(user_email)
            credentials = credentials.with_scopes(CALENDAR_SCOPES)
        elif hasattr(credentials, 'with_scopes'):
            # Add required scopes
            credentials = credentials.with_scopes(CALENDAR_SCOPES)

        service = build('calendar', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"Error getting Calendar service: {e}")
        # Return a service with default credentials as fallback
        credentials, _ = default()
        return build('calendar', 'v3', credentials=credentials)


def _parse_calendar_event(event) -> Dict[str, Any]:
    """Parse Google Calendar API event into standard format"""
    return {
        "id": event.get('id', ''),
        "title": event.get('summary', 'No Title'),
        "start": event.get('start', {}).get('dateTime', event.get('start', {}).get('date', '')),
        "end": event.get('end', {}).get('dateTime', event.get('end', {}).get('date', '')),
        "attendees": [a.get('email', '') for a in event.get('attendees', [])],
        "location": event.get('location', ''),
        "description": event.get('description', ''),
        "status": event.get('status', 'confirmed')
    }


def _get_calendar_events(user_email: str, time_range: str) -> List[Dict]:
    """Query Google Calendar for events"""
    try:
        service = _get_calendar_service(user_email=user_email)

        # Parse time range
        if time_range == "today":
            time_min = datetime.datetime.now().replace(hour=0, minute=0, second=0)
            time_max = time_min + datetime.timedelta(days=1)
        elif time_range == "this_week":
            time_min = datetime.datetime.now()
            time_max = time_min + datetime.timedelta(days=7)
        elif time_range == "next_30_days":
            time_min = datetime.datetime.now()
            time_max = time_min + datetime.timedelta(days=30)
        else:  # next_7_days
            time_min = datetime.datetime.now()
            time_max = time_min + datetime.timedelta(days=7)

        # Query calendar
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min.isoformat() + 'Z',
            timeMax=time_max.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        return [_parse_calendar_event(e) for e in events]

    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        return []


def _get_attendee_availability(
    attendees: List[str],
    date_range: str
) -> Dict[str, List[Dict]]:
    """Get calendar availability for all attendees"""
    availability = {}
    for attendee in attendees:
        availability[attendee] = _get_calendar_events(attendee, date_range)
    return availability


def _find_free_slots(
    availability: Dict[str, List[Dict]],
    duration_minutes: int,
    preferred_time_range: str
) -> List[Dict[str, Any]]:
    """Find time slots when all attendees are free"""
    free_slots = []

    start_hour, end_hour = _get_time_range_hours(preferred_time_range)

    # Check next 7 days
    for day_offset in range(7):
        check_date = datetime.datetime.now() + datetime.timedelta(days=day_offset)

        # Skip weekends
        if check_date.weekday() >= 5:
            continue

        # Check each hour slot
        for hour in range(start_hour, end_hour):
            slot_start = check_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            slot_end = slot_start + datetime.timedelta(minutes=duration_minutes)

            # Check if all attendees are free
            if _all_attendees_free(availability, slot_start, slot_end):
                free_slots.append({
                    "start": slot_start.isoformat(),
                    "end": slot_end.isoformat(),
                    "day_of_week": check_date.strftime("%A")
                })

    return free_slots


def _rank_time_slots(
    slots: List[Dict],
    attendees: List[str]
) -> List[Dict[str, Any]]:
    """Rank time slots by preference score"""
    for slot in slots:
        score = 0

        # Prefer mid-morning or mid-afternoon
        slot_time = date_parser.parse(slot["start"])
        hour = slot_time.hour
        if 10 <= hour <= 11 or 14 <= hour <= 15:
            score += 10

        # Prefer Tuesday-Thursday
        if slot_time.weekday() in [1, 2, 3]:
            score += 5

        # Avoid Monday mornings and Friday afternoons
        if slot_time.weekday() == 0 and hour < 11:
            score -= 5
        if slot_time.weekday() == 4 and hour > 14:
            score -= 5

        slot["score"] = score

    return sorted(slots, key=lambda x: x["score"], reverse=True)


def _calculate_end_time(start_time: str, duration_minutes: int) -> str:
    """Calculate meeting end time"""
    start = date_parser.parse(start_time)
    end = start + datetime.timedelta(minutes=duration_minutes)
    return end.isoformat()


def _calculate_meeting_hours(events: List[Dict]) -> float:
    """Calculate total hours in meetings"""
    total_minutes = sum(
        (date_parser.parse(e["end"]) - date_parser.parse(e["start"])).seconds / 60
        for e in events if e.get("start") and e.get("end")
    )
    return round(total_minutes / 60, 1)


def _find_back_to_back(events: List[Dict]) -> List[tuple]:
    """Find back-to-back meetings with no breaks"""
    back_to_back = []
    for i in range(len(events) - 1):
        if events[i]["end"] == events[i+1]["start"]:
            back_to_back.append((events[i], events[i+1]))
    return back_to_back


def _find_overload_days(events: List[Dict]) -> List[str]:
    """Find days with excessive meeting time"""
    day_hours = {}
    for event in events:
        if event.get("start") and event.get("end"):
            day = date_parser.parse(event["start"]).date().isoformat()
            duration = (date_parser.parse(event["end"]) - date_parser.parse(event["start"])).seconds / 3600
            day_hours[day] = day_hours.get(day, 0) + duration

    return [day for day, hours in day_hours.items() if hours >= 5]


def _find_fragmented_time(events: List[Dict]) -> bool:
    """Detect fragmented time blocks"""
    gaps = []
    for i in range(len(events) - 1):
        gap = (date_parser.parse(events[i+1]["start"]) - date_parser.parse(events[i]["end"])).seconds / 60
        gaps.append(gap)

    # Fragmented if many gaps of 15-45 minutes
    short_gaps = [g for g in gaps if 15 <= g <= 45]
    return len(short_gaps) >= 3


def _suggest_break_times(back_to_back: List[tuple]) -> List[str]:
    """Suggest where to add breaks"""
    return [f"Add 15-min buffer after {b[0]['title']}" for b in back_to_back[:3]]


def _suggest_reschedule(overload_days: List[str]) -> List[str]:
    """Suggest meeting rescheduling"""
    return [f"Move non-critical meetings from {day}" for day in overload_days]


def _assess_prep_needs(event: Dict) -> str:
    """Assess if meeting needs preparation"""
    keywords = ["review", "presentation", "demo", "pitch", "board"]
    if any(kw in event.get("title", "").lower() for kw in keywords):
        return "high"
    return "low"


def _get_meeting_context(event: Dict) -> str:
    """Get context for meeting"""
    return f"Meeting about {event.get('title', 'N/A')}"


def _get_time_range_hours(preferred_time_range: str) -> tuple:
    """Convert time range to hours"""
    if preferred_time_range == "morning":
        return 9, 12
    elif preferred_time_range == "afternoon":
        return 13, 17
    else:  # business_hours
        return 9, 17


def _all_attendees_free(
    availability: Dict[str, List[Dict]],
    slot_start: datetime.datetime,
    slot_end: datetime.datetime
) -> bool:
    """Check if all attendees are free"""
    for attendee, events in availability.items():
        for event in events:
            if event.get("start") and event.get("end"):
                event_start = date_parser.parse(event["start"])
                event_end = date_parser.parse(event["end"])
                if not (slot_end <= event_start or slot_start >= event_end):
                    return False
    return True


def _events_overlap(event1: Dict, event2: Dict) -> bool:
    """Check if two events overlap"""
    if not (event1.get("start") and event1.get("end") and event2.get("start") and event2.get("end")):
        return False

    start1 = date_parser.parse(event1["start"])
    end1 = date_parser.parse(event1["end"])
    start2 = date_parser.parse(event2["start"])
    end2 = date_parser.parse(event2["end"])

    return not (end1 <= start2 or start1 >= end2)


def _assess_conflict_severity(event1: Dict, event2: Dict) -> str:
    """Assess severity of calendar conflict"""
    important_keywords = ["board", "executive", "ceo", "urgent"]
    e1_important = any(kw in event1.get("title", "").lower() for kw in important_keywords)
    e2_important = any(kw in event2.get("title", "").lower() for kw in important_keywords)

    if e1_important or e2_important:
        return "high"
    return "medium"


def _generate_resolution_options(event1: Dict, event2: Dict) -> List[str]:
    """Generate options to resolve conflict"""
    return [
        f"Reschedule '{event1['title']}' to next available slot",
        f"Reschedule '{event2['title']}' to next available slot",
        "Decline one meeting and send regrets"
    ]


# Tool functions - These are automatically wrapped by ADK as FunctionTools
def find_meeting_time(
    attendees: List[str],
    duration_minutes: int,
    preferred_time_range: str = "business_hours",
    date_range: str = "next_7_days"
) -> List[Dict[str, Any]]:
    """
    Find optimal meeting time considering all attendees' calendars.

    Args:
        attendees: List of attendee email addresses
        duration_minutes: Meeting duration in minutes
        preferred_time_range: "business_hours", "morning", "afternoon"
        date_range: "next_7_days", "next_2_weeks", "this_week"

    Returns:
        List of available time slots with scoring
    """
    try:
        # Get availability for all attendees
        availability = _get_attendee_availability(attendees, date_range)

        # Find overlapping free slots
        free_slots = _find_free_slots(
            availability,
            duration_minutes,
            preferred_time_range
        )

        # Score and rank slots
        ranked_slots = _rank_time_slots(free_slots, attendees)

        return ranked_slots[:5]  # Return top 5 options

    except Exception as e:
        return [{
            "error": str(e),
            "message": "Failed to find meeting times"
        }]


def schedule_meeting(
    title: str,
    start_time: str,
    duration_minutes: int,
    attendees: List[str],
    description: str = "",
    location: str = "",
    send_invites: bool = True
) -> Dict[str, Any]:
    """
    Create a calendar event with attendees.

    Args:
        title: Meeting title
        start_time: ISO format datetime string
        duration_minutes: Meeting duration
        attendees: List of attendee emails
        description: Optional meeting description
        location: Physical or virtual location
        send_invites: Whether to send calendar invites

    Returns:
        Created event details
    """
    event = {
        "title": title,
        "start": start_time,
        "end": _calculate_end_time(start_time, duration_minutes),
        "attendees": attendees,
        "description": description,
        "location": location,
        "status": "confirmed"
    }

    # Note: Actually creating events would require write scope
    # For read-only demo, we just return the event structure
    return {
        "status": "event_planned",
        "event": event,
        "message": "Event details prepared. To actually create, grant calendar write access."
    }


def optimize_calendar(
    user_email: str,
    time_range: str = "this_week"
) -> Dict[str, Any]:
    """
    Analyze calendar and suggest optimizations.

    Args:
        user_email: User's email address
        time_range: Time period to analyze

    Returns:
        Analysis and recommendations
    """
    try:
        # Get user's calendar events
        events = _get_calendar_events(user_email, time_range)

        analysis = {
            "total_meetings": len(events),
            "total_hours": _calculate_meeting_hours(events),
            "back_to_back_meetings": _find_back_to_back(events),
            "meeting_overload_days": _find_overload_days(events),
            "fragmented_time": _find_fragmented_time(events),
            "recommendations": []
        }

        # Generate recommendations
        if analysis["back_to_back_meetings"]:
            analysis["recommendations"].append({
                "type": "add_breaks",
                "priority": "high",
                "message": f"You have {len(analysis['back_to_back_meetings'])} back-to-back meetings. Consider adding 15-min buffers.",
                "suggested_actions": _suggest_break_times(analysis["back_to_back_meetings"])
            })

        if analysis["meeting_overload_days"]:
            analysis["recommendations"].append({
                "type": "redistribute_meetings",
                "priority": "medium",
                "message": f"{len(analysis['meeting_overload_days'])} day(s) have 5+ hours of meetings.",
                "suggested_actions": _suggest_reschedule(analysis["meeting_overload_days"])
            })

        if analysis["fragmented_time"]:
            analysis["recommendations"].append({
                "type": "consolidate_focus_time",
                "priority": "medium",
                "message": "Calendar has fragmented time blocks. Consider grouping meetings.",
                "suggested_actions": ["Block 2-hour focus time slots", "Move 1:1s to same day"]
            })

        return analysis

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to optimize calendar"
        }


def get_daily_schedule(user_email: str) -> Dict[str, Any]:
    """
    Get today's schedule with context and preparation needs.

    Args:
        user_email: User's email address

    Returns:
        Today's schedule with meeting prep info
    """
    try:
        events = _get_calendar_events(user_email, "today")

        schedule = {
            "date": datetime.datetime.now().date().isoformat(),
            "total_meetings": len(events),
            "first_meeting": events[0]["start"] if events else None,
            "last_meeting": events[-1]["end"] if events else None,
            "meetings": []
        }

        for event in events:
            meeting_info = {
                "time": event["start"],
                "title": event["title"],
                "attendees": event.get("attendees", []),
                "location": event.get("location", ""),
                "prep_needed": _assess_prep_needs(event),
                "context": _get_meeting_context(event)
            }
            schedule["meetings"].append(meeting_info)

        return schedule

    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to get daily schedule"
        }


def resolve_conflicts(user_email: str) -> List[Dict[str, Any]]:
    """
    Detect and suggest resolutions for calendar conflicts.

    Args:
        user_email: User's email address

    Returns:
        List of conflicts with resolution suggestions
    """
    try:
        events = _get_calendar_events(user_email, "next_30_days")

        conflicts = []
        for i, event1 in enumerate(events):
            for event2 in events[i+1:]:
                if _events_overlap(event1, event2):
                    conflict = {
                        "conflict_type": "double_booking",
                        "event1": event1,
                        "event2": event2,
                        "severity": _assess_conflict_severity(event1, event2),
                        "suggestions": _generate_resolution_options(event1, event2)
                    }
                    conflicts.append(conflict)

        return conflicts

    except Exception as e:
        return [{
            "error": str(e),
            "message": "Failed to resolve conflicts"
        }]


# Create the agent - ADK automatically wraps functions as FunctionTools
root_agent = Agent(
    name="calendar_agent",
    model="gemini-2.5-pro",
    instruction="You are a calendar management agent. Help users find optimal meeting times, schedule events, optimize their calendar, resolve conflicts, and get daily schedule briefings. Use available tools to query Google Calendar directly and coordinate with multiple attendees. Prioritize work-life balance and efficient time management.",
    description="Smart calendar management assistant that optimizes scheduling through intelligent meeting time discovery, automated conflict resolution, calendar optimization, and daily schedule briefings. Uses Google Calendar API for direct access to calendar data.",
    tools=[find_meeting_time, schedule_meeting, optimize_calendar, get_daily_schedule, resolve_conflicts]
)
