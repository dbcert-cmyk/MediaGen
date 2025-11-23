#!/usr/bin/env python3
"""
Comprehensive datastore investigation - searches ALL datastores in project
"""

from google.cloud import discoveryengine_v1
from google.auth import default
import google.auth

PROJECT_ID = "ai-testing-458318"
PROJECT_NUMBER = "805114253837"


def check_current_credentials():
    """Check what credentials we're using"""
    print("="*80)
    print("Current Credentials")
    print("="*80)

    try:
        credentials, project = default()
        print(f"\nProject: {project}")
        print(f"Credentials type: {type(credentials).__name__}")

        if hasattr(credentials, 'service_account_email'):
            print(f"Service account: {credentials.service_account_email}")
        elif hasattr(credentials, '_service_account_email'):
            print(f"Service account: {credentials._service_account_email}")
        else:
            print("Using user credentials (not service account)")

        return credentials, project

    except Exception as e:
        print(f"Error getting credentials: {e}")
        return None, None


def list_all_datastores():
    """List all datastores in the project"""
    print("\n" + "="*80)
    print("Discovering All Datastores")
    print("="*80)

    try:
        client = discoveryengine_v1.DataStoreServiceClient()

        # Try different parent paths
        parent_paths = [
            f"projects/{PROJECT_ID}/locations/global/collections/default_collection",
            f"projects/{PROJECT_NUMBER}/locations/global/collections/default_collection",
        ]

        all_datastores = []

        for parent in parent_paths:
            try:
                print(f"\nTrying parent: {parent}")
                request = discoveryengine_v1.ListDataStoresRequest(parent=parent)
                page_result = client.list_data_stores(request=request)

                for datastore in page_result:
                    all_datastores.append(datastore)

                if all_datastores:
                    print(f"✅ Found {len(all_datastores)} datastores")
                    break
                else:
                    print(f"   No datastores found")

            except Exception as e:
                print(f"   Error: {str(e)[:100]}")

        return all_datastores

    except Exception as e:
        print(f"\nError listing datastores: {e}")
        return []


def search_datastore(datastore_name, display_name):
    """Try to search a datastore and return results"""
    print(f"\n{'='*80}")
    print(f"Testing: {display_name}")
    print(f"{'='*80}")
    print(f"Path: {datastore_name}")

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
                print(f"\n✅ FOUND DATA - {len(results)} documents")
                print(f"   Serving config: {serving_config}")

                # Show sample results
                print(f"\n   Sample results:")
                for i, result in enumerate(results[:3]):
                    doc = result.document
                    print(f"\n   Document {i+1}:")
                    print(f"      ID: {doc.id}")

                    # Try to show useful fields
                    if hasattr(doc, 'derived_struct_data') and doc.derived_struct_data:
                        data = doc.derived_struct_data
                        # Email fields
                        if 'subject' in data:
                            print(f"      Subject: {data['subject']}")
                        if 'from' in data:
                            print(f"      From: {data['from']}")
                        if 'snippet' in data:
                            print(f"      Snippet: {data['snippet'][:100]}")
                        # Calendar fields
                        if 'title' in data:
                            print(f"      Title: {data['title']}")
                        if 'start' in data:
                            print(f"      Start: {data['start']}")
                        # Show first few keys
                        keys = list(data.keys())[:5]
                        if keys:
                            print(f"      Available fields: {', '.join(keys)}")

                return len(results), serving_config

        except google.auth.exceptions.RefreshError as e:
            print(f"\n❌ AUTHENTICATION ERROR")
            print(f"   {e}")
            print(f"\n   Run: gcloud auth application-default login")
            return 0, None

        except Exception as e:
            error_str = str(e)
            if "NOT_FOUND" not in error_str and "not found" not in error_str.lower():
                if "PERMISSION" in error_str or "403" in error_str:
                    print(f"\n❌ PERMISSION_DENIED")
                    print(f"   Error: {error_str[:100]}")
                    return 0, None

    print(f"\n⚠️  No data found (or no access)")
    return 0, None


def main():
    """Run comprehensive investigation"""

    print("="*80)
    print("Comprehensive Datastore Investigation")
    print("="*80)
    print()

    # Check credentials
    creds, project = check_current_credentials()

    if not creds:
        print("\n❌ Cannot proceed without credentials")
        print("\nRun this first:")
        print("  gcloud auth application-default login")
        return

    # List all datastores
    datastores = list_all_datastores()

    if not datastores:
        print("\n❌ No datastores found in project")
        return

    # Search each datastore
    print("\n\n" + "="*80)
    print(f"Testing All {len(datastores)} Datastores")
    print("="*80)

    results = {}

    for i, datastore in enumerate(datastores, 1):
        display_name = datastore.display_name
        datastore_name = datastore.name

        # Categorize by type
        ds_id = datastore_name.split('/')[-1]
        ds_type = "Unknown"
        if 'gmail' in ds_id.lower() or 'mail' in ds_id.lower():
            ds_type = "Gmail"
        elif 'calendar' in ds_id.lower():
            ds_type = "Calendar"
        elif 'drive' in ds_id.lower():
            ds_type = "Drive"
        elif 'gcs' in ds_id.lower():
            ds_type = "Cloud Storage"
        else:
            ds_type = "Unstructured Data"

        print(f"\n[{i}/{len(datastores)}] {display_name} ({ds_type})")

        count, config = search_datastore(datastore_name, display_name)

        results[display_name] = {
            'name': datastore_name,
            'type': ds_type,
            'count': count,
            'serving_config': config
        }

    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    print(f"\nTotal datastores: {len(datastores)}")

    # Group by status
    with_data = {k: v for k, v in results.items() if v['count'] > 0}
    empty = {k: v for k, v in results.items() if v['count'] == 0}

    print(f"Datastores with data: {len(with_data)}")
    print(f"Empty/inaccessible: {len(empty)}")

    if with_data:
        print("\n🎯 DATASTORES WITH DATA:")
        print("="*80)

        for name, info in with_data.items():
            print(f"\n✅ {name} ({info['type']})")
            print(f"   Path: {info['name']}")
            print(f"   Documents: ~{info['count']}")
            print(f"   Serving config: {info['serving_config']}")

            # Show how to use in agent code
            print(f"\n   💡 Use in {info['type']} agent:")
            print(f"   DATASTORE = \"{info['name']}\"")

    if empty:
        print("\n\n⚠️  EMPTY OR INACCESSIBLE DATASTORES:")
        print("="*80)

        # Group by type
        by_type = {}
        for name, info in empty.items():
            ds_type = info['type']
            if ds_type not in by_type:
                by_type[ds_type] = []
            by_type[ds_type].append(name)

        for ds_type, names in by_type.items():
            print(f"\n{ds_type}:")
            for name in names:
                print(f"  - {name}")

    # Recommendations
    print("\n\n" + "="*80)
    print("RECOMMENDATIONS")
    print("="*80)

    if with_data:
        print("\n✅ Update your agents to use the datastores with data (shown above)")

    gmail_empty = any(v['type'] == 'Gmail' and v['count'] == 0 for v in results.values())
    calendar_empty = any(v['type'] == 'Calendar' and v['count'] == 0 for v in results.values())
    drive_empty = any(v['type'] == 'Drive' and v['count'] == 0 for v in results.values())

    if gmail_empty or calendar_empty or drive_empty:
        print("\n⚠️  Gmail/Calendar/Drive datastores are empty via API")
        print("\nThis suggests:")
        print("  1. Gemini Enterprise Plus uses direct Workspace API access")
        print("  2. Not Discovery Engine datastores for Gmail/Calendar/Drive")
        print("\n✅ SOLUTION: Use direct Gmail/Calendar/Drive APIs in your agents")
        print("   (Already implemented in updated agent code)")

    print()


if __name__ == '__main__':
    main()
