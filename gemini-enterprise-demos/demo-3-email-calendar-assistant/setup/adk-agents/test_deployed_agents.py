#!/usr/bin/env python3
"""
Test deployed agents in Vertex AI Agent Engine
"""

import vertexai
import time

PROJECT_ID = "ai-testing-458318"
LOCATION = "us-central1"
PROJECT_NUMBER = "805114253837"

# Agent resource paths (update these with your new agent IDs if they changed)
AGENTS = {
    "Email Management": f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/6553102495684493312",
    "Calendar Management": f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/8840086681458573312",
}

# Test queries
TEST_QUERIES = {
    "Email Management": "What emails do I have?",
    "Calendar Management": "What's on my calendar today?",
}


def test_deployed_agent(name, resource_path, query):
    """Test a deployed agent"""

    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"{'='*80}")
    print(f"Resource: {resource_path}")
    print(f"Query: '{query}'")
    print()

    try:
        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

        # Load agent
        print("Loading agent...")
        agent = client.agent_engines.get(name=resource_path)
        print("✓ Agent loaded")

        # Query agent (without session to avoid permission issues)
        print(f"\nSending query...")
        start_time = time.time()

        responses = []
        try:
            for chunk in agent.stream_query(
                message=query,
                user_id="test-user"
                # Note: No session_id to avoid session permission errors
            ):
                responses.append(chunk)
                print(f"  Received chunk: {type(chunk).__name__}")
        except Exception as query_error:
            print(f"  Query error: {query_error}")

        elapsed = time.time() - start_time

        print(f"\n{'='*80}")
        if len(responses) > 0:
            print(f"✅ {name}: SUCCESS")
            print(f"   Chunks received: {len(responses)}")
            print(f"   Time: {elapsed:.2f}s")

            print(f"\n   Response preview:")
            for i, chunk in enumerate(responses[:3]):
                print(f"   Chunk {i+1}: {str(chunk)[:200]}")
                if len(str(chunk)) > 200:
                    print(f"            ...")

            return True
        else:
            print(f"⚠️  {name}: NO RESPONSE")
            print(f"   Agent loaded but returned no chunks")
            return False

    except Exception as e:
        print(f"\n{'='*80}")
        print(f"❌ {name}: FAILED")
        print(f"   Error: {e}")

        import traceback
        traceback.print_exc()
        return False


def main():
    """Test all deployed agents"""

    print("="*80)
    print("Testing Deployed Agents in Vertex AI Agent Engine")
    print("="*80)
    print()
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print()

    results = {}

    for name, resource_path in AGENTS.items():
        query = TEST_QUERIES.get(name, "Hello")
        success = test_deployed_agent(name, resource_path, query)
        results[name] = success

        # Brief pause between tests
        time.sleep(2)

    # Summary
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for name, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"  {status} - {name}")

    print()
    if success_count == total_count:
        print("🎉 All agents working! Ready to register in Gemini Enterprise Plus.")
    elif success_count > 0:
        print("⚠️  Some agents working. Check failed ones above.")
    else:
        print("❌ No agents working. Check errors above.")

    print()


if __name__ == '__main__':
    main()
