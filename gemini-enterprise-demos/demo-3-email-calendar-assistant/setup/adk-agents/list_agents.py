#!/usr/bin/env python3
"""List deployed ADK agents in Vertex AI Agent Engine"""

import os
import vertexai

PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = os.environ.get("LOCATION", "us-central1")

print(f"Listing agents in project: {PROJECT_ID}, location: {LOCATION}\n")

client = vertexai.Client(
    project=PROJECT_ID,
    location=LOCATION
)

try:
    # List all deployed agents
    agents = client.agent_engines.list()

    for agent in agents:
        print("=" * 70)
        print(f"Display Name: {getattr(agent, 'display_name', 'N/A')}")
        print(f"Resource Name: {agent.name}")

        if hasattr(agent, 'description'):
            print(f"Description: {agent.description[:100]}...")

        print(f"\nFor Gemini Enterprise registration, use this resource path:")
        print(f"  {agent.name}")
        print("=" * 70)
        print()

except Exception as e:
    print(f"Error listing agents: {e}")
    import traceback
    traceback.print_exc()
