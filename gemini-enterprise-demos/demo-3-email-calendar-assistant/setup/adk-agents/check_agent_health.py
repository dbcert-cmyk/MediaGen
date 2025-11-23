#!/usr/bin/env python3
"""
Check agent deployment health and Discovery Engine connectivity
"""

import vertexai
from google.cloud import discoveryengine_v1
import os

PROJECT_ID = "ai-testing-458318"
LOCATION = "us-central1"
PROJECT_NUMBER = "805114253837"

# Discovery Engine datastores
DATASTORES = {
    "Gmail": f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-gmail-datastore_1763851937069_google_mail",
    "Calendar": f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-calendar-datastore_1763851980966_google_calendar",
    "Drive": f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-drive-datastore_1763851832394_google_drive"
}

# Agents
AGENTS = {
    "Email Management": f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/6553102495684493312",
    "Calendar Management": f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/8840086681458573312",
    "Meeting Preparation": f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/2472841233286823936",
    "Follow-up & Task Management": f"projects/{PROJECT_NUMBER}/locations/{LOCATION}/reasoningEngines/3123611379441860608"
}


def check_discovery_engine_datastore(name, datastore_path):
    """Test if a Discovery Engine datastore is accessible and has data"""

    print(f"\nChecking: {name}")
    print(f"Path: {datastore_path}")

    try:
        client = discoveryengine_v1.SearchServiceClient()

        # Try a simple search
        request = discoveryengine_v1.SearchRequest(
            serving_config=f"{datastore_path}/servingConfigs/default_search",
            query="*",  # Wildcard to get any results
            page_size=5
        )

        response = client.search(request)

        # Count results
        result_count = 0
        for result in response.results:
            result_count += 1

        if result_count > 0:
            print(f"✅ Accessible - Found {result_count} documents")
            return True
        else:
            print(f"⚠️  Accessible but EMPTY - No documents found")
            return False

    except Exception as e:
        print(f"❌ Error accessing datastore: {e}")
        return False


def check_agent_deployment(name, resource_path):
    """Check if agent is deployed and accessible"""

    print(f"\nChecking: {name}")
    print(f"Path: {resource_path}")

    try:
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

        agent = client.agent_engines.get(name=resource_path)

        print(f"✅ Agent is deployed and accessible")

        # Try to get some info about the agent
        if hasattr(agent, 'display_name'):
            print(f"   Display name: {agent.display_name}")
        if hasattr(agent, 'description'):
            print(f"   Description: {agent.description[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Error accessing agent: {e}")
        return False


def main():
    """Run all health checks"""

    print("="*80)
    print("Agent & Discovery Engine Health Check")
    print("="*80)

    # Check Discovery Engine datastores
    print("\n" + "="*80)
    print("1. DISCOVERY ENGINE DATASTORES")
    print("="*80)

    datastore_results = {}
    for name, path in DATASTORES.items():
        datastore_results[name] = check_discovery_engine_datastore(name, path)

    # Check agents
    print("\n" + "="*80)
    print("2. AGENT DEPLOYMENTS")
    print("="*80)

    agent_results = {}
    for name, path in AGENTS.items():
        agent_results[name] = check_agent_deployment(name, path)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    print("\nDiscovery Engine Datastores:")
    for name, healthy in datastore_results.items():
        status = "✅ OK" if healthy else "❌ ISSUE"
        print(f"  {status} - {name}")

    print("\nAgent Deployments:")
    for name, healthy in agent_results.items():
        status = "✅ OK" if healthy else "❌ ISSUE"
        print(f"  {status} - {name}")

    # Recommendations
    print("\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    empty_datastores = [name for name, healthy in datastore_results.items() if not healthy]
    if empty_datastores:
        print("\n⚠️  Empty or inaccessible datastores detected:")
        for ds in empty_datastores:
            print(f"   - {ds}")
        print("\n   This could explain why agents return no response.")
        print("   Agents can't provide data if datastores are empty.")
        print("\n   Solutions:")
        print("   1. Wait for Discovery Engine to index data (can take hours)")
        print("   2. Verify data sources are connected correctly")
        print("   3. Check Discovery Engine permissions")
        print("   4. Test datastores directly in Cloud Console")

    failed_agents = [name for name, healthy in agent_results.items() if not healthy]
    if failed_agents:
        print("\n❌ Failed agents detected:")
        for agent in failed_agents:
            print(f"   - {agent}")
        print("\n   These agents need to be redeployed.")

    if not empty_datastores and not failed_agents:
        print("\n✅ All datastores and agents are healthy.")
        print("\n   If agents still return no response, check:")
        print("   1. Agent code for errors (syntax, imports, logic)")
        print("   2. Agent logs in Cloud Console")
        print("   3. Firestore session backend configuration")
        print("   4. Service account permissions")

    print()


if __name__ == '__main__':
    main()
