"""
Hotel Specialist Agent
Handles accommodation search and recommendations
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
import random


class HotelAgent(BaseAgent):
    """Agent specialized in finding and recommending accommodations"""

    def __init__(self):
        super().__init__(
            name="Hotel Specialist",
            role="expert accommodation advisor"
        )

    def create_system_prompt(self) -> str:
        return """You are an expert Hotel Specialist for a travel planning service.

Your responsibilities:
- Search for accommodation options based on location and preferences
- Find hotels near specific attractions or landmarks
- Compare prices, ratings, and amenities
- Recommend the best accommodation based on budget and requirements

Always respond in valid JSON format with clear, structured hotel recommendations."""

    def search_hotels(self, destination: str, checkin_date: str, checkout_date: str,
                     budget: str, guests: int = 2, near: str = None) -> List[Dict]:
        """
        Mock hotel search (in production, this would call Booking.com API or similar)

        Args:
            destination: City or area
            checkin_date: Check-in date
            checkout_date: Check-out date
            budget: Budget category (budget/economy/premium/luxury)
            guests: Number of guests
            near: Optional landmark or attraction to be near

        Returns:
            List of hotel options
        """
        # Mock hotel data generator
        hotel_names = [
            "Grand Plaza Hotel", "City Center Inn", "Riverside Boutique Hotel",
            "Heritage Suites", "Modern Stay Hotel", "Historic District Hotel",
            "Artisan Hotel & Spa", "Downtown Comfort Inn", "Garden View Hotel"
        ]

        amenities_pool = [
            "Free WiFi", "Breakfast included", "Gym", "Pool", "Spa",
            "Restaurant", "Room service", "Airport shuttle", "Parking",
            "Business center", "Concierge", "Laundry service"
        ]

        budget_price_range = {
            "budget": (50, 100),
            "economy": (100, 200),
            "premium": (200, 400),
            "luxury": (400, 800)
        }

        price_min, price_max = budget_price_range.get(budget.lower(), (100, 200))

        hotels = []
        for i in range(4):  # Return 4 options
            name = random.choice(hotel_names)
            price_per_night = random.randint(price_min, price_max)
            rating = round(random.uniform(3.5, 5.0), 1)
            num_amenities = random.randint(4, 8)
            amenities = random.sample(amenities_pool, num_amenities)

            # Calculate nights
            from datetime import datetime
            try:
                checkin = datetime.strptime(checkin_date, "%Y-%m-%d")
                checkout = datetime.strptime(checkout_date, "%Y-%m-%d")
                nights = (checkout - checkin).days
            except:
                nights = 3  # default

            hotel = {
                "hotel_id": f"HT{random.randint(1000, 9999)}",
                "name": name,
                "rating": rating,
                "price_per_night": price_per_night,
                "total_price": price_per_night * nights,
                "currency": "USD",
                "location": destination,
                "distance_to_center": f"{random.uniform(0.5, 5.0):.1f} km",
                "amenities": amenities,
                "room_type": random.choice(["Standard Room", "Deluxe Room", "Suite"]),
                "guests": guests,
                "checkin": checkin_date,
                "checkout": checkout_date,
                "nights": nights
            }

            if near:
                hotel["distance_to_attraction"] = f"{random.uniform(0.2, 3.0):.1f} km from {near}"

            hotels.append(hotel)

        # Sort by rating (best first)
        hotels.sort(key=lambda x: (-x["rating"], x["total_price"]))
        return hotels

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process hotel search task

        Args:
            task: Dict containing hotel search parameters

        Returns:
            Dict with hotel recommendations
        """
        try:
            # Extract task parameters
            destination = task.get("destination", "")
            checkin_date = task.get("checkin_date", "")
            checkout_date = task.get("checkout_date", "")
            budget = task.get("budget", "economy")
            guests = task.get("guests", 2)
            preferences = task.get("preferences", "")
            near = task.get("near", None)

            # Search for hotels
            hotels = self.search_hotels(
                destination, checkin_date, checkout_date,
                budget, guests, near
            )

            # Use Claude to analyze and recommend
            analysis_prompt = f"""Analyze these hotel options and recommend the best one:

Destination: {destination}
Check-in: {checkin_date}
Check-out: {checkout_date}
Budget: {budget}
Guests: {guests}
Preferences: {preferences}
{f"Near: {near}" if near else ""}

Hotel Options:
{json.dumps(hotels, indent=2)}

Provide a recommendation with:
1. The recommended hotel (include full details)
2. Why it's the best choice based on the preferences
3. Alternative options

Respond in this JSON format:
{{
    "recommended_hotel": {{...}},
    "recommendation_reason": "string",
    "alternative_hotels": [{{...}}],
    "summary": "string"
}}"""

            response = self.query(analysis_prompt)

            # Ensure hotels are included
            if "recommended_hotel" not in response:
                response = {
                    "recommended_hotel": hotels[0] if hotels else None,
                    "recommendation_reason": "Best rating and value for money",
                    "alternative_hotels": hotels[1:],
                    "all_hotels": hotels,
                    "summary": f"Found {len(hotels)} hotel options in {destination}"
                }
            else:
                response["all_hotels"] = hotels

            response["success"] = True
            return response

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }


import json
