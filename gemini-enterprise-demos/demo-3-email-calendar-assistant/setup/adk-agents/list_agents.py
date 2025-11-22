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

    count = 0
    for agent in agents:
        count += 1
        print("=" * 70)
        print(f"Agent #{count}")
        print("=" * 70)

        # Dump the model data
        agent_data = agent.model_dump()

        print(f"\nAgent Data:")
        for key, value in agent_data.items():
            if isinstance(value, str) and len(value) > 100:
                print(f"  {key}: {value[:100]}...")
            else:
                print(f"  {key}: {value}")

        print()

        # Extract resource path if available
        if 'resource_id' in agent_data:
            resource_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{agent_data['resource_id']}"
            print(f"📋 Resource Path for Gemini Enterprise:")
            print(f"   {resource_path}")

        print("=" * 70)
        print()

    if count == 0:
        print("No agents found. Have you deployed any agents yet?")

except Exception as e:
    print(f"Error listing agents: {e}")
    import traceback
    traceback.print_exc()
