#!/usr/bin/env python3
"""
Deploy ADK agents to Vertex AI Agent Engine
Usage: python deploy_agent.py <agent_name> --staging-bucket gs://BUCKET
"""

import sys
import os
import argparse
from pathlib import Path
import importlib.util

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = os.environ.get("LOCATION", "us-central1")


def deploy_agent(agent_name: str, staging_bucket: str):
    """
    Deploy an ADK agent to Vertex AI Agent Engine using the SDK.

    Args:
        agent_name: Name of the agent to deploy (email_agent, calendar_agent, etc.)
        staging_bucket: GCS bucket for staging (gs://bucket-name)
    """
    if not staging_bucket:
        print("❌ Error: --staging-bucket is required")
        print("\nCreate a GCS bucket first:")
        print(f"  gsutil mb -p {PROJECT_ID} -l {LOCATION} gs://YOUR_BUCKET_NAME")
        sys.exit(1)

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
    print(f"✓ Project: {PROJECT_ID}")
    print(f"✓ Location: {LOCATION}")
    print(f"✓ Staging bucket: {staging_bucket}")

    # Import Vertex AI SDK
    try:
        import vertexai
        from vertexai.preview import agent_engines
        print(f"✓ Imported Vertex AI SDK")
    except ImportError as e:
        print(f"❌ Error: Missing required package")
        print(f"\nInstall with:")
        print(f"  pip install google-cloud-aiplatform[agent_engines,adk]>=1.112")
        sys.exit(1)

    # Initialize Vertex AI
    print(f"\n✓ Initializing Vertex AI client...")
    client = vertexai.Client(
        project=PROJECT_ID,
        location=LOCATION
    )

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
            "google-cloud-aiplatform[agent_engines,adk]>=1.112",
            "google-cloud-discoveryengine",
            "google-cloud-firestore",
            "google-cloud-storage",
            "python-dateutil"
        ],
        "staging_bucket": staging_bucket
    }

    # Deploy to Agent Engine
    print(f"\n{'='*60}")
    print(f"Starting deployment (this may take 2-5 minutes)...")
    print(f"{'='*60}\n")

    try:
        # Create agent using agent_engines.create() - CORRECT API
        remote_agent = client.agent_engines.create(
            agent=root_agent,
            config=config
        )

        print(f"\n{'='*60}")
        print(f"✅ Deployment successful!")
        print(f"{'='*60}\n")
        print(f"Agent Name: {agent_name}")
        print(f"Resource Name: {remote_agent.resource_name}")

        if hasattr(remote_agent, 'display_name'):
            print(f"Display Name: {remote_agent.display_name}")

        print(f"\nTo query this agent:")
        print(f"  response = remote_agent.query(input='Your query here')")
        print(f"\nView in console:")
        print(f"  https://console.cloud.google.com/vertex-ai/agent-engine?project={PROJECT_ID}")

        return remote_agent

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ Deployment failed!")
        print(f"{'='*60}\n")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

        print(f"\n💡 Troubleshooting tips:")
        print(f"  1. Ensure Vertex AI API is enabled:")
        print(f"     gcloud services enable aiplatform.googleapis.com --project={PROJECT_ID}")
        print(f"  2. Verify staging bucket exists:")
        print(f"     gsutil ls {staging_bucket}")
        print(f"  3. Check IAM permissions (need roles/aiplatform.user)")

        sys.exit(1)


def main():
    global PROJECT_ID, LOCATION

    parser = argparse.ArgumentParser(
        description="Deploy ADK agents to Vertex AI Agent Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python deploy_agent.py email_agent --staging-bucket gs://my-bucket
  python deploy_agent.py calendar_agent --staging-bucket gs://my-bucket

Available agents:
  - email_agent
  - calendar_agent
  - meeting_prep_agent
  - followup_agent

Note: A GCS staging bucket is required. Create one with:
  gsutil mb -p PROJECT_ID -l LOCATION gs://BUCKET_NAME
"""
    )

    parser.add_argument(
        "agent_name",
        help="Name of the agent to deploy"
    )

    parser.add_argument(
        "--staging-bucket",
        required=True,
        help="GCS bucket for staging (required, format: gs://bucket-name)"
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
    PROJECT_ID = args.project
    LOCATION = args.location

    # Set environment variables
    os.environ["PROJECT_ID"] = PROJECT_ID
    os.environ["LOCATION"] = LOCATION

    # Deploy
    deploy_agent(args.agent_name, args.staging_bucket)


if __name__ == "__main__":
    main()
