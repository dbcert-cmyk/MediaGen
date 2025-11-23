#!/usr/bin/env python3
"""
Test all 4 deployed ADK agents to verify they work correctly
"""

import vertexai
from vertexai._genai import agent_engines

PROJECT_ID = "ai-testing-458318"
LOCATION = "us-central1"

# All agent resource paths
AGENTS = {
    "Email Management": "projects/805114253837/locations/us-central1/reasoningEngines/6553102495684493312",
    "Calendar Management": "projects/805114253837/locations/us-central1/reasoningEngines/8840086681458573312",
    "Meeting Preparation": "projects/805114253837/locations/us-central1/reasoningEngines/2472841233286823936",
    "Follow-up & Task Management": "projects/805114253837/locations/us-central1/reasoningEngines/3123611379441860608"
}

# Test queries for each agent
TEST_QUERIES = {
    "Email Management": "What emails do I have?",
    "Calendar Management": "What's on my calendar?",
    "Meeting Preparation": "Help me prepare for my next meeting",
    "Follow-up & Task Management": "What tasks do I need to follow up on?"
}


def test_agent(name, resource_path, query):
    """Test a single agent"""

    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")

    try:
        # Initialize
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

        # Load agent
        print(f"Loading agent...")
        adk_app = client.agent_engines.get(name=resource_path)
        print(f"✓ Agent loaded")

        # Test query
        print(f"\nQuery: '{query}'")
        print(f"Calling stream_query...")

        responses = []
        error_occurred = False

        for chunk in adk_app.stream_query(
            message=query,
            user_id="demo-user",
            session_id="test-session-001"  # Provide session to avoid creation error
        ):
            responses.append(chunk)

            # Check for errors in response
            if isinstance(chunk, dict):
                if 'code' in chunk and chunk.get('code') != 200:
                    print(f"  ⚠️  Error chunk: {chunk}")
                    error_occurred = True
                elif 'error' in chunk:
                    print(f"  ⚠️  Error chunk: {chunk}")
                    error_occurred = True
                else:
                    print(f"  ✓ Chunk received: {str(chunk)[:100]}...")
            else:
                print(f"  ✓ Chunk received: {str(chunk)[:100]}...")

        # Summary
        print(f"\n{'='*60}")
        if error_occurred:
            print(f"⚠️  {name}: RESPONDED WITH ERRORS")
            print(f"Total chunks: {len(responses)}")
            print(f"\nFull response:")
            for i, r in enumerate(responses):
                print(f"  Chunk {i+1}: {r}")
        else:
            print(f"✅ {name}: SUCCESS")
            print(f"Total chunks: {len(responses)}")

        return {
            'name': name,
            'status': 'success' if not error_occurred else 'partial',
            'chunks': len(responses),
            'responses': responses
        }

    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ {name}: FAILED")
        print(f"{'='*60}")
        print(f"Error: {e}")

        import traceback
        traceback.print_exc()

        return {
            'name': name,
            'status': 'failed',
            'error': str(e)
        }


def main():
    """Test all agents"""

    print("="*60)
    print("Testing All Deployed ADK Agents")
    print("="*60)
    print()
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Agents to test: {len(AGENTS)}")
    print()

    results = {}

    for name, resource_path in AGENTS.items():
        query = TEST_QUERIES.get(name, "Hello")
        result = test_agent(name, resource_path, query)
        results[name] = result

    # Final summary
    print(f"\n\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")

    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    partial_count = sum(1 for r in results.values() if r['status'] == 'partial')
    failed_count = sum(1 for r in results.values() if r['status'] == 'failed')

    print(f"\n✅ Successful: {success_count}/{len(AGENTS)}")
    print(f"⚠️  Partial (with errors): {partial_count}/{len(AGENTS)}")
    print(f"❌ Failed: {failed_count}/{len(AGENTS)}")

    print(f"\nAgent Status:")
    for name, result in results.items():
        status_icon = {
            'success': '✅',
            'partial': '⚠️ ',
            'failed': '❌'
        }.get(result['status'], '?')

        print(f"  {status_icon} {name}: {result['status'].upper()}")

        if result['status'] == 'failed':
            print(f"      Error: {result.get('error', 'Unknown')}")

    print()

    if success_count == len(AGENTS):
        print("🎉 All agents working! Ready to register in Gemini Enterprise Plus.")
    elif success_count + partial_count == len(AGENTS):
        print("⚠️  Agents responding but with errors. May need session configuration.")
    else:
        print("❌ Some agents completely failed. Need to debug deployment.")

    print()


if __name__ == '__main__':
    main()
