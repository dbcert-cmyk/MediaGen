#!/usr/bin/env python3
"""
Test calling an agent directly via Vertex AI API
This bypasses Gemini Enterprise Plus to see if the agent works at all
"""

import vertexai
from vertexai.preview import reasoning_engines

PROJECT_ID = "ai-testing-458318"
LOCATION = "us-central1"

# Email Agent resource path
EMAIL_AGENT = "projects/805114253837/locations/us-central1/reasoningEngines/6553102495684493312"

def test_agent():
    """Test calling the email agent directly"""

    print("="*60)
    print("Testing Email Agent Direct Call")
    print("="*60)
    print()

    try:
        # Initialize Vertex AI
        vertexai.init(project=PROJECT_ID, location=LOCATION)

        print(f"Loading agent using agent_engines.get(): {EMAIL_AGENT}")

        # Correct way to get a deployed agent according to latest docs
        from vertexai._genai import agent_engines
        client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

        adk_app = client.agent_engines.get(name=EMAIL_AGENT)

        print("✓ Agent loaded successfully")
        print()

        # Check what operations are supported
        print("Checking supported operations...")
        try:
            operations = adk_app.operation_schemas()
            print(f"Supported operations: {operations}")
        except:
            print("Could not get operation schemas")

        print()

        # Try calling the agent with the query method (from docs)
        print("Sending test query: 'Hello, can you help me?'")

        # According to docs, should use async_stream_query or regular query
        if hasattr(adk_app, 'query'):
            response = adk_app.query(input="Hello, can you help me?")
        elif hasattr(adk_app, 'async_stream_query'):
            # Try sync version
            response = adk_app.query(input="Hello, can you help me?")
        else:
            response = "No query method found"

        print("="*60)
        print("✅ AGENT RESPONDED!")
        print("="*60)
        print()
        print("Response:")
        print(response)

    except Exception as e:
        print("="*60)
        print("❌ AGENT FAILED")
        print("="*60)
        print()
        print(f"Error: {e}")
        print()
        print("This confirms the agent has issues.")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_agent()
