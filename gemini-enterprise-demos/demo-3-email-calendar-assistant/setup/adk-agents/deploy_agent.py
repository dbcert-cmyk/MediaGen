#!/usr/bin/env python3
"""
Deploy ADK agents to Vertex AI Agent Engine
Usage: python deploy_agent.py <agent_name> [--staging-bucket BUCKET]
"""

import sys
import os
import argparse
from pathlib import Path
import vertexai
from vertexai.preview import reasoning_engines

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = os.environ.get("LOCATION", "us-central1")


def deploy_agent(agent_name: str, staging_bucket: str = None):
    """
    Deploy an ADK agent to Vertex AI Agent Engine.

    Args:
        agent_name: Name of the agent to deploy (email_agent, calendar_agent, etc.)
        staging_bucket: GCS bucket for staging (optional)
    """
    print(f"\n{'='*60}")
    print(f"Deploying {agent_name} to Vertex AI Agent Engine")
    print(f"{'='*60}\n")

    # Agent directory
    agent_dir = Path(__file__).parent / agent_name
    agent_file = agent_dir / "agent.py"

    if not agent_file.exists():
        print(f"❌ Error: Agent file not found: {agent_file}")
        sys.exit(1)

    print(f"✓ Found agent file: {agent_file}")

    # Initialize Vertex AI
    print(f"✓ Initializing Vertex AI (project={PROJECT_ID}, location={LOCATION})")
    vertexai.init(project=PROJECT_ID, location=LOCATION)

    # Load the agent module
    print(f"✓ Loading agent module...")
    sys.path.insert(0, str(agent_dir))

    try:
        # Import the agent module
        import importlib.util
        spec = importlib.util.spec_from_file_location(agent_name, agent_file)
        agent_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(agent_module)

        # Get the root_agent
        if not hasattr(agent_module, 'root_agent'):
            print(f"❌ Error: Agent file must export 'root_agent'")
            sys.exit(1)

        root_agent = agent_module.root_agent
        print(f"✓ Loaded root_agent: {root_agent.name}")

    except Exception as e:
        print(f"❌ Error loading agent: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Prepare deployment config
    config = {
        "requirements": [
            "google-cloud-aiplatform[agent_engines,adk]>=1.111",
            "google-cloud-discoveryengine",
            "google-cloud-firestore",
            "google-cloud-storage",
            "python-dateutil"
        ]
    }

    if staging_bucket:
        config["staging_bucket"] = staging_bucket
        print(f"✓ Using staging bucket: {staging_bucket}")

    # Deploy to Agent Engine
    print(f"\n{'='*60}")
    print(f"Starting deployment (this may take 2-5 minutes)...")
    print(f"{'='*60}\n")

    try:
        # Create reasoning engine (Agent Engine backend)
        remote_agent = reasoning_engines.ReasoningEngine.create(
            root_agent,
            requirements=config["requirements"],
            display_name=agent_name,
            description=f"Deployed ADK agent: {agent_name}"
        )

        print(f"\n{'='*60}")
        print(f"✅ Deployment successful!")
        print(f"{'='*60}\n")
        print(f"Agent Name: {agent_name}")
        print(f"Resource Name: {remote_agent.resource_name}")
        print(f"Display Name: {remote_agent.display_name}")
        print(f"\nTo query this agent:")
        print(f"  resource_name = '{remote_agent.resource_name}'")
        print(f"  response = remote_agent.query(input='Your query here')")
        print(f"\nView in console:")
        print(f"  https://console.cloud.google.com/vertex-ai/reasoning-engines?project={PROJECT_ID}")

        return remote_agent

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ Deployment failed!")
        print(f"{'='*60}\n")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Deploy ADK agents to Vertex AI Agent Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy_agent.py email_agent
  python deploy_agent.py calendar_agent --staging-bucket gs://my-bucket

Available agents:
  - email_agent
  - calendar_agent
  - meeting_prep_agent
  - followup_agent
"""
    )

    parser.add_argument(
        "agent_name",
        help="Name of the agent to deploy (email_agent, calendar_agent, meeting_prep_agent, followup_agent)"
    )

    parser.add_argument(
        "--staging-bucket",
        help="GCS bucket for staging (optional, format: gs://bucket-name)"
    )

    parser.add_argument(
        "--project",
        default=PROJECT_ID,
        help=f"GCP project ID (default: {PROJECT_ID})"
    )

    parser.add_argument(
        "--location",
        default=LOCATION,
        help=f"GCP location (default: {LOCATION})"
    )

    args = parser.parse_args()

    # Update globals
    global PROJECT_ID, LOCATION
    PROJECT_ID = args.project
    LOCATION = args.location

    # Set environment variables
    os.environ["PROJECT_ID"] = PROJECT_ID
    os.environ["LOCATION"] = LOCATION

    # Deploy
    deploy_agent(args.agent_name, args.staging_bucket)


if __name__ == "__main__":
    main()
