"""
Calendar Agent - Handles meeting scheduling and calendar optimization
Part of Gemini Enterprise Demo #3
"""

import os
from google.adk import Agent, Tool
from google.cloud import discoveryengine_v1
from typing import List, Dict, Any, Optional
import datetime
from dateutil import parser as date_parser


class CalendarAgent(Agent):
    """
    Agent that manages calendar operations including:
    - Smart meeting scheduling
    - Calendar optimization
    - Meeting conflict resolution
    - Attendee coordination
    """

    def __init__(self, project_id: str, location: str):
        super().__init__(
            name="calendar_agent",
            model="gemini-2.5-pro",
            description="Intelligent calendar assistant for meeting management",
            instruction="You are a calendar management agent. Help users find optimal meeting times, schedule events, optimize their calendar, resolve conflicts, and get daily schedule briefings. Use available tools to query calendar data and coordinate with multiple attendees. Prioritize work-life balance and efficient time management."
        )
        self.project_id = project_id
        self.location = location
        self.calendar_datastore = f"projects/{project_id}/locations/global/collections/default_collection/dataStores/demo-calendar-datastore"

    @Tool(
        name="find_meeting_time",
        description="Find optimal meeting time considering all attendees' calendars"
    )
    def find_meeting_time(
        self,
        attendees: List[str],
        duration_minutes: int,
        preferred_time_range: str = "business_hours",
        date_range: str = "next_7_days"
    ) -> List[Dict[str, Any]]:
        """
        Finds optimal meeting times for all attendees.

        Args:
            attendees: List of attendee email addresses
            duration_minutes: Meeting duration in minutes
            preferred_time_range: "business_hours", "morning", "afternoon"
            date_range: "next_7_days", "next_2_weeks", "this_week"

        Returns:
            List of available time slots with scoring
        """
        # Get availability for all attendees
        availability = self._get_attendee_availability(attendees, date_range)

        # Find overlapping free slots
        free_slots = self._find_free_slots(
            availability,
            duration_minutes,
            preferred_time_range
        )

        # Score and rank slots
        ranked_slots = self._rank_time_slots(free_slots, attendees)

        return ranked_slots[:5]  # Return top 5 options

    @Tool(
        name="schedule_meeting",
        description="Create a calendar event with attendees"
    )
    def schedule_meeting(
        self,
        title: str,
        start_time: str,
        duration_minutes: int,
        attendees: List[str],
        description: str = "",
        location: str = "",
        send_invites: bool = True
    ) -> Dict[str, Any]:
        """
        Creates a calendar event.

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
        # This would use Gemini Enterprise Calendar Actions
        event = {
            "title": title,
            "start": start_time,
            "end": self._calculate_end_time(start_time, duration_minutes),
            "attendees": attendees,
            "description": description,
            "location": location,
            "status": "confirmed"
        }

        # Log for demo
        print(f"Creating meeting: {title} at {start_time}")
        print(f"Attendees: {', '.join(attendees)}")
        if send_invites:
            print(f"Sending invites to {len(attendees)} attendees")

        return event

    @Tool(
        name="optimize_calendar",
        description="Analyze calendar and suggest optimizations"
    )
    def optimize_calendar(
        self,
        user_email: str,
        time_range: str = "this_week"
    ) -> Dict[str, Any]:
        """
        Analyzes calendar and provides optimization suggestions.

        Args:
            user_email: User's email address
            time_range: Time period to analyze

        Returns:
            Analysis and recommendations
        """
        # Get user's calendar events
        events = self._get_calendar_events(user_email, time_range)

        analysis = {
            "total_meetings": len(events),
            "total_hours": self._calculate_meeting_hours(events),
            "back_to_back_meetings": self._find_back_to_back(events),
            "meeting_overload_days": self._find_overload_days(events),
            "fragmented_time": self._find_fragmented_time(events),
            "recommendations": []
        }

        # Generate recommendations
        if analysis["back_to_back_meetings"]:
            analysis["recommendations"].append({
                "type": "add_breaks",
                "priority": "high",
                "message": f"You have {len(analysis['back_to_back_meetings'])} back-to-back meetings. Consider adding 15-min buffers.",
                "suggested_actions": self._suggest_break_times(analysis["back_to_back_meetings"])
            })

        if analysis["meeting_overload_days"]:
            analysis["recommendations"].append({
                "type": "redistribute_meetings",
                "priority": "medium",
                "message": f"{len(analysis['meeting_overload_days'])} day(s) have 5+ hours of meetings.",
                "suggested_actions": self._suggest_reschedule(analysis["meeting_overload_days"])
            })

        if analysis["fragmented_time"]:
            analysis["recommendations"].append({
                "type": "consolidate_focus_time",
                "priority": "medium",
                "message": "Calendar has fragmented time blocks. Consider grouping meetings.",
                "suggested_actions": ["Block 2-hour focus time slots", "Move 1:1s to same day"]
            })

        return analysis

    @Tool(
        name="get_daily_schedule",
        description="Get today's schedule with context and preparation needs"
    )
    def get_daily_schedule(self, user_email: str) -> Dict[str, Any]:
        """
        Provides daily schedule briefing.

        Args:
            user_email: User's email address

        Returns:
            Today's schedule with meeting prep info
        """
        today = datetime.datetime.now().date()
        events = self._get_calendar_events(
            user_email,
            f"{today.isoformat()}/{today.isoformat()}"
        )

        schedule = {
            "date": today.isoformat(),
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
                "prep_needed": self._assess_prep_needs(event),
                "context": self._get_meeting_context(event)
            }
            schedule["meetings"].append(meeting_info)

        return schedule

    @Tool(
        name="resolve_conflicts",
        description="Detect and suggest resolutions for calendar conflicts"
    )
    def resolve_conflicts(self, user_email: str) -> List[Dict[str, Any]]:
        """
        Finds calendar conflicts and suggests resolutions.

        Args:
            user_email: User's email address

        Returns:
            List of conflicts with resolution suggestions
        """
        events = self._get_calendar_events(user_email, "next_30_days")

        conflicts = []
        for i, event1 in enumerate(events):
            for event2 in events[i+1:]:
                if self._events_overlap(event1, event2):
                    conflict = {
                        "conflict_type": "double_booking",
                        "event1": event1,
                        "event2": event2,
                        "severity": self._assess_conflict_severity(event1, event2),
                        "suggestions": self._generate_resolution_options(event1, event2)
                    }
                    conflicts.append(conflict)

        return conflicts

    # Helper methods

    def _get_attendee_availability(
        self,
        attendees: List[str],
        date_range: str
    ) -> Dict[str, List[Dict]]:
        """Get calendar availability for all attendees"""
        # In production, query Calendar data store
        # For demo, return mock availability
        availability = {}
        for attendee in attendees:
            availability[attendee] = self._get_calendar_events(attendee, date_range)
        return availability

    def _find_free_slots(
        self,
        availability: Dict[str, List[Dict]],
        duration_minutes: int,
        preferred_time_range: str
    ) -> List[Dict[str, Any]]:
        """Find time slots when all attendees are free"""
        # Simplified logic for demo
        free_slots = []

        # Business hours: 9 AM - 5 PM
        start_hour, end_hour = self._get_time_range_hours(preferred_time_range)

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
                if self._all_attendees_free(availability, slot_start, slot_end):
                    free_slots.append({
                        "start": slot_start.isoformat(),
                        "end": slot_end.isoformat(),
                        "day_of_week": check_date.strftime("%A")
                    })

        return free_slots

    def _rank_time_slots(
        self,
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

    def _calculate_end_time(self, start_time: str, duration_minutes: int) -> str:
        """Calculate meeting end time"""
        start = date_parser.parse(start_time)
        end = start + datetime.timedelta(minutes=duration_minutes)
        return end.isoformat()

    def _get_calendar_events(self, user_email: str, time_range: str) -> List[Dict]:
        """Query calendar data store for events"""
        # In production, query Gemini Enterprise Calendar data store
        # For demo, return mock events
        return []

    def _calculate_meeting_hours(self, events: List[Dict]) -> float:
        """Calculate total hours in meetings"""
        total_minutes = sum(
            (date_parser.parse(e["end"]) - date_parser.parse(e["start"])).seconds / 60
            for e in events
        )
        return round(total_minutes / 60, 1)

    def _find_back_to_back(self, events: List[Dict]) -> List[tuple]:
        """Find back-to-back meetings with no breaks"""
        back_to_back = []
        for i in range(len(events) - 1):
            if events[i]["end"] == events[i+1]["start"]:
                back_to_back.append((events[i], events[i+1]))
        return back_to_back

    def _find_overload_days(self, events: List[Dict]) -> List[str]:
        """Find days with excessive meeting time"""
        day_hours = {}
        for event in events:
            day = date_parser.parse(event["start"]).date().isoformat()
            duration = (date_parser.parse(event["end"]) - date_parser.parse(event["start"])).seconds / 3600
            day_hours[day] = day_hours.get(day, 0) + duration

        return [day for day, hours in day_hours.items() if hours >= 5]

    def _find_fragmented_time(self, events: List[Dict]) -> bool:
        """Detect fragmented time blocks"""
        # Check if there are many short gaps between meetings
        gaps = []
        for i in range(len(events) - 1):
            gap = (date_parser.parse(events[i+1]["start"]) - date_parser.parse(events[i]["end"])).seconds / 60
            gaps.append(gap)

        # Fragmented if many gaps of 15-45 minutes
        short_gaps = [g for g in gaps if 15 <= g <= 45]
        return len(short_gaps) >= 3

    def _suggest_break_times(self, back_to_back: List[tuple]) -> List[str]:
        """Suggest where to add breaks"""
        return [f"Add 15-min buffer after {b[0]['title']}" for b in back_to_back[:3]]

    def _suggest_reschedule(self, overload_days: List[str]) -> List[str]:
        """Suggest meeting rescheduling"""
        return [f"Move non-critical meetings from {day}" for day in overload_days]

    def _assess_prep_needs(self, event: Dict) -> str:
        """Assess if meeting needs preparation"""
        keywords = ["review", "presentation", "demo", "pitch", "board"]
        if any(kw in event.get("title", "").lower() for kw in keywords):
            return "high"
        return "low"

    def _get_meeting_context(self, event: Dict) -> str:
        """Get context for meeting"""
        # In production, query email threads and documents
        return f"Meeting about {event.get('title', 'N/A')}"

    def _get_time_range_hours(self, preferred_time_range: str) -> tuple:
        """Convert time range to hours"""
        if preferred_time_range == "morning":
            return 9, 12
        elif preferred_time_range == "afternoon":
            return 13, 17
        else:  # business_hours
            return 9, 17

    def _all_attendees_free(
        self,
        availability: Dict[str, List[Dict]],
        slot_start: datetime.datetime,
        slot_end: datetime.datetime
    ) -> bool:
        """Check if all attendees are free"""
        for attendee, events in availability.items():
            for event in events:
                event_start = date_parser.parse(event["start"])
                event_end = date_parser.parse(event["end"])
                if not (slot_end <= event_start or slot_start >= event_end):
                    return False
        return True

    def _events_overlap(self, event1: Dict, event2: Dict) -> bool:
        """Check if two events overlap"""
        start1 = date_parser.parse(event1["start"])
        end1 = date_parser.parse(event1["end"])
        start2 = date_parser.parse(event2["start"])
        end2 = date_parser.parse(event2["end"])

        return not (end1 <= start2 or start1 >= end2)

    def _assess_conflict_severity(self, event1: Dict, event2: Dict) -> str:
        """Assess severity of calendar conflict"""
        # Check if either meeting is marked important
        important_keywords = ["board", "executive", "ceo", "urgent"]
        e1_important = any(kw in event1.get("title", "").lower() for kw in important_keywords)
        e2_important = any(kw in event2.get("title", "").lower() for kw in important_keywords)

        if e1_important or e2_important:
            return "high"
        return "medium"

    def _generate_resolution_options(self, event1: Dict, event2: Dict) -> List[str]:
        """Generate options to resolve conflict"""
        return [
            f"Reschedule '{event1['title']}' to next available slot",
            f"Reschedule '{event2['title']}' to next available slot",
            "Decline one meeting and send regrets"
        ]


# Agent registration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = os.environ.get("LOCATION", "us-central1")

def create_agent(project_id: str, location: str = "us-central1") -> CalendarAgent:
    """Factory function to create and configure the Calendar Agent"""
    return CalendarAgent(project_id, location)

# Export root_agent for ADK deployment
root_agent = create_agent(PROJECT_ID, LOCATION)
