#!/usr/bin/env python3
"""
Investigate why API returns empty but Gemini chat sees data
"""

from google.cloud import discoveryengine_v1
from google.cloud import discoveryengine_v1alpha

PROJECT_ID = "ai-testing-458318"
PROJECT_NUMBER = "805114253837"

# Datastores we've been trying
DATASTORES_TO_TEST = [
    # Current paths we've been using
    f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-gmail-datastore_1763851937069_google_mail",
    f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-calendar-datastore_1763851980966_google_calendar",
    f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-drive-datastore_1763851832394_google_drive",

    # Try with project number instead
    f"projects/{PROJECT_NUMBER}/locations/global/collections/default_collection/dataStores/demo-gmail-datastore_1763851937069_google_mail",
    f"projects/{PROJECT_NUMBER}/locations/global/collections/default_collection/dataStores/demo-calendar-datastore_1763851980966_google_calendar",
    f"projects/{PROJECT_NUMBER}/locations/global/collections/default_collection/dataStores/demo-drive-datastore_1763851832394_google_drive",
]

# Different serving configs to try
SERVING_CONFIGS = [
    "default_search",
    "default_config",
    "serving_config_0"
]


def list_all_datastores():
    """Try to list all available datastores"""

    print("\n" + "="*80)
    print("Attempting to list all datastores in project")
    print("="*80)

    try:
        client = discoveryengine_v1.DataStoreServiceClient()

        # Try different parent paths
        parent_paths = [
            f"projects/{PROJECT_ID}/locations/global/collections/default_collection",
            f"projects/{PROJECT_NUMBER}/locations/global/collections/default_collection",
            f"projects/{PROJECT_ID}/locations/global",
            f"projects/{PROJECT_NUMBER}/locations/global",
        ]

        for parent in parent_paths:
            try:
                print(f"\nTrying parent: {parent}")
                request = discoveryengine_v1.ListDataStoresRequest(parent=parent)
                page_result = client.list_data_stores(request=request)

                count = 0
                for datastore in page_result:
                    count += 1
                    print(f"\n  Found datastore #{count}:")
                    print(f"    Name: {datastore.name}")
                    print(f"    Display name: {datastore.display_name}")
                    if hasattr(datastore, 'industry_vertical'):
                        print(f"    Type: {datastore.industry_vertical}")

                if count > 0:
                    print(f"\n✅ Found {count} datastores using parent: {parent}")
                    return
                else:
                    print(f"  No datastores found")

            except Exception as e:
                print(f"  ❌ Error: {str(e)[:100]}")

        print("\n⚠️  Could not list datastores with any parent path")

    except Exception as e:
        print(f"\n❌ Failed to create client: {e}")


def test_search_variations(datastore_path, name):
    """Try different search methods on a datastore"""

    print(f"\n" + "="*80)
    print(f"Testing: {name}")
    print(f"Path: {datastore_path}")
    print("="*80)

    client = discoveryengine_v1.SearchServiceClient()

    # Try different queries
    queries = [
        "*",           # Wildcard
        "",            # Empty
        "email",       # Keyword
        "meeting",     # From the example the user showed
    ]

    for query in queries:
        for serving_config in SERVING_CONFIGS:
            serving_config_path = f"{datastore_path}/servingConfigs/{serving_config}"

            try:
                request = discoveryengine_v1.SearchRequest(
                    serving_config=serving_config_path,
                    query=query if query else "*",
                    page_size=5
                )

                response = client.search(request)

                result_count = sum(1 for _ in response.results)

                if result_count > 0:
                    print(f"\n✅ SUCCESS - Found {result_count} results!")
                    print(f"   Query: '{query}'")
                    print(f"   Serving config: {serving_config}")
                    print(f"\n   Sample results:")

                    # Show first result
                    request2 = discoveryengine_v1.SearchRequest(
                        serving_config=serving_config_path,
                        query=query if query else "*",
                        page_size=3
                    )
                    response2 = client.search(request2)

                    for i, result in enumerate(response2.results):
                        doc = result.document
                        print(f"\n   Result {i+1}:")
                        print(f"      ID: {doc.id}")
                        if hasattr(doc, 'derived_struct_data'):
                            data = doc.derived_struct_data
                            if 'subject' in data:
                                print(f"      Subject: {data['subject']}")
                            if 'from' in data:
                                print(f"      From: {data['from']}")
                            if 'snippet' in data:
                                print(f"      Snippet: {data['snippet'][:100]}")

                    return True

            except Exception as e:
                error_msg = str(e)
                if "NOT_FOUND" in error_msg or "not found" in error_msg.lower():
                    continue  # Skip not found errors
                elif "PERMISSION_DENIED" in error_msg:
                    print(f"\n❌ PERMISSION_DENIED for serving config: {serving_config}")
                    print(f"   This might be the issue!")
                else:
                    print(f"\n⚠️  Error with query='{query}', serving_config={serving_config}")
                    print(f"   {error_msg[:100]}")

    print(f"\n❌ No successful searches found for {name}")
    return False


def main():
    """Run investigation"""

    print("="*80)
    print("Discovery Engine Data Investigation")
    print("="*80)
    print()
    print("Regular Gemini chat shows data, but API returns empty.")
    print("Let's find out why...")

    # Step 1: Try to list all datastores
    list_all_datastores()

    # Step 2: Try different search variations
    print("\n\n" + "="*80)
    print("Testing Search Variations")
    print("="*80)

    for datastore_path in DATASTORES_TO_TEST:
        # Extract name from path
        name = datastore_path.split("/")[-1].split("_")[0]
        test_search_variations(datastore_path, name)

    print("\n\n" + "="*80)
    print("INVESTIGATION COMPLETE")
    print("="*80)
    print()
    print("If all searches failed, the issue is likely:")
    print("  1. Service account permissions")
    print("  2. Wrong datastore paths")
    print("  3. Datastore configuration (different than Gemini chat uses)")
    print()
    print("Next step: Check Discovery Engine console to see:")
    print("  - Actual datastore names")
    print("  - Service account permissions")
    print("  - API access settings")
    print()


if __name__ == '__main__':
    main()
