#!/usr/bin/env python3
"""
Search ALL datastores in the project to find which ones have data
"""

from google.cloud import discoveryengine_v1
import sys

PROJECT_ID = "ai-testing-458318"
PROJECT_NUMBER = "805114253837"


def search_datastore(datastore_name, display_name):
    """Try to search a datastore and return result count"""

    client = discoveryengine_v1.SearchServiceClient()

    # Try different serving configs
    serving_configs = ["default_search", "default_config", "serving_config_0"]

    for serving_config in serving_configs:
        serving_config_path = f"{datastore_name}/servingConfigs/{serving_config}"

        try:
            request = discoveryengine_v1.SearchRequest(
                serving_config=serving_config_path,
                query="*",  # Wildcard to get everything
                page_size=10
            )

            response = client.search(request)
            results = list(response.results)

            if len(results) > 0:
                print(f"\n   ✅ FOUND DATA - {len(results)} documents")
                print(f"      Serving config: {serving_config}")

                # Show sample results
                print(f"\n      Sample results:")
                for i, result in enumerate(results[:3]):
                    doc = result.document
                    print(f"\n      Document {i+1}:")
                    print(f"         ID: {doc.id}")

                    # Try to show useful fields
                    if hasattr(doc, 'derived_struct_data') and doc.derived_struct_data:
                        data = doc.derived_struct_data
                        # Email fields
                        if 'subject' in data:
                            print(f"         Subject: {data['subject']}")
                        if 'from' in data:
                            print(f"         From: {data['from']}")
                        if 'snippet' in data:
                            print(f"         Snippet: {data['snippet'][:100]}")
                        # Calendar fields
                        if 'title' in data:
                            print(f"         Title: {data['title']}")
                        if 'start' in data:
                            print(f"         Start: {data['start']}")
                        if 'description' in data:
                            print(f"         Description: {data['description'][:100]}")

                return len(results), serving_config

        except Exception as e:
            error_msg = str(e)
            if "NOT_FOUND" not in error_msg and "not found" not in error_msg.lower():
                if "PERMISSION" in error_msg:
                    print(f"\n   ❌ PERMISSION_DENIED")
                    return 0, None

    return 0, None


def list_and_search_all_datastores():
    """List all datastores and search each one"""

    print("="*80)
    print("Searching ALL Datastores in Project")
    print("="*80)
    print()

    client = discoveryengine_v1.DataStoreServiceClient()

    # Try different parent paths
    parent_paths = [
        f"projects/{PROJECT_ID}/locations/global/collections/default_collection",
        f"projects/{PROJECT_NUMBER}/locations/global/collections/default_collection",
        f"projects/{PROJECT_ID}/locations/global",
        f"projects/{PROJECT_NUMBER}/locations/global",
    ]

    all_datastores = []

    for parent in parent_paths:
        try:
            print(f"Checking parent: {parent}")
            request = discoveryengine_v1.ListDataStoresRequest(parent=parent)
            page_result = client.list_data_stores(request=request)

            for datastore in page_result:
                all_datastores.append(datastore)

            if all_datastores:
                print(f"✅ Found {len(all_datastores)} datastores\n")
                break
            else:
                print(f"   No datastores found\n")

        except Exception as e:
            print(f"   Error: {str(e)[:100]}\n")

    if not all_datastores:
        print("\n❌ Could not find any datastores!")
        print("\nTrying alternative: Search specific known paths...")

        # Try known datastore patterns
        known_patterns = [
            f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-gmail-datastore_1763851937069_google_mail",
            f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-calendar-datastore_1763851980966_google_calendar",
            f"projects/{PROJECT_ID}/locations/global/collections/default_collection/dataStores/demo-drive-datastore_1763851832394_google_drive",
        ]

        for ds_path in known_patterns:
            ds_name = ds_path.split("/")[-1]
            print(f"\n{'='*80}")
            print(f"Trying known path: {ds_name}")
            print(f"{'='*80}")
            print(f"Path: {ds_path}")

            count, config = search_datastore(ds_path, ds_name)
            if count > 0:
                print(f"\n   🎯 THIS DATASTORE HAS DATA!")
                print(f"\n   Use this in agent code:")
                print(f'   DATASTORE = "{ds_path}"')

        return

    # Search each datastore
    print("\n" + "="*80)
    print("Testing Each Datastore")
    print("="*80)

    datastores_with_data = []

    for i, datastore in enumerate(all_datastores, 1):
        print(f"\n[{i}/{len(all_datastores)}] {datastore.display_name}")
        print(f"   Name: {datastore.name}")
        print(f"   Type: {datastore.industry_vertical if hasattr(datastore, 'industry_vertical') else 'N/A'}")

        count, config = search_datastore(datastore.name, datastore.display_name)

        if count > 0:
            datastores_with_data.append({
                'name': datastore.name,
                'display_name': datastore.display_name,
                'count': count,
                'serving_config': config
            })
            print(f"\n   🎯 THIS DATASTORE HAS DATA!")
        else:
            print(f"   ⚠️  Empty or no access")

    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    print(f"\nTotal datastores found: {len(all_datastores)}")
    print(f"Datastores with data: {len(datastores_with_data)}")

    if datastores_with_data:
        print("\n🎯 DATASTORES THAT HAVE DATA:")
        print("="*80)

        for ds in datastores_with_data:
            print(f"\nDisplay Name: {ds['display_name']}")
            print(f"Path: {ds['name']}")
            print(f"Documents: ~{ds['count']}")
            print(f"Serving Config: {ds['serving_config']}")

            # Extract just the datastore ID for easier reference
            ds_id = ds['name'].split('/')[-1]

            # Guess the type based on name
            ds_type = "UNKNOWN"
            if 'gmail' in ds_id.lower() or 'mail' in ds_id.lower():
                ds_type = "Gmail"
            elif 'calendar' in ds_id.lower():
                ds_type = "Calendar"
            elif 'drive' in ds_id.lower():
                ds_type = "Drive"

            print(f"\n   💡 Use this in your {ds_type} agent code:")
            print(f'   {ds_type.upper()}_DATASTORE = "{ds["name"]}"')

        print("\n" + "="*80)
        print("\n✅ Found the datastores with data!")
        print("\nNext step: Update agent code to use these datastore paths")

    else:
        print("\n❌ No datastores with accessible data found")
        print("\nPossible issues:")
        print("  1. Service account needs 'Discovery Engine Viewer' role")
        print("  2. Datastores are in a different project")
        print("  3. Data hasn't been indexed yet")

    print()


if __name__ == '__main__':
    list_and_search_all_datastores()
