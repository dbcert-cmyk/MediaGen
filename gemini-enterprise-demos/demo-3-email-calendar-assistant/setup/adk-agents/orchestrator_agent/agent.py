"""
Orchestrator Agent - Main coordinator for all specialized agents
Routes queries to appropriate agents and combines multi-agent responses
Part of Gemini Enterprise Demo #3
"""

import os
from google.adk.agents import Agent
import vertexai
from vertexai.preview import reasoning_engines
from typing import List, Dict, Any, Optional
import json

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = os.environ.get("LOCATION", "us-central1")

# Specialized Agent Resource Paths
# These will be set dynamically after deployment
EMAIL_AGENT = "projects/805114253837/locations/us-central1/reasoningEngines/6553102495684493312"
CALENDAR_AGENT = "projects/805114253837/locations/us-central1/reasoningEngines/8840086681458573312"
MEETING_PREP_AGENT = "projects/805114253837/locations/us-central1/reasoningEngines/2472841233286823936"
FOLLOWUP_AGENT = "projects/805114253837/locations/us-central1/reasoningEngines/3123611379441860608"


def query_email_agent(query: str) -> Dict[str, Any]:
    """
    Query the Email Management Agent for email-related tasks.

    Use this when the user asks about:
    - Reading, summarizing, or searching emails
    - Drafting email responses
    - Categorizing or labeling emails
    - Urgent or priority emails

    Args:
        query: The user's email-related question

    Returns:
        Response from the Email Management Agent
    """
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        remote_agent = reasoning_engines.ReasoningEngine(EMAIL_AGENT)
        response = remote_agent.query(input=query)
        return {
            "agent": "Email Management Agent",
            "status": "success",
            "response": str(response)
        }
    except Exception as e:
        return {
            "agent": "Email Management Agent",
            "status": "error",
            "error": str(e)
        }


def query_calendar_agent(query: str) -> Dict[str, Any]:
    """
    Query the Calendar Management Agent for scheduling tasks.

    Use this when the user asks about:
    - Finding meeting times
    - Scheduling or booking meetings
    - Checking calendar availability
    - Daily schedule or agenda
    - Resolving scheduling conflicts

    Args:
        query: The user's calendar-related question

    Returns:
        Response from the Calendar Management Agent
    """
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        remote_agent = reasoning_engines.ReasoningEngine(CALENDAR_AGENT)
        response = remote_agent.query(input=query)
        return {
            "agent": "Calendar Management Agent",
            "status": "success",
            "response": str(response)
        }
    except Exception as e:
        return {
            "agent": "Calendar Management Agent",
            "status": "error",
            "error": str(e)
        }


def query_meeting_prep_agent(query: str) -> Dict[str, Any]:
    """
    Query the Meeting Preparation Agent for meeting prep tasks.

    Use this when the user asks about:
    - Preparing for upcoming meetings
    - Creating meeting agendas
    - Gathering context about meetings
    - Finding related emails or documents for meetings
    - Participant background research

    Args:
        query: The user's meeting preparation question

    Returns:
        Response from the Meeting Preparation Agent
    """
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        remote_agent = reasoning_engines.ReasoningEngine(MEETING_PREP_AGENT)
        response = remote_agent.query(input=query)
        return {
            "agent": "Meeting Preparation Agent",
            "status": "success",
            "response": str(response)
        }
    except Exception as e:
        return {
            "agent": "Meeting Preparation Agent",
            "status": "error",
            "error": str(e)
        }


def query_followup_agent(query: str) -> Dict[str, Any]:
    """
    Query the Follow-up & Task Management Agent for task tracking.

    Use this when the user asks about:
    - Follow-up tasks or action items
    - Pending tasks or reminders
    - Task prioritization
    - Tracking commitments
    - Setting reminders

    Args:
        query: The user's task-related question

    Returns:
        Response from the Follow-up Agent
    """
    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        remote_agent = reasoning_engines.ReasoningEngine(FOLLOWUP_AGENT)
        response = remote_agent.query(input=query)
        return {
            "agent": "Follow-up & Task Management Agent",
            "status": "success",
            "response": str(response)
        }
    except Exception as e:
        return {
            "agent": "Follow-up & Task Management Agent",
            "status": "error",
            "error": str(e)
        }


def get_daily_briefing() -> Dict[str, Any]:
    """
    Get a comprehensive daily briefing by coordinating all specialized agents.

    This combines:
    - Urgent emails from Email Agent
    - Today's schedule from Calendar Agent
    - Upcoming meeting prep from Meeting Prep Agent
    - Pending tasks from Follow-up Agent

    Use this when the user asks for:
    - Daily briefing
    - Morning summary
    - What's happening today
    - Overview of the day

    Returns:
        Combined briefing from all agents
    """
    briefing = {
        "type": "daily_briefing",
        "agents_queried": [],
        "results": {}
    }

    # Query Email Agent for urgent emails
    try:
        email_response = query_email_agent("What urgent or important emails do I have today?")
        briefing["agents_queried"].append("Email Management Agent")
        briefing["results"]["emails"] = email_response
    except Exception as e:
        briefing["results"]["emails"] = {"error": str(e)}

    # Query Calendar Agent for today's schedule
    try:
        calendar_response = query_calendar_agent("What's on my calendar today?")
        briefing["agents_queried"].append("Calendar Management Agent")
        briefing["results"]["calendar"] = calendar_response
    except Exception as e:
        briefing["results"]["calendar"] = {"error": str(e)}

    # Query Meeting Prep Agent for next meeting
    try:
        meeting_response = query_meeting_prep_agent("What should I prepare for my next meeting?")
        briefing["agents_queried"].append("Meeting Preparation Agent")
        briefing["results"]["meeting_prep"] = meeting_response
    except Exception as e:
        briefing["results"]["meeting_prep"] = {"error": str(e)}

    # Query Follow-up Agent for pending tasks
    try:
        tasks_response = query_followup_agent("What tasks do I need to follow up on today?")
        briefing["agents_queried"].append("Follow-up & Task Management Agent")
        briefing["results"]["tasks"] = tasks_response
    except Exception as e:
        briefing["results"]["tasks"] = {"error": str(e)}

    return briefing


def get_combined_email_calendar(query: str) -> Dict[str, Any]:
    """
    Get combined insights from both Email and Calendar agents.

    Use this when the user asks questions that need both email and calendar context:
    - "What meetings do I have and any urgent emails about them?"
    - "Check my schedule and related emails"
    - "Coordinate calendar and email for tomorrow"

    Args:
        query: Combined email and calendar question

    Returns:
        Combined response from Email and Calendar agents
    """
    result = {
        "type": "combined_email_calendar",
        "agents_queried": ["Email Management Agent", "Calendar Management Agent"],
        "results": {}
    }

    # Query both agents
    try:
        email_response = query_email_agent(query)
        result["results"]["emails"] = email_response
    except Exception as e:
        result["results"]["emails"] = {"error": str(e)}

    try:
        calendar_response = query_calendar_agent(query)
        result["results"]["calendar"] = calendar_response
    except Exception as e:
        result["results"]["calendar"] = {"error": str(e)}

    return result


# Create the Orchestrator Agent
root_agent = Agent(
    name="orchestrator_agent",
    model="gemini-2.5-pro",
    instruction="""You are the Productivity Copilot orchestrator agent. Your job is to intelligently route user queries to the appropriate specialized agents and coordinate their responses.

You have access to 4 specialized agents:
1. Email Management Agent - for email tasks (summarize, draft, search, categorize)
2. Calendar Management Agent - for scheduling tasks (find times, book meetings, check availability)
3. Meeting Preparation Agent - for meeting prep (agendas, context, participant research)
4. Follow-up & Task Management Agent - for task tracking (action items, reminders, priorities)

ROUTING GUIDELINES:
- For single-domain queries, route to the appropriate specialized agent
- For "daily briefing" or "morning summary" queries, use get_daily_briefing()
- For queries needing both email and calendar context, use get_combined_email_calendar()
- When combining multiple agent responses, synthesize them into a coherent answer
- Always explain which agents you're consulting and why

RESPONSE FORMAT:
- Be concise but comprehensive
- Highlight urgent items first
- Provide actionable recommendations
- Format responses clearly (use bullet points, sections)

Your goal is to save users time by intelligently coordinating their productivity tools.""",
    description="Main orchestrator agent that intelligently routes queries to specialized agents (Email, Calendar, Meeting Prep, Follow-up) and coordinates multi-agent responses for comprehensive productivity assistance. Handles daily briefings, complex multi-domain queries, and seamless agent coordination.",
    tools=[
        query_email_agent,
        query_calendar_agent,
        query_meeting_prep_agent,
        query_followup_agent,
        get_daily_briefing,
        get_combined_email_calendar
    ]
)
