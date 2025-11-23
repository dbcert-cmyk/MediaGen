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

        # Try a simple query using the correct API
        print("Sending test query: 'Hello, can you help me?'")
        print()

        # Try different calling methods
        try:
            # Method 1: Direct call
            response = remote_agent("Hello, can you help me?")
        except Exception as e1:
            print(f"Method 1 failed: {e1}")
            try:
                # Method 2: Chat method
                response = remote_agent.chat("Hello, can you help me?")
            except Exception as e2:
                print(f"Method 2 failed: {e2}")
                # Method 3: Using input dict
                response = remote_agent(input="Hello, can you help me?")

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
