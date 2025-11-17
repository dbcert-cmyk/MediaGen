#!/usr/bin/env python3
"""
Test script for Multi-Agent Travel Planner
Run this to verify your setup and see the agents in action
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agents import CoordinatorAgent
import json


def test_api_key():
    """Test if API key is configured"""
    print("=" * 60)
    print("🔑 Testing API Key Configuration...")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found!")
        print("\nPlease set your API key:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("  or create a .env file with ANTHROPIC_API_KEY=your-key-here")
        return False

    print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")
    return True


def test_agent_initialization():
    """Test agent initialization"""
    print("\n" + "=" * 60)
    print("🤖 Testing Agent Initialization...")
    print("=" * 60)

    try:
        coordinator = CoordinatorAgent()
        print(f"✅ Coordinator Agent: {coordinator.name}")
        print(f"✅ Flight Agent: {coordinator.flight_agent.name}")
        print(f"✅ Hotel Agent: {coordinator.hotel_agent.name}")
        print(f"✅ Activity Agent: {coordinator.activity_agent.name}")
        return True
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False


def test_travel_planning():
    """Test complete travel planning workflow"""
    print("\n" + "=" * 60)
    print("✈️ Testing Complete Travel Planning Workflow...")
    print("=" * 60)

    try:
        # Sample request
        test_request = "Plan me a 3-day budget trip to Paris focused on art and museums"
        print(f"\n📝 Test Request: '{test_request}'\n")

        # Initialize coordinator
        coordinator = CoordinatorAgent()

        # Create travel plan
        print("🚀 Creating travel plan...\n")
        plan = coordinator.create_travel_plan(test_request)

        # Check if successful
        if plan.get("success"):
            print("\n✅ Travel plan created successfully!")

            # Display summary
            print("\n" + "=" * 60)
            print("📋 Plan Summary")
            print("=" * 60)
            summary = plan.get("trip_summary", {})
            for key, value in summary.items():
                print(f"  {key.title()}: {value}")

            # Display cost
            if "estimated_total_cost" in plan:
                cost = plan["estimated_total_cost"]
                print(f"\n💰 Total Estimated Cost: ${cost['amount']:,.2f} {cost['currency']}")

            # Save to file
            output_file = "test_travel_plan.json"
            with open(output_file, 'w') as f:
                json.dump(plan, f, indent=2)
            print(f"\n💾 Full plan saved to: {output_file}")

            # Generate markdown
            markdown = coordinator.format_travel_plan_markdown(plan)
            markdown_file = "test_travel_plan.md"
            with open(markdown_file, 'w') as f:
                f.write(markdown)
            print(f"💾 Markdown plan saved to: {markdown_file}")

            return True
        else:
            print(f"\n❌ Travel planning failed: {plan.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ Error during travel planning: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "🌍" * 20)
    print("MULTI-AGENT TRAVEL PLANNER - TEST SUITE")
    print("🌍" * 20 + "\n")

    # Run tests
    tests_passed = 0
    total_tests = 3

    if test_api_key():
        tests_passed += 1

    if test_agent_initialization():
        tests_passed += 1

    if test_travel_planning():
        tests_passed += 1

    # Final summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("\n🎉 All tests passed! Your setup is ready!")
        print("\nNext steps:")
        print("  1. Run the Streamlit app: cd ui && streamlit run streamlit_app.py")
        print("  2. Open http://localhost:8501 in your browser")
        print("  3. Start planning amazing trips!")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")

    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
