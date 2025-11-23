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

        print(f"Loading agent: {EMAIL_AGENT}")
        remote_agent = reasoning_engines.ReasoningEngine(EMAIL_AGENT)

        print("✓ Agent loaded successfully")
        print()

        # First, let's see what methods are available
        print("Available methods on ReasoningEngine object:")
        methods = [m for m in dir(remote_agent) if not m.startswith('_')]
        for method in methods[:20]:  # Show first 20
            print(f"  - {method}")
        print()

        # Check if it has an execute or invoke method
        if hasattr(remote_agent, 'execute'):
            print("Found 'execute' method! Trying it...")
            response = remote_agent.execute(input="Hello, can you help me?")
        elif hasattr(remote_agent, 'invoke'):
            print("Found 'invoke' method! Trying it...")
            response = remote_agent.invoke(input="Hello, can you help me?")
        elif hasattr(remote_agent, 'query'):
            print("Found 'query' method! Trying it...")
            response = remote_agent.query(input="Hello, can you help me?")
        else:
            print("⚠️  No standard invocation method found!")
            print("The agent is deployed but the API to call it has changed.")
            response = None

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
