#!/usr/bin/env python3
"""
Update existing ADK agents in Vertex AI Agent Engine
"""

import os
import sys
import importlib.util
from pathlib import Path
import vertexai

PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = os.environ.get("LOCATION", "us-central1")

# Agents to update with their resource IDs
AGENTS_TO_UPDATE = {
    "email_agent": "6553102495684493312",
    "calendar_agent": "8840086681458573312"
}

def update_agent(agent_name: str, agent_id: str):
    """Update an existing deployed agent"""
    print(f"\n{'='*60}")
    print(f"Updating {agent_name} (ID: {agent_id})")
    print(f"{'='*60}\n")

    # Agent directory
    agent_dir = Path(__file__).parent / agent_name
    agent_file = agent_dir / "agent.py"

    if not agent_file.exists():
        print(f"❌ Error: Agent file not found: {agent_file}")
        return False

    print(f"✓ Found agent file: {agent_file}")

    # Initialize Vertex AI
    client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

    # Load the agent module
    print(f"✓ Loading agent module...")
    sys.path.insert(0, str(agent_dir))

    try:
        # Import the agent module
        spec = importlib.util.spec_from_file_location(agent_name, agent_file)
        agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_module)

        # Get the root_agent
        if not hasattr(agent_module, 'root_agent'):
            print(f"❌ Error: Agent file must export 'root_agent'")
            return False

        root_agent = agent_module.root_agent
        print(f"✓ Loaded root_agent: {root_agent.name}")

    except Exception as e:
        print(f"❌ Error loading agent: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Update the agent
    try:
        print(f"\n{'='*60}")
        print(f"Updating agent (this may take a few minutes)...")
        print(f"{'='*60}\n")

        # Get existing agent
        resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{agent_id}"
        existing_agent = client.agent_engines.get(name=resource_name)

        print(f"✓ Found existing agent: {existing_agent.display_name}")

        # Delete old agent
        print(f"✓ Deleting old agent...")
        existing_agent.delete()

        # Wait a moment
        import time
        time.sleep(5)

        # Deploy new version (create with same config)
        print(f"✓ Deploying new version...")

        display_name_map = {
            "email_agent": "Email Management Agent",
            "calendar_agent": "Calendar Management Agent"
        }

        config = {
            "display_name": display_name_map.get(agent_name, agent_name),
            "description": getattr(root_agent, 'description', ''),
            "requirements": [
                "google-cloud-aiplatform>=1.112",
                "google-adk",
                "google-api-python-client",
                "google-auth",
                "google-auth-httplib2",
                "google-auth-oauthlib",
                "google-cloud-firestore",
                "google-cloud-storage",
                "python-dateutil",
                "pydantic",
                "cloudpickle"
            ],
            "staging_bucket": "gs://adk-agents-staging"
        }

        remote_agent = client.agent_engines.create(
            agent=root_agent,
            config=config
        )

        print(f"\n{'='*60}")
        print(f"✅ Update successful!")
        print(f"{'='*60}\n")

        if hasattr(remote_agent, 'name'):
            print(f"New Resource Name: {remote_agent.name}")
        if hasattr(remote_agent, 'resource_id'):
            print(f"New Resource ID: {remote_agent.resource_id}")

        return True

    except Exception as e:
        print(f"\n❌ Update failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print(f"\nUpdating agents in project: {PROJECT_ID}, location: {LOCATION}")

    updated = 0
    failed = 0

    for agent_name, agent_id in AGENTS_TO_UPDATE.items():
        if update_agent(agent_name, agent_id):
            updated += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"Summary: {updated} updated, {failed} failed")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
