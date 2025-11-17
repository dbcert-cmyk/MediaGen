"""
Base Agent Class for the Multi-Agent Travel Planner
This provides the foundation for all specialist agents
"""
import json
from typing import Dict, Any, Optional, List
from anthropic import Anthropic
import os


class BaseAgent:
    """Base class for all travel planning agents"""

    def __init__(self, name: str, role: str, model: str = "claude-3-5-sonnet-20241022"):
        self.name = name
        self.role = role
        self.model = model
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.conversation_history: List[Dict] = []

    def create_system_prompt(self) -> str:
        """Override this in subclasses to define agent-specific behavior"""
        return f"""You are {self.name}, a {self.role} for a travel planning service.

Your job is to provide expert assistance in your domain. Always respond in valid JSON format
with the structure specified in each request."""

    def query(self, user_message: str, response_format: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Send a query to Claude and get a structured response

        Args:
            user_message: The message/query to send
            response_format: Optional dict describing expected JSON structure

        Returns:
            Parsed JSON response
        """
        system_prompt = self.create_system_prompt()

        if response_format:
            system_prompt += f"\n\nExpected response format:\n{json.dumps(response_format, indent=2)}"

        messages = [{"role": "user", "content": user_message}]

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages
            )

            # Extract text content
            content = response.content[0].text

            # Try to parse as JSON
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, wrap in a response
                return {
                    "success": False,
                    "error": "Invalid JSON response",
                    "raw_content": content
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Override this method in specialist agents to handle specific tasks

        Args:
            task: Dictionary containing task details

        Returns:
            Dictionary with results
        """
        raise NotImplementedError("Subclasses must implement process_task()")
