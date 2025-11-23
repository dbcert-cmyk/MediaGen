#!/usr/bin/env python3
"""
Delete old/duplicate agents from Vertex AI Agent Engine
Keeps only the 4 most recent agents (Email, Calendar, Meeting Prep, Follow-up)
"""

import os
import vertexai
from vertexai._genai.agent_engines import AgentEngines

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = "us-central1"

# Agents to KEEP (most recent deployments from 2025-11-22 23:*)
KEEP_AGENTS = [
    "3123611379441860608",  # Follow-up & Task Management Agent (23:35)
    "2472841233286823936",  # Meeting Preparation Agent (23:30)
    "8840086681458573312",  # Calendar Management Agent (23:24)
    "6553102495684493312",  # Email Management Agent (23:17)
]

# Agents to DELETE (old duplicates and test agents)
DELETE_AGENTS = [
    "3823921121497972736",  # Follow-up (old - 21:43)
    "5088588191858950144",  # Meeting Prep (old - 21:29)
    "5127713213621731328",  # Calendar (old - 21:24)
    "8450243838714314752",  # Email (old - 21:16)
    "5744706362571489280",  # Property Management Agent (test)
    "4058108302121238528",  # Gemini Enterprise Agent (test)
    "1222810861714800640",  # SearchAgent (test)
]


def delete_agents():
    """Delete old/duplicate agents"""

    print("=" * 70)
    print("Deleting Old/Duplicate Agents")
    print("=" * 70)
    print()

    # Initialize Vertex AI
    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION
    )

    client = AgentEngines()

    deleted_count = 0
    failed_count = 0

    for agent_id in DELETE_AGENTS:
        try:
            print(f"Deleting agent: {agent_id}...")

            # Get the agent
            agent_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{agent_id}"
            agent = client.get(name=agent_name)

            # Get display name if available
            agent_data = agent.model_dump()
            display_name = agent_data.get('api_resource', {}).get('display_name', 'Unknown')

            print(f"  Display Name: {display_name}")

            # Delete the agent
            agent.delete()

            print(f"  ✅ Deleted successfully")
            deleted_count += 1
            print()

        except Exception as e:
            print(f"  ❌ Error deleting: {e}")
            failed_count += 1
            print()

    # Summary
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print(f"✅ Deleted: {deleted_count} agents")
    if failed_count > 0:
        print(f"❌ Failed: {failed_count} agents")
    print()

    print("Remaining agents (run list_agents.py to verify):")
    print(f"  - {len(KEEP_AGENTS)} active agents")
    print()


if __name__ == "__main__":
    print()
    print("⚠️  WARNING: This will permanently delete the following agents:")
    print()

    for agent_id in DELETE_AGENTS:
        print(f"  - {agent_id}")

    print()
    response = input("Do you want to continue? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        delete_agents()
    else:
        print("Cancelled. No agents were deleted.")
