"""
Host/Coordinator Agent
Orchestrates all specialist agents to create a complete travel plan
"""
from typing import Dict, Any
from .base_agent import BaseAgent
from .flight_agent import FlightAgent
from .hotel_agent import HotelAgent
from .activity_agent import ActivityAgent
import json
from datetime import datetime, timedelta


class CoordinatorAgent(BaseAgent):
    """Main orchestrator that coordinates all specialist agents"""

    def __init__(self):
        super().__init__(
            name="Travel Coordinator",
            role="expert travel planning coordinator"
        )

        # Initialize specialist agents
        self.flight_agent = FlightAgent()
        self.hotel_agent = HotelAgent()
        self.activity_agent = ActivityAgent()

    def create_system_prompt(self) -> str:
        return """You are the Travel Coordinator, the main orchestrator for a travel planning service.

Your responsibilities:
- Parse user travel requests and extract key information
- Coordinate with specialist agents (Flight, Hotel, Activity)
- Combine all information into a cohesive travel plan
- Present the final plan in a beautiful, user-friendly format

You manage the workflow and ensure all components work together seamlessly."""

    def parse_user_request(self, user_request: str) -> Dict[str, Any]:
        """
        Parse the user's travel request using Claude to extract structured information

        Args:
            user_request: Natural language travel request

        Returns:
            Structured dict with trip parameters
        """
        parse_prompt = f"""Parse this travel request and extract structured information:

User Request: "{user_request}"

Extract and infer:
- Destination (city/country)
- Duration (number of days)
- Budget level (budget/economy/premium/luxury)
- Interests/preferences (list)
- Number of travelers
- Approximate dates (if mentioned, otherwise suggest dates 30 days from now)
- Origin city (if mentioned, otherwise use "New York" as default)

Respond in this JSON format:
{{
    "destination": "string",
    "origin": "string",
    "duration_days": number,
    "budget": "budget/economy/premium/luxury",
    "interests": ["interest1", "interest2"],
    "travelers": number,
    "departure_date": "YYYY-MM-DD",
    "return_date": "YYYY-MM-DD",
    "special_requests": "string"
}}"""

        result = self.query(parse_prompt)

        # Validate and set defaults
        if not result.get("destination"):
            result = {
                "destination": "Paris",
                "origin": "New York",
                "duration_days": 3,
                "budget": "economy",
                "interests": ["sightseeing"],
                "travelers": 1,
                "departure_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "return_date": (datetime.now() + timedelta(days=33)).strftime("%Y-%m-%d"),
                "special_requests": ""
            }

        return result

    def create_travel_plan(self, user_request: str) -> Dict[str, Any]:
        """
        Main orchestration method - creates complete travel plan

        Args:
            user_request: User's travel request in natural language

        Returns:
            Complete travel plan with all components
        """
        try:
            print(f"\n{'='*60}")
            print(f"🌍 TRAVEL COORDINATOR: Processing request...")
            print(f"{'='*60}\n")

            # Step 1: Parse user request
            print("📋 Step 1: Parsing travel request...")
            trip_params = self.parse_user_request(user_request)
            print(f"✅ Parsed: {trip_params['duration_days']} days in {trip_params['destination']}")
            print(f"   Budget: {trip_params['budget']}, Interests: {', '.join(trip_params['interests'])}\n")

            # Step 2: Search for flights
            print("✈️  Step 2: Searching for flights...")
            flight_task = {
                "origin": trip_params["origin"],
                "destination": trip_params["destination"],
                "departure_date": trip_params["departure_date"],
                "return_date": trip_params["return_date"],
                "budget": trip_params["budget"],
                "passengers": trip_params["travelers"]
            }
            flight_results = self.flight_agent.process_task(flight_task)
            if flight_results.get("success"):
                print(f"✅ Found {len(flight_results.get('all_flights', []))} flight options\n")
            else:
                print(f"⚠️  Flight search had issues: {flight_results.get('error', 'Unknown error')}\n")

            # Step 3: Search for hotels
            print("🏨 Step 3: Searching for accommodations...")
            # Determine what to be near based on interests
            near_attraction = None
            if "art" in trip_params["interests"] or "museum" in trip_params["interests"]:
                near_attraction = "art museums"
            elif "beach" in trip_params["interests"]:
                near_attraction = "beach"

            hotel_task = {
                "destination": trip_params["destination"],
                "checkin_date": trip_params["departure_date"],
                "checkout_date": trip_params["return_date"],
                "budget": trip_params["budget"],
                "guests": trip_params["travelers"],
                "preferences": ", ".join(trip_params["interests"]),
                "near": near_attraction
            }
            hotel_results = self.hotel_agent.process_task(hotel_task)
            if hotel_results.get("success"):
                print(f"✅ Found {len(hotel_results.get('all_hotels', []))} hotel options\n")
            else:
                print(f"⚠️  Hotel search had issues: {hotel_results.get('error', 'Unknown error')}\n")

            # Step 4: Create itinerary
            print("📅 Step 4: Creating detailed itinerary...")
            activity_task = {
                "destination": trip_params["destination"],
                "duration_days": trip_params["duration_days"],
                "interests": trip_params["interests"],
                "budget": trip_params["budget"]
            }
            activity_results = self.activity_agent.process_task(activity_task)
            if activity_results.get("success"):
                itinerary_days = len(activity_results.get("itinerary", []))
                print(f"✅ Created {itinerary_days}-day itinerary\n")
            else:
                print(f"⚠️  Itinerary creation had issues: {activity_results.get('error', 'Unknown error')}\n")

            # Step 5: Combine everything into final plan
            print("📦 Step 5: Assembling final travel plan...")
            complete_plan = {
                "success": True,
                "trip_summary": {
                    "destination": trip_params["destination"],
                    "origin": trip_params["origin"],
                    "duration": f"{trip_params['duration_days']} days",
                    "dates": f"{trip_params['departure_date']} to {trip_params['return_date']}",
                    "travelers": trip_params["travelers"],
                    "budget_level": trip_params["budget"]
                },
                "flights": flight_results,
                "accommodation": hotel_results,
                "itinerary": activity_results,
                "user_request": user_request
            }

            # Calculate total estimated cost
            total_cost = 0
            if flight_results.get("recommended_flight"):
                total_cost += flight_results["recommended_flight"].get("total_price", 0)
            if hotel_results.get("recommended_hotel"):
                total_cost += hotel_results["recommended_hotel"].get("total_price", 0)
            if activity_results.get("total_estimated_cost"):
                total_cost += activity_results["total_estimated_cost"]

            complete_plan["estimated_total_cost"] = {
                "amount": total_cost,
                "currency": "USD",
                "breakdown": {
                    "flights": flight_results.get("recommended_flight", {}).get("total_price", 0),
                    "accommodation": hotel_results.get("recommended_hotel", {}).get("total_price", 0),
                    "activities": activity_results.get("total_estimated_cost", 0)
                }
            }

            print(f"✅ Complete travel plan assembled!\n")
            print(f"{'='*60}")
            print(f"💰 Estimated Total Cost: ${total_cost:,.2f} USD")
            print(f"{'='*60}\n")

            return complete_plan

        except Exception as e:
            print(f"\n❌ Error creating travel plan: {str(e)}\n")
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }

    def format_travel_plan_markdown(self, plan: Dict[str, Any]) -> str:
        """
        Convert the travel plan to beautiful markdown format

        Args:
            plan: Complete travel plan dict

        Returns:
            Markdown formatted string
        """
        if not plan.get("success"):
            return f"# ❌ Error\n\n{plan.get('error', 'Unknown error occurred')}"

        md = []
        md.append("# 🌍 Your Complete Travel Plan\n")

        # Trip Summary
        summary = plan["trip_summary"]
        md.append("## 📋 Trip Summary\n")
        md.append(f"- **Destination:** {summary['destination']}")
        md.append(f"- **Origin:** {summary['origin']}")
        md.append(f"- **Duration:** {summary['duration']}")
        md.append(f"- **Dates:** {summary['dates']}")
        md.append(f"- **Travelers:** {summary['travelers']}")
        md.append(f"- **Budget Level:** {summary['budget_level'].title()}\n")

        # Total Cost
        if "estimated_total_cost" in plan:
            cost = plan["estimated_total_cost"]
            md.append("## 💰 Estimated Total Cost\n")
            md.append(f"### **${cost['amount']:,.2f} {cost['currency']}**\n")
            md.append("**Breakdown:**")
            md.append(f"- Flights: ${cost['breakdown']['flights']:,.2f}")
            md.append(f"- Accommodation: ${cost['breakdown']['accommodation']:,.2f}")
            md.append(f"- Activities & Food: ${cost['breakdown']['activities']:,.2f}\n")

        # Flights
        md.append("---\n")
        md.append("## ✈️ Recommended Flight\n")
        flights = plan.get("flights", {})
        if flights.get("recommended_flight"):
            flight = flights["recommended_flight"]
            md.append(f"**{flight['airline']}** - Flight {flight.get('flight_id', 'N/A')}")
            md.append(f"- **Price:** ${flight['total_price']:,.2f} {flight['currency']} ({flight.get('price_per_person', 0)} per person)")
            md.append(f"- **Duration:** {flight['duration']}")
            md.append(f"- **Stops:** {flight['stops']}")
            md.append(f"- **Departure:** {flight['departure']['date']} at {flight['departure']['time']}")
            md.append(f"- **Return:** {flight['return_flight']['departure_date']} at {flight['return_flight']['departure_time']}\n")

            if flights.get("recommendation_reason"):
                md.append(f"**Why this flight?** {flights['recommendation_reason']}\n")

        # Accommodation
        md.append("---\n")
        md.append("## 🏨 Recommended Accommodation\n")
        hotels = plan.get("accommodation", {})
        if hotels.get("recommended_hotel"):
            hotel = hotels["recommended_hotel"]
            md.append(f"**{hotel['name']}** ⭐ {hotel.get('rating', 'N/A')}/5.0")
            md.append(f"- **Price:** ${hotel['total_price']:,.2f} {hotel['currency']} (${hotel['price_per_night']}/night × {hotel.get('nights', 1)} nights)")
            md.append(f"- **Room Type:** {hotel.get('room_type', 'Standard')}")
            md.append(f"- **Location:** {hotel.get('distance_to_center', 'City center')}")

            if hotel.get("amenities"):
                md.append(f"- **Amenities:** {', '.join(hotel['amenities'][:5])}")

            if hotels.get("recommendation_reason"):
                md.append(f"\n**Why this hotel?** {hotels['recommendation_reason']}\n")

        # Itinerary
        md.append("---\n")
        md.append("## 📅 Day-by-Day Itinerary\n")
        itinerary_data = plan.get("itinerary", {})
        if itinerary_data.get("itinerary"):
            for day in itinerary_data["itinerary"]:
                day_num = day.get("day", 1)
                theme = day.get("theme", "Exploration")
                md.append(f"### Day {day_num}: {theme}\n")

                if day.get("activities"):
                    for activity in day["activities"]:
                        time = activity.get("time", "")
                        name = activity.get("activity", "Activity")
                        location = activity.get("location", "")
                        cost = activity.get("estimated_cost", 0)

                        md.append(f"**{time}** - {name}")
                        if location:
                            md.append(f"  - 📍 {location}")
                        if activity.get("description"):
                            md.append(f"  - {activity['description']}")
                        if cost > 0:
                            md.append(f"  - 💵 ~${cost}")
                        md.append("")

                if day.get("daily_cost_estimate"):
                    md.append(f"*Daily Budget: ~${day['daily_cost_estimate']}*\n")

        # Additional Tips
        if itinerary_data.get("local_tips"):
            md.append("---\n")
            md.append("## 💡 Local Tips\n")
            for tip in itinerary_data["local_tips"]:
                md.append(f"- {tip}")
            md.append("")

        if itinerary_data.get("packing_suggestions"):
            md.append("## 🎒 Packing Suggestions\n")
            for item in itinerary_data["packing_suggestions"]:
                md.append(f"- {item}")
            md.append("")

        md.append("---\n")
        md.append("*This itinerary was created by your AI Travel Planning Team* ✨")

        return "\n".join(md)
