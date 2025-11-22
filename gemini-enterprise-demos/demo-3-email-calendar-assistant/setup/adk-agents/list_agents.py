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

        # Print all available attributes for debugging
        print(f"Available attributes: {[attr for attr in dir(agent) if not attr.startswith('_')]}")
        print()

        # Try to get common attributes
        if hasattr(agent, 'display_name'):
            print(f"Display Name: {agent.display_name}")

        if hasattr(agent, 'resource_id'):
            print(f"Resource ID: {agent.resource_id}")
            print(f"\nResource Path (for Gemini Enterprise):")
            print(f"  projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{agent.resource_id}")

        if hasattr(agent, 'description'):
            desc = agent.description
            if len(desc) > 100:
                desc = desc[:100] + "..."
            print(f"Description: {desc}")

        print("=" * 70)
        print()

except Exception as e:
    print(f"Error listing agents: {e}")
    import traceback
    traceback.print_exc()
