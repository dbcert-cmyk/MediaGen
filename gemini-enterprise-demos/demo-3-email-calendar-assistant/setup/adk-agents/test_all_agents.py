#!/usr/bin/env python3
"""
Test all 4 deployed ADK agents with multiple query variations
"""

import vertexai
from vertexai._genai import agent_engines
import time

PROJECT_ID = "ai-testing-458318"
LOCATION = "us-central1"

# All agent resource paths
AGENTS = {
    "Email Management": "projects/805114253837/locations/us-central1/reasoningEngines/6553102495684493312",
    "Calendar Management": "projects/805114253837/locations/us-central1/reasoningEngines/8840086681458573312",
    "Meeting Preparation": "projects/805114253837/locations/us-central1/reasoningEngines/2472841233286823936",
    "Follow-up & Task Management": "projects/805114253837/locations/us-central1/reasoningEngines/3123611379441860608"
}

# Multiple test queries for each agent (testing different capabilities)
TEST_QUERIES = {
    "Email Management": [
        "What emails do I have?",
        "Summarize my emails from today",
        "Show me urgent emails",
        "Search for emails from the CEO",
        "Draft a response to the latest email"
    ],
    "Calendar Management": [
        "What's on my calendar?",
        "Show me today's schedule",
        "Find time for a 30-minute meeting this week",
        "What meetings do I have tomorrow?",
        "Am I free at 2pm today?"
    ],
    "Meeting Preparation": [
        "Help me prepare for my next meeting",
        "What do I need to know for the Q1 planning meeting?",
        "Summarize background for my 2pm meeting",
        "Gather context for today's executive meeting",
        "What documents are relevant to the product review?"
    ],
    "Follow-up & Task Management": [
        "What tasks do I need to follow up on?",
        "Show me pending action items",
        "Track follow-ups from this week's meetings",
        "What deadlines are coming up?",
        "List all open tasks"
    ]
}


def test_single_query(agent_app, agent_name, query, query_num, total_queries):
    """Test a single query and return one-line result"""

    start_time = time.time()

    try:
        responses = []
        error_occurred = False
        error_msg = None

        for chunk in agent_app.stream_query(
            message=query,
            user_id="demo-user",
            session_id=f"test-session-{int(time.time())}"
        ):
            responses.append(chunk)

            # Check for errors in response
            if isinstance(chunk, dict):
                if 'code' in chunk and chunk.get('code') != 200:
                    error_occurred = True
                    error_msg = f"Error code {chunk.get('code')}: {chunk.get('message', 'Unknown')}"
                elif 'error' in chunk:
                    error_occurred = True
                    error_msg = str(chunk.get('error'))

        elapsed = time.time() - start_time

        # Determine status
        if error_occurred:
            status_icon = "⚠️ "
            status = "PARTIAL"
            detail = f"{len(responses)} chunks, {error_msg[:40]}"
        elif len(responses) == 0:
            status_icon = "❌"
            status = "FAILED"
            detail = "No response"
        else:
            status_icon = "✅"
            status = "SUCCESS"
            detail = f"{len(responses)} chunks, {elapsed:.1f}s"

        # One-line output
        print(f"[{status_icon}] {agent_name} ({query_num}/{total_queries}) - \"{query[:50]}{'...' if len(query) > 50 else ''}\" - {status} ({detail})")

        return {
            'query': query,
            'status': 'success' if status == 'SUCCESS' else ('partial' if status == 'PARTIAL' else 'failed'),
            'chunks': len(responses),
            'elapsed': elapsed,
            'error': error_msg
        }

    except Exception as e:
        elapsed = time.time() - start_time
        error_str = str(e)

        # Shorten error for one-line display
        if "metadata.google.internal" in error_str:
            short_error = "Auth: No credentials configured"
        elif "RefreshError" in error_str:
            short_error = "Auth: Failed to refresh credentials"
        elif "PermissionDenied" in error_str:
            short_error = "Auth: Permission denied"
        else:
            short_error = error_str[:50]

        print(f"[❌] {agent_name} ({query_num}/{total_queries}) - \"{query[:50]}{'...' if len(query) > 50 else ''}\" - FAILED ({short_error})")

        return {
            'query': query,
            'status': 'failed',
            'error': error_str,
            'elapsed': elapsed
        }


def test_agent(name, resource_path, queries):
    """Test an agent with multiple queries"""

    print(f"\n{'='*80}")
    print(f"Testing: {name} ({len(queries)} queries)")
    print(f"{'='*80}")

    results = []

    try:
        # Initialize and load agent once
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

        print(f"Loading agent...")
        adk_app = client.agent_engines.get(name=resource_path)
        print(f"✓ Agent loaded\n")

        # Test each query
        for i, query in enumerate(queries, 1):
            result = test_single_query(adk_app, name, query, i, len(queries))
            results.append(result)

            # Brief pause between queries
            if i < len(queries):
                time.sleep(0.5)

        # Agent summary
        success_count = sum(1 for r in results if r['status'] == 'success')
        partial_count = sum(1 for r in results if r['status'] == 'partial')
        failed_count = sum(1 for r in results if r['status'] == 'failed')

        print(f"\n{name} Summary: {success_count} ✅  {partial_count} ⚠️   {failed_count} ❌")

        return {
            'name': name,
            'results': results,
            'success': success_count,
            'partial': partial_count,
            'failed': failed_count
        }

    except Exception as e:
        print(f"\n❌ Failed to load agent: {e}")

        # If agent fails to load, mark all queries as failed
        for i, query in enumerate(queries, 1):
            print(f"[❌] {name} ({i}/{len(queries)}) - \"{query[:50]}\" - FAILED (Agent load failed)")

        return {
            'name': name,
            'results': [],
            'success': 0,
            'partial': 0,
            'failed': len(queries),
            'load_error': str(e)
        }


def main():
    """Test all agents"""

    print("="*80)
    print("ADK Agent Comprehensive Testing")
    print("="*80)
    print()
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Agents: {len(AGENTS)}")

    total_queries = sum(len(queries) for queries in TEST_QUERIES.values())
    print(f"Total test queries: {total_queries}")
    print()

    all_results = {}

    for name, resource_path in AGENTS.items():
        queries = TEST_QUERIES.get(name, ["Hello"])
        result = test_agent(name, resource_path, queries)
        all_results[name] = result

    # Final summary
    print(f"\n\n{'='*80}")
    print("FINAL SUMMARY")
    print(f"{'='*80}\n")

    total_success = sum(r['success'] for r in all_results.values())
    total_partial = sum(r['partial'] for r in all_results.values())
    total_failed = sum(r['failed'] for r in all_results.values())

    print(f"Overall Results:")
    print(f"  ✅ Success:  {total_success}/{total_queries} ({total_success*100//total_queries if total_queries > 0 else 0}%)")
    print(f"  ⚠️  Partial:  {total_partial}/{total_queries} ({total_partial*100//total_queries if total_queries > 0 else 0}%)")
    print(f"  ❌ Failed:   {total_failed}/{total_queries} ({total_failed*100//total_queries if total_queries > 0 else 0}%)")

    print(f"\nPer-Agent Results:")
    for name, result in all_results.items():
        total = result['success'] + result['partial'] + result['failed']
        success_pct = (result['success'] * 100 // total) if total > 0 else 0

        if result['success'] == total:
            status = "✅ EXCELLENT"
        elif result['success'] + result['partial'] == total:
            status = "⚠️  PARTIAL"
        else:
            status = "❌ ISSUES"

        print(f"  {status} - {name}: {result['success']}/{total} passed")

        if 'load_error' in result:
            print(f"           Load Error: {result['load_error'][:60]}")

    print()

    if total_success == total_queries:
        print("🎉 All agents working perfectly! Ready for production.")
    elif total_success + total_partial == total_queries:
        print("⚠️  Agents responding but with some errors. Review error messages above.")
    elif total_failed == total_queries:
        print("❌ All tests failed. Check authentication and agent deployment.")
    else:
        print("⚠️  Mixed results. Some agents working, some need debugging.")

    print()


if __name__ == '__main__':
    main()
