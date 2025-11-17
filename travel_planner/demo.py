#!/usr/bin/env python3
"""
Quick Demo of Multi-Agent Travel Planner (No API Key Required)
This demonstrates the agent architecture without making actual API calls
"""
import json


def demo_agent_structure():
    """Demonstrate the agent structure"""
    print("=" * 70)
    print("🌍 MULTI-AGENT TRAVEL PLANNER - ARCHITECTURE DEMO")
    print("=" * 70)

    print("\n📋 Agent Hierarchy:\n")
    print("  CoordinatorAgent (Host)")
    print("    ├── FlightAgent (Specialist)")
    print("    │   └── Searches flights, compares prices, recommends best options")
    print("    ├── HotelAgent (Specialist)")
    print("    │   └── Finds accommodations, matches to preferences")
    print("    └── ActivityAgent (Specialist)")
    print("        └── Creates detailed itineraries, recommends attractions")

    print("\n🔄 Workflow:\n")
    steps = [
        "1. User: 'Plan a 3-day budget trip to Paris for art'",
        "2. Coordinator: Parses request into structured data",
        "3. FlightAgent: Searches for flights (mock/real API)",
        "4. HotelAgent: Searches for hotels near art museums",
        "5. ActivityAgent: Creates 3-day art-focused itinerary",
        "6. Coordinator: Combines all results into final plan",
        "7. UI: Displays beautiful markdown travel plan"
    ]

    for step in steps:
        print(f"  {step}")


def demo_sample_output():
    """Show sample travel plan structure"""
    print("\n" + "=" * 70)
    print("📦 SAMPLE OUTPUT STRUCTURE")
    print("=" * 70)

    sample_plan = {
        "success": True,
        "trip_summary": {
            "destination": "Paris, France",
            "origin": "New York, NY",
            "duration": "3 days",
            "dates": "2024-04-15 to 2024-04-18",
            "travelers": 1,
            "budget_level": "budget"
        },
        "estimated_total_cost": {
            "amount": 1450.00,
            "currency": "USD",
            "breakdown": {
                "flights": 650.00,
                "accommodation": 450.00,
                "activities": 350.00
            }
        },
        "flights": {
            "recommended_flight": {
                "airline": "Air France",
                "price": 650.00,
                "duration": "7h 30m",
                "stops": 0
            }
        },
        "accommodation": {
            "recommended_hotel": {
                "name": "Art District Hotel",
                "rating": 4.2,
                "price_per_night": 150.00,
                "total_price": 450.00,
                "distance_to_attraction": "0.5 km from Louvre Museum"
            }
        },
        "itinerary": {
            "itinerary": [
                {
                    "day": 1,
                    "theme": "Classic Parisian Art",
                    "activities": [
                        {
                            "time": "09:00",
                            "activity": "Louvre Museum",
                            "description": "Explore world-famous art collection",
                            "estimated_cost": 15
                        }
                    ]
                }
            ],
            "total_estimated_cost": 350
        }
    }

    print("\n" + json.dumps(sample_plan, indent=2))


def demo_key_features():
    """Highlight key features"""
    print("\n" + "=" * 70)
    print("✨ KEY FEATURES")
    print("=" * 70)

    features = [
        ("🗣️ Natural Language", "Just describe your trip in plain English"),
        ("🤖 Multi-Agent System", "Specialized AI agents work in parallel"),
        ("💰 Budget Aware", "Recommendations match your budget level"),
        ("📅 Complete Itinerary", "Day-by-day plans with timing and costs"),
        ("🎨 Beautiful UI", "Clean Streamlit interface with examples"),
        ("📥 Export Options", "Download as Markdown or JSON"),
        ("🔌 API Ready", "Easy to integrate real travel APIs"),
        ("⚡ Fast & Efficient", "Parallel agent execution")
    ]

    for icon_name, description in features:
        print(f"\n  {icon_name}")
        print(f"    └─ {description}")


def demo_usage_examples():
    """Show usage examples"""
    print("\n" + "=" * 70)
    print("💡 EXAMPLE REQUESTS")
    print("=" * 70)

    examples = [
        {
            "request": "Plan a 3-day budget trip to Paris focused on art",
            "parsed": {
                "destination": "Paris",
                "duration": 3,
                "budget": "budget",
                "interests": ["art", "museums"]
            }
        },
        {
            "request": "5-day luxury vacation in Tokyo with great food",
            "parsed": {
                "destination": "Tokyo",
                "duration": 5,
                "budget": "luxury",
                "interests": ["food", "culture"]
            }
        },
        {
            "request": "Family trip to Orlando, 4 days, theme parks",
            "parsed": {
                "destination": "Orlando",
                "duration": 4,
                "budget": "economy",
                "interests": ["theme parks", "family"]
            }
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n  Example {i}:")
        print(f"    Input:  \"{example['request']}\"")
        print(f"    Parsed: {json.dumps(example['parsed'], indent=12)[12:]}")


def demo_tech_stack():
    """Show technology stack"""
    print("\n" + "=" * 70)
    print("🛠️ TECHNOLOGY STACK")
    print("=" * 70)

    tech = [
        ("Anthropic Claude", "LLM for agent intelligence (Claude 3.5 Sonnet)"),
        ("Streamlit", "Web UI framework"),
        ("Python 3.8+", "Core programming language"),
        ("JSON", "Inter-agent communication protocol"),
        ("Mock APIs", "Demo flight/hotel data (easily replaceable)"),
    ]

    for name, description in tech:
        print(f"\n  📌 {name}")
        print(f"     └─ {description}")

    print("\n  🔜 Future Integrations:")
    print("     ├─ Amadeus API (flights)")
    print("     ├─ Booking.com API (hotels)")
    print("     └─ Google Places API (activities)")


def main():
    """Run demo"""
    demo_agent_structure()
    demo_sample_output()
    demo_key_features()
    demo_usage_examples()
    demo_tech_stack()

    print("\n" + "=" * 70)
    print("🚀 GETTING STARTED")
    print("=" * 70)
    print("\n  1. Install dependencies:")
    print("     $ pip install -r requirements.txt")
    print("\n  2. Set up API key:")
    print("     $ export ANTHROPIC_API_KEY='your-key-here'")
    print("\n  3. Run the app:")
    print("     $ cd ui && streamlit run streamlit_app.py")
    print("\n  4. Or test without UI:")
    print("     $ python test_planner.py")

    print("\n" + "=" * 70)
    print("📚 Learn More: See README.md for full documentation")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
