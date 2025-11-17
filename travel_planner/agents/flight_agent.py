"""
Flight Specialist Agent
Handles flight search and recommendations
"""
from typing import Dict, Any, List
from .base_agent import BaseAgent
import random
from datetime import datetime, timedelta


class FlightAgent(BaseAgent):
    """Agent specialized in finding and recommending flights"""

    def __init__(self):
        super().__init__(
            name="Flight Specialist",
            role="expert flight booking advisor"
        )

    def create_system_prompt(self) -> str:
        return """You are an expert Flight Specialist for a travel planning service.

Your responsibilities:
- Search for flight options based on user requirements
- Compare prices, airlines, and routes
- Recommend the best flight options based on budget and preferences
- Provide detailed flight information including layovers, duration, and costs

Always respond in valid JSON format with clear, structured flight recommendations."""

    def search_flights(self, origin: str, destination: str, departure_date: str,
                      return_date: str, budget: str, passengers: int = 1) -> List[Dict]:
        """
        Mock flight search (in production, this would call a real API like Amadeus or Skyscanner)

        Args:
            origin: Departure city/airport
            destination: Arrival city/airport
            departure_date: Departure date
            return_date: Return date
            budget: Budget category (budget/economy/premium)
            passengers: Number of passengers

        Returns:
            List of flight options
        """
        # Mock flight data generator
        airlines = ["United Airlines", "American Airlines", "Delta", "Air France",
                   "British Airways", "Lufthansa", "Emirates"]

        budget_multiplier = {
            "budget": 1.0,
            "economy": 1.5,
            "premium": 2.5
        }

        base_price = random.randint(300, 800)
        multiplier = budget_multiplier.get(budget.lower(), 1.0)

        flights = []
        for i in range(3):  # Return 3 options
            airline = random.choice(airlines)
            price = int(base_price * multiplier * (1 + random.uniform(-0.2, 0.3)))
            duration_hours = random.randint(8, 20)
            stops = random.choice([0, 1, 1, 2])  # More likely to have 1 stop

            flight = {
                "flight_id": f"FL{random.randint(1000, 9999)}",
                "airline": airline,
                "price_per_person": price,
                "total_price": price * passengers,
                "currency": "USD",
                "duration": f"{duration_hours}h {random.randint(0, 55)}m",
                "stops": stops,
                "departure": {
                    "airport": origin,
                    "date": departure_date,
                    "time": f"{random.randint(6, 22):02d}:{random.choice(['00', '15', '30', '45'])}"
                },
                "arrival": {
                    "airport": destination,
                    "date": departure_date,
                    "time": f"{random.randint(6, 22):02d}:{random.choice(['00', '15', '30', '45'])}"
                },
                "return_flight": {
                    "departure_date": return_date,
                    "departure_time": f"{random.randint(6, 22):02d}:{random.choice(['00', '15', '30', '45'])}",
                    "arrival_time": f"{random.randint(6, 22):02d}:{random.choice(['00', '15', '30', '45'])}"
                }
            }
            flights.append(flight)

        # Sort by price
        flights.sort(key=lambda x: x["total_price"])
        return flights

    def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process flight search task

        Args:
            task: Dict containing flight search parameters

        Returns:
            Dict with flight recommendations
        """
        try:
            # Extract task parameters
            origin = task.get("origin", "")
            destination = task.get("destination", "")
            departure_date = task.get("departure_date", "")
            return_date = task.get("return_date", "")
            budget = task.get("budget", "economy")
            passengers = task.get("passengers", 1)

            # Search for flights
            flights = self.search_flights(
                origin, destination, departure_date,
                return_date, budget, passengers
            )

            # Use Claude to analyze and recommend the best options
            analysis_prompt = f"""Analyze these flight options and recommend the best one:

Origin: {origin}
Destination: {destination}
Departure: {departure_date}
Return: {return_date}
Budget: {budget}
Passengers: {passengers}

Flight Options:
{json.dumps(flights, indent=2)}

Provide a recommendation with:
1. The recommended flight (include full details)
2. Why it's the best choice
3. Alternatives if the user wants different options

Respond in this JSON format:
{{
    "recommended_flight": {{...}},
    "recommendation_reason": "string",
    "alternative_flights": [{{...}}],
    "summary": "string"
}}"""

            response = self.query(analysis_prompt)

            # Ensure flights are included
            if "recommended_flight" not in response:
                response = {
                    "recommended_flight": flights[0] if flights else None,
                    "recommendation_reason": "Best price and convenience",
                    "alternative_flights": flights[1:],
                    "all_flights": flights,
                    "summary": f"Found {len(flights)} flight options from {origin} to {destination}"
                }
            else:
                response["all_flights"] = flights

            response["success"] = True
            return response

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }


import json
