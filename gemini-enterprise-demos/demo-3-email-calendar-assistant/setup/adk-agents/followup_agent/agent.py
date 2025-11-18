"""
Follow-up Agent - Automates post-meeting and post-email follow-ups
Part of Gemini Enterprise Demo #3
"""

from google.adk import Agent, Tool
from google.cloud import firestore
from typing import List, Dict, Any
import datetime


class FollowUpAgent(Agent):
    """
    Agent that handles automated follow-ups:
    - Post-meeting summaries and action items
    - Email response reminders
    - Task tracking and completion
    - Proactive nudges for pending items
    """

    def __init__(self, project_id: str, location: str):
        super().__init__(
            name="followup-agent",
            model="gemini-2.5-pro",
            description="Automated follow-up and task management assistant"
        )
        self.project_id = project_id
        self.location = location
        self.db = firestore.Client(project=project_id)

    @Tool(
        name="create_meeting_followup",
        description="Generate post-meeting summary with action items"
    )
    def create_meeting_followup(
        self,
        meeting_id: str,
        meeting_transcript: str = None,
        send_to_participants: bool = True
    ) -> Dict[str, Any]:
        """
        Creates comprehensive meeting follow-up.

        Args:
            meeting_id: Calendar event ID
            meeting_transcript: Optional meeting transcript from Google Meet
            send_to_participants: Whether to email participants

        Returns:
            Follow-up package with summary, action items, and next steps
        """
        # Get meeting details
        meeting = self._get_meeting_details(meeting_id)

        # Extract key information
        if meeting_transcript:
            summary = self._generate_summary_from_transcript(meeting_transcript)
            action_items = self._extract_action_items(meeting_transcript)
            decisions = self._extract_decisions(meeting_transcript)
            key_points = self._extract_key_points(meeting_transcript)
        else:
            # If no transcript, use meeting description and title
            summary = f"Meeting about {meeting['title']}"
            action_items = []
            decisions = []
            key_points = []

        followup = {
            "meeting_id": meeting_id,
            "meeting_title": meeting["title"],
            "date": meeting["start"],
            "participants": meeting["attendees"],
            "summary": summary,
            "key_discussion_points": key_points,
            "decisions_made": decisions,
            "action_items": action_items,
            "next_meeting": self._suggest_next_meeting(meeting, action_items),
            "attachments": []
        }

        # Create follow-up email draft
        email_draft = self._format_followup_email(followup)
        followup["email_draft"] = email_draft

        # Store action items in Firestore for tracking
        self._store_action_items(action_items, meeting_id)

        # Schedule follow-up reminders
        self._schedule_reminders(action_items)

        return followup

    @Tool(
        name="track_action_items",
        description="Track status of action items and send reminders"
    )
    def track_action_items(
        self,
        user_email: str,
        timeframe: str = "all"
    ) -> Dict[str, Any]:
        """
        Tracks all action items for a user.

        Args:
            user_email: User's email address
            timeframe: "all", "overdue", "this_week", "today"

        Returns:
            Action items with status and recommendations
        """
        # Query Firestore for action items
        items_ref = self.db.collection('follow_up_tasks')
        query = items_ref.where('user_id', '==', user_email)

        # Apply timeframe filter
        now = datetime.datetime.now()
        if timeframe == "overdue":
            query = query.where('due_date', '<', now).where('status', '==', 'pending')
        elif timeframe == "this_week":
            week_end = now + datetime.timedelta(days=7)
            query = query.where('due_date', '<=', week_end)
        elif timeframe == "today":
            today_end = now.replace(hour=23, minute=59, second=59)
            query = query.where('due_date', '<=', today_end)

        items = []
        for doc in query.stream():
            item = doc.to_dict()
            item['id'] = doc.id
            items.append(item)

        # Categorize items
        categorized = {
            "overdue": [],
            "due_today": [],
            "due_this_week": [],
            "upcoming": [],
            "completed": []
        }

        today_end = now.replace(hour=23, minute=59, second=59)
        week_end = now + datetime.timedelta(days=7)

        for item in items:
            due_date = item.get('due_date')

            if item['status'] == 'completed':
                categorized["completed"].append(item)
            elif due_date < now:
                categorized["overdue"].append(item)
            elif due_date <= today_end:
                categorized["due_today"].append(item)
            elif due_date <= week_end:
                categorized["due_this_week"].append(item)
            else:
                categorized["upcoming"].append(item)

        # Generate recommendations
        recommendations = []
        if categorized["overdue"]:
            recommendations.append(
                f"⚠️ {len(categorized['overdue'])} overdue items - prioritize these"
            )
        if categorized["due_today"]:
            recommendations.append(
                f"📅 {len(categorized['due_today'])} items due today"
            )

        return {
            "total_items": len(items),
            "categorized": categorized,
            "recommendations": recommendations
        }

    @Tool(
        name="send_email_reminder",
        description="Send reminder for unanswered emails"
    )
    def send_email_reminder(
        self,
        email_id: str,
        days_since_received: int
    ) -> Dict[str, Any]:
        """
        Creates reminder for unanswered email.

        Args:
            email_id: Email that needs response
            days_since_received: How many days ago it was received

        Returns:
            Reminder details with suggested response
        """
        # Get email context
        email = self._get_email_details(email_id)

        # Determine urgency
        if "urgent" in email["subject"].lower() or days_since_received >= 3:
            urgency = "high"
        elif days_since_received >= 1:
            urgency = "medium"
        else:
            urgency = "low"

        reminder = {
            "email_id": email_id,
            "from": email["from"],
            "subject": email["subject"],
            "received_date": email["date"],
            "days_since_received": days_since_received,
            "urgency": urgency,
            "suggested_response": self._generate_response_suggestion(email),
            "reminder_message": self._format_reminder_message(email, days_since_received)
        }

        return reminder

    @Tool(
        name="update_action_item",
        description="Update status of an action item"
    )
    def update_action_item(
        self,
        item_id: str,
        status: str,
        notes: str = None
    ) -> Dict[str, Any]:
        """
        Updates action item status.

        Args:
            item_id: Action item ID
            status: New status ("pending", "in_progress", "completed", "blocked")
            notes: Optional notes about the update

        Returns:
            Updated action item
        """
        # Update in Firestore
        item_ref = self.db.collection('follow_up_tasks').document(item_id)

        update_data = {
            'status': status,
            'updated_at': datetime.datetime.now()
        }

        if notes:
            update_data['notes'] = notes

        if status == "completed":
            update_data['completed_at'] = datetime.datetime.now()

        item_ref.update(update_data)

        # Get updated item
        updated = item_ref.get().to_dict()
        updated['id'] = item_id

        # Check if this was part of a larger workflow
        related_items = self._get_related_action_items(item_id)

        return {
            "updated_item": updated,
            "related_items": related_items,
            "workflow_status": self._check_workflow_status(related_items)
        }

    @Tool(
        name="generate_weekly_summary",
        description="Create weekly summary of completed tasks and upcoming items"
    )
    def generate_weekly_summary(
        self,
        user_email: str
    ) -> Dict[str, Any]:
        """
        Generates weekly summary report.

        Args:
            user_email: User's email address

        Returns:
            Weekly summary with accomplishments and next week preview
        """
        now = datetime.datetime.now()
        week_start = now - datetime.timedelta(days=7)
        week_end = now + datetime.timedelta(days=7)

        # Get completed items from past week
        completed_query = self.db.collection('follow_up_tasks')\
            .where('user_id', '==', user_email)\
            .where('status', '==', 'completed')\
            .where('completed_at', '>=', week_start)

        completed_items = [doc.to_dict() for doc in completed_query.stream()]

        # Get upcoming items for next week
        upcoming_query = self.db.collection('follow_up_tasks')\
            .where('user_id', '==', user_email)\
            .where('status', '==', 'pending')\
            .where('due_date', '<=', week_end)

        upcoming_items = [doc.to_dict() for doc in upcoming_query.stream()]

        # Categorize accomplishments
        accomplishments_by_category = self._categorize_items(completed_items)

        summary = {
            "week_of": week_start.strftime("%B %d, %Y"),
            "accomplishments": {
                "total_completed": len(completed_items),
                "by_category": accomplishments_by_category,
                "highlights": self._identify_highlights(completed_items)
            },
            "next_week_preview": {
                "total_upcoming": len(upcoming_items),
                "by_priority": self._group_by_priority(upcoming_items),
                "recommended_focus": self._recommend_focus_areas(upcoming_items)
            },
            "productivity_metrics": {
                "completion_rate": self._calculate_completion_rate(user_email, week_start),
                "average_time_to_complete": self._calculate_avg_completion_time(completed_items),
                "on_time_percentage": self._calculate_on_time_percentage(completed_items)
            }
        }

        return summary

    # Helper methods

    def _get_meeting_details(self, meeting_id: str) -> Dict[str, Any]:
        """Retrieve meeting details"""
        # Mock data for demo
        return {
            "id": meeting_id,
            "title": "Sprint Planning",
            "start": "2025-11-20T09:00:00-08:00",
            "attendees": ["demo-user@company.com", "team@company.com"],
            "description": "Plan next sprint"
        }

    def _generate_summary_from_transcript(self, transcript: str) -> str:
        """Generate meeting summary from transcript"""
        prompt = f"""
        Summarize this meeting transcript in 2-3 sentences:

        {transcript[:2000]}  # Limit for context

        Focus on:
        - Main topics discussed
        - Key outcomes
        - Overall sentiment
        """

        return self.generate_content(prompt)

    def _extract_action_items(self, transcript: str) -> List[Dict]:
        """Extract action items from transcript"""
        prompt = f"""
        Extract all action items from this meeting transcript.

        For each action item, identify:
        - What needs to be done
        - Who is responsible (if mentioned)
        - When it's due (if mentioned)

        Transcript:
        {transcript[:2000]}

        Return as a structured list.
        """

        response = self.generate_content(prompt)

        # Parse response into structured action items
        # In production, use more sophisticated parsing
        items = []
        for line in response.strip().split('\n'):
            if line.strip():
                items.append({
                    "description": line.strip(),
                    "owner": "TBD",
                    "due_date": datetime.datetime.now() + datetime.timedelta(days=7),
                    "status": "pending"
                })

        return items

    def _extract_decisions(self, transcript: str) -> List[str]:
        """Extract decisions made during meeting"""
        prompt = f"""
        Extract all decisions that were made in this meeting.

        Transcript:
        {transcript[:2000]}

        Return as a bulleted list of clear decision statements.
        """

        response = self.generate_content(prompt)
        return [line.strip() for line in response.strip().split('\n') if line.strip()]

    def _extract_key_points(self, transcript: str) -> List[str]:
        """Extract key discussion points"""
        prompt = f"""
        Extract the 5-7 most important discussion points from this meeting.

        Transcript:
        {transcript[:2000]}

        Return as a bulleted list.
        """

        response = self.generate_content(prompt)
        return [line.strip() for line in response.strip().split('\n') if line.strip()]

    def _suggest_next_meeting(self, meeting: Dict, action_items: List[Dict]) -> Dict:
        """Suggest when next meeting should be scheduled"""
        if action_items:
            # Schedule next meeting after action items are due
            latest_due = max([item['due_date'] for item in action_items])
            next_meeting_date = latest_due + datetime.timedelta(days=7)
        else:
            # Default to 2 weeks
            next_meeting_date = datetime.datetime.now() + datetime.timedelta(days=14)

        return {
            "suggested_date": next_meeting_date.isoformat(),
            "reason": "Follow up on action items" if action_items else "Regular sync",
            "duration_minutes": meeting.get("duration", 30)
        }

    def _format_followup_email(self, followup: Dict) -> str:
        """Format follow-up as email"""
        email = f"""
Subject: Meeting Summary: {followup['meeting_title']}

Hi everyone,

Thanks for joining today's meeting. Here's a summary:

SUMMARY:
{followup['summary']}

KEY DISCUSSION POINTS:
{chr(10).join(f'• {point}' for point in followup['key_discussion_points'][:5])}

DECISIONS MADE:
{chr(10).join(f'• {decision}' for decision in followup['decisions_made'][:5])}

ACTION ITEMS:
{chr(10).join(f"• {item['description']} (Owner: {item.get('owner', 'TBD')}, Due: {item.get('due_date', 'TBD')})" for item in followup['action_items'][:10])}

NEXT MEETING:
{followup['next_meeting'].get('suggested_date', 'TBD')} - {followup['next_meeting'].get('reason', '')}

Please let me know if I missed anything or if any action items need clarification.

Best,
[Auto-generated by Meeting Follow-up Agent]
"""
        return email

    def _store_action_items(self, items: List[Dict], meeting_id: str):
        """Store action items in Firestore"""
        for item in items:
            self.db.collection('follow_up_tasks').add({
                **item,
                'related_meeting_id': meeting_id,
                'created_at': datetime.datetime.now()
            })

    def _schedule_reminders(self, items: List[Dict]):
        """Schedule reminders for action items"""
        # In production, schedule actual calendar reminders
        pass

    def _get_email_details(self, email_id: str) -> Dict:
        """Get email details"""
        return {
            "id": email_id,
            "from": "sender@example.com",
            "subject": "Question about project",
            "date": "2025-11-15",
            "body": "..."
        }

    def _generate_response_suggestion(self, email: Dict) -> str:
        """Generate suggested email response"""
        prompt = f"""
        Draft a brief response to this email:

        From: {email['from']}
        Subject: {email['subject']}

        Keep it professional and concise.
        """

        return self.generate_content(prompt)

    def _format_reminder_message(self, email: Dict, days: int) -> str:
        """Format reminder message"""
        return f"⏰ Reminder: Email from {email['from']} about '{email['subject']}' hasn't been answered in {days} days."

    def _get_related_action_items(self, item_id: str) -> List[Dict]:
        """Get related action items"""
        return []

    def _check_workflow_status(self, items: List[Dict]) -> str:
        """Check overall workflow completion status"""
        if not items:
            return "No related items"

        completed = len([i for i in items if i.get('status') == 'completed'])
        total = len(items)

        if completed == total:
            return f"Workflow complete ({completed}/{total})"
        else:
            return f"In progress ({completed}/{total} completed)"

    def _categorize_items(self, items: List[Dict]) -> Dict:
        """Categorize items by type"""
        categories = {}
        for item in items:
            category = item.get('task_type', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(item)
        return categories

    def _identify_highlights(self, items: List[Dict]) -> List[str]:
        """Identify highlight accomplishments"""
        return [item['description'] for item in items[:3]]

    def _group_by_priority(self, items: List[Dict]) -> Dict:
        """Group items by priority"""
        grouped = {"high": [], "medium": [], "low": []}
        for item in items:
            priority = item.get('priority', 'medium')
            grouped[priority].append(item)
        return grouped

    def _recommend_focus_areas(self, items: List[Dict]) -> List[str]:
        """Recommend focus areas"""
        return ["Complete high-priority items first", "Block focus time for complex tasks"]

    def _calculate_completion_rate(self, user_email: str, since_date: datetime.datetime) -> float:
        """Calculate completion rate"""
        return 85.0  # Mock value

    def _calculate_avg_completion_time(self, items: List[Dict]) -> str:
        """Calculate average completion time"""
        return "2.5 days"  # Mock value

    def _calculate_on_time_percentage(self, items: List[Dict]) -> float:
        """Calculate on-time completion percentage"""
        return 78.0  # Mock value


# Agent registration
def create_agent(project_id: str, location: str = "us-central1") -> FollowUpAgent:
    """Factory function to create and configure the Follow-up Agent"""
    return FollowUpAgent(project_id, location)
