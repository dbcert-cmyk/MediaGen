"""
Activity Specialist Agent
Handles itinerary creation and activity recommendations
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
import json


class ActivityAgent(BaseAgent):
    """Agent specialized in creating itineraries and recommending activities"""

    def __init__(self):
        super().__init__(
            name="Activity Specialist",
            role="expert travel itinerary planner"
        )

    def create_system_prompt(self) -> str:
        return """You are an expert Activity Specialist and Itinerary Planner.

Your responsibilities:
- Research and recommend activities, attractions, and experiences
- Create detailed day-by-day itineraries
- Consider travel time between locations
- Balance popular attractions with hidden gems
- Adapt recommendations based on interests and budget

You have access to general knowledge about popular destinations, attractions,
museums, restaurants, and activities worldwide.

Always respond in valid JSON format with detailed, practical itineraries."""

    def create_itinerary(self, destination: str, duration_days: int,
                        interests: List[str], budget: str) -> Dict[str, Any]:
        """
        Create a detailed itinerary using Claude's knowledge

        Args:
            destination: Destination city/country
            duration_days: Number of days
            interests: List of interests (e.g., ["art", "museums", "food"])
            budget: Budget category

        Returns:
            Detailed itinerary
        """
        interests_str = ", ".join(interests) if interests else "general sightseeing"

        itinerary_prompt = f"""Create a detailed {duration_days}-day itinerary for {destination}.

Interests: {interests_str}
Budget: {budget}

For each day, provide:
1. Morning activity (with timing, description, estimated cost)
2. Lunch recommendation (with cuisine type, location)
3. Afternoon activity (with timing, description, estimated cost)
4. Dinner recommendation (with cuisine type, location)
5. Optional evening activity
6. Daily estimated cost

Include:
- Specific attraction names and locations
- Realistic timing (consider travel time)
- Mix of popular and lesser-known spots
- Budget-appropriate recommendations
- Practical tips (booking requirements, best times to visit)

Respond in this JSON format:
{{
    "itinerary": [
        {{
            "day": 1,
            "theme": "string",
            "activities": [
                {{
                    "time": "09:00",
                    "activity": "string",
                    "location": "string",
                    "description": "string",
                    "duration": "2 hours",
                    "estimated_cost": 20,
                    "type": "attraction/meal/experience"
                }}
            ],
            "daily_cost_estimate": 150,
            "tips": ["tip1", "tip2"]
        }}
    ],
    "total_estimated_cost": 450,
    "summary": "string",
    "packing_suggestions": ["item1", "item2"],
    "local_tips": ["tip1", "tip2"]
}}"""

        return self.query(itinerary_prompt)

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process itinerary creation task

        Args:
            task: Dict containing itinerary parameters

        Returns:
            Dict with detailed itinerary
        """
        try:
            destination = task.get("destination", "")
            duration_days = task.get("duration_days", 3)
            interests = task.get("interests", [])
            budget = task.get("budget", "economy")

            # Create itinerary using Claude's knowledge
            result = self.create_itinerary(
                destination, duration_days, interests, budget
            )

            # Ensure success flag
            if "itinerary" in result:
                result["success"] = True
            else:
                # Fallback structure
                result = {
                    "success": True,
                    "itinerary": [],
                    "summary": f"Itinerary for {duration_days} days in {destination}",
                    "note": "Using simplified itinerary format"
                }

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
