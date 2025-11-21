"""
Email Agent - Handles email summarization, drafting, and management
Part of Gemini Enterprise Demo #3
"""

import os
from google.adk import Agent, Tool
from google.cloud import discoveryengine_v1
from typing import List, Dict, Any
import datetime


class EmailAgent(Agent):
    """
    Agent that manages email operations including:
    - Email summarization and prioritization
    - Draft generation
    - Smart filtering and labeling
    - Context-aware responses
    """

    def __init__(self, project_id: str, location: str):
        super().__init__(
            name="email-agent",
            model="gemini-2.5-pro",
            description="Intelligent email assistant that manages inbox operations",
            instruction="You are an email management agent. Help users summarize emails, draft responses, search their inbox, and categorize messages. Use the available tools to query Gmail data and generate intelligent responses. Always prioritize urgent emails and provide actionable recommendations."
        )
        self.project_id = project_id
        self.location = location
        self.gmail_datastore = f"projects/{project_id}/locations/global/collections/default_collection/dataStores/demo-gmail-datastore"

    @Tool(
        name="summarize_emails",
        description="Summarize unread emails and prioritize by importance"
    )
    def summarize_emails(self, time_range: str = "today") -> Dict[str, Any]:
        """
        Summarizes emails from specified time range.

        Args:
            time_range: "today", "this_week", "last_24h"

        Returns:
            Summary with priorities, urgent items, and recommended actions
        """
        # Query Gemini Enterprise data store
        client = discoveryengine_v1.SearchServiceClient()

        # Build search query
        query = self._build_time_query(time_range)

        request = discoveryengine_v1.SearchRequest(
            serving_config=f"{self.gmail_datastore}/servingConfigs/default_search",
            query=query,
            page_size=50
        )

        response = client.search(request)

        # Analyze emails with Gemini
        emails = [self._parse_email(result) for result in response.results]

        summary = {
            "total_unread": len(emails),
            "urgent": self._filter_urgent(emails),
            "important": self._filter_important(emails),
            "can_wait": self._filter_can_wait(emails),
            "recommended_actions": self._generate_recommendations(emails)
        }

        return summary

    @Tool(
        name="draft_email_response",
        description="Generate a draft email response based on context"
    )
    def draft_email_response(
        self,
        email_id: str,
        tone: str = "professional",
        key_points: List[str] = None
    ) -> str:
        """
        Drafts an email response with appropriate tone and content.

        Args:
            email_id: The email to respond to
            tone: "professional", "casual", "formal"
            key_points: Optional list of points to include

        Returns:
            Draft email text
        """
        # Retrieve email context
        email_context = self._get_email_context(email_id)

        # Build prompt for Gemini
        prompt = f"""
        Draft a {tone} email response to the following email:

        From: {email_context['from']}
        Subject: {email_context['subject']}
        Body: {email_context['body']}

        Key points to address:
        {chr(10).join(f'- {point}' for point in (key_points or []))}

        Context from previous emails in thread:
        {email_context['thread_context']}

        Generate a clear, concise response.
        """

        # Use Gemini to generate draft
        draft = self.generate_content(prompt)

        return draft

    @Tool(
        name="search_emails",
        description="Search emails with natural language query"
    )
    def search_emails(
        self,
        query: str,
        date_range: str = None,
        from_sender: str = None,
        has_attachment: bool = None
    ) -> List[Dict[str, Any]]:
        """
        Search emails using natural language.

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
            serving_config=f"{self.gmail_datastore}/servingConfigs/default_search",
            query=enhanced_query,
            page_size=20
        )

        response = client.search(request)

        results = [self._parse_email(result) for result in response.results]
        return results

    @Tool(
        name="categorize_and_label",
        description="Automatically categorize and label emails"
    )
    def categorize_and_label(self, email_ids: List[str]) -> Dict[str, List[str]]:
        """
        Automatically categorizes emails and suggests labels.

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
            email = self._get_email_context(email_id)

            # Use Gemini to categorize
            prompt = f"""
            Categorize this email into ONE of these categories:
            - urgent_action_required
            - review_requested
            - informational
            - meeting_invites
            - follow_ups

            Email subject: {email['subject']}
            Email body: {email['body'][:500]}

            Return only the category name.
            """

            category = self.generate_content(prompt).strip()
            if category in categories:
                categories[category].append(email_id)

        return categories

    # Helper methods

    def _build_time_query(self, time_range: str) -> str:
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

    def _parse_email(self, search_result) -> Dict[str, Any]:
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

    def _filter_urgent(self, emails: List[Dict]) -> List[Dict]:
        """Filter urgent emails"""
        urgent_keywords = ["urgent", "asap", "deadline", "important", "critical"]
        return [
            e for e in emails
            if any(kw in e["subject"].lower() or kw in e["snippet"].lower()
                   for kw in urgent_keywords)
        ]

    def _filter_important(self, emails: List[Dict]) -> List[Dict]:
        """Filter important but not urgent emails"""
        important_senders = ["ceo@", "board@", "executives@"]
        return [
            e for e in emails
            if any(sender in e["from"].lower() for sender in important_senders)
            and e not in self._filter_urgent(emails)
        ]

    def _filter_can_wait(self, emails: List[Dict]) -> List[Dict]:
        """Filter emails that can wait"""
        all_emails = set(e["id"] for e in emails)
        urgent_ids = set(e["id"] for e in self._filter_urgent(emails))
        important_ids = set(e["id"] for e in self._filter_important(emails))

        can_wait_ids = all_emails - urgent_ids - important_ids
        return [e for e in emails if e["id"] in can_wait_ids]

    def _generate_recommendations(self, emails: List[Dict]) -> List[str]:
        """Generate action recommendations"""
        recommendations = []

        urgent = self._filter_urgent(emails)
        if urgent:
            recommendations.append(f"Respond to {len(urgent)} urgent email(s) first")

        meeting_invites = [e for e in emails if "invite" in e["subject"].lower()]
        if meeting_invites:
            recommendations.append(f"Accept/decline {len(meeting_invites)} meeting invite(s)")

        return recommendations

    def _get_email_context(self, email_id: str) -> Dict[str, Any]:
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


# Agent registration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = os.environ.get("LOCATION", "us-central1")

def create_agent(project_id: str, location: str = "us-central1") -> EmailAgent:
    """Factory function to create and configure the Email Agent"""
    return EmailAgent(project_id, location)

# Export root_agent for ADK deployment
root_agent = create_agent(PROJECT_ID, LOCATION)
