#!/usr/bin/env python3
"""
Debug script to see exactly what agents are returning
"""

import vertexai
from vertexai._genai import agent_engines
import time
import json

PROJECT_ID = "ai-testing-458318"
LOCATION = "us-central1"

# Test with just one agent first
EMAIL_AGENT = "projects/805114253837/locations/us-central1/reasoningEngines/6553102495684493312"


def debug_agent_response():
    """Debug what the agent is actually returning"""

    print("="*80)
    print("Agent Response Debugging")
    print("="*80)
    print()

    # Initialize
    print("1. Initializing Vertex AI client...")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
    print("✓ Client initialized\n")

    # Load agent
    print("2. Loading Email Management Agent...")
    try:
        agent = client.agent_engines.get(name=EMAIL_AGENT)
        print(f"✓ Agent loaded")
        print(f"   Type: {type(agent)}")
        print(f"   Agent name: {agent.name if hasattr(agent, 'name') else 'N/A'}")
        print()
    except Exception as e:
        print(f"❌ Failed to load agent: {e}")
        return

    # Test query
    query = "What emails do I have?"
    print(f"3. Testing query: '{query}'")
    print()

    print("4. Calling stream_query()...")
    print("   Watching for response chunks...")
    print()

    try:
        chunk_count = 0
        start_time = time.time()

        for chunk in agent.stream_query(
            message=query,
            user_id="demo-user",
            session_id=f"debug-session-{int(time.time())}"
        ):
            chunk_count += 1
            elapsed = time.time() - start_time

            print(f"   Chunk #{chunk_count} (at {elapsed:.2f}s):")
            print(f"      Type: {type(chunk)}")
            print(f"      Value: {chunk}")

            # If it's a dict, show keys
            if isinstance(chunk, dict):
                print(f"      Keys: {list(chunk.keys())}")
                for key, value in chunk.items():
                    print(f"         {key}: {value}")

            # If it's an object, show attributes
            elif hasattr(chunk, '__dict__'):
                print(f"      Attributes: {chunk.__dict__}")

            print()

        total_time = time.time() - start_time

        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total chunks received: {chunk_count}")
        print(f"Total time: {total_time:.2f}s")

        if chunk_count == 0:
            print()
            print("⚠️  NO CHUNKS RECEIVED")
            print()
            print("Possible causes:")
            print("  1. Agent code has an error and silently fails")
            print("  2. Discovery Engine datastore is not accessible")
            print("  3. Agent requires additional configuration")
            print("  4. Session backend (Firestore) not configured")
            print("  5. Agent is not returning data from tools")
            print()
            print("Next steps:")
            print("  - Check agent logs in Cloud Console")
            print("  - Verify Discovery Engine datastores have data")
            print("  - Test Discovery Engine datastores directly")
            print("  - Check agent code for errors")

    except Exception as e:
        print(f"❌ Error during stream_query: {e}")
        import traceback
        traceback.print_exc()
        print()
        print("This error occurred during the streaming process.")


if __name__ == '__main__':
    debug_agent_response()
