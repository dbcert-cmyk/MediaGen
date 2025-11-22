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

        # Extract key information from api_resource
        api_resource = agent_data.get('api_resource', {})

        display_name = api_resource.get('display_name', 'N/A')
        resource_path = api_resource.get('name', 'N/A')
        description = api_resource.get('description', '')
        create_time = api_resource.get('create_time', 'N/A')

        # Display clean output
        print(f"\nDisplay Name: {display_name}")
        print(f"Resource Path: {resource_path}")
        if description:
            print(f"Description: {description}")
        print(f"Created: {create_time}")

        print(f"\n📋 Copy this resource path for Gemini Enterprise:")
        print(f"   {resource_path}")

        print("=" * 70)
        print()

    if count == 0:
        print("No agents found. Have you deployed any agents yet?")

except Exception as e:
    print(f"Error listing agents: {e}")
    import traceback
    traceback.print_exc()
