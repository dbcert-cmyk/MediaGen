#!/usr/bin/env python3
"""
Check Discovery Engine Datastores
Verifies that required datastores exist and are properly configured
"""

import os
from google.cloud import discoveryengine_v1
from google.api_core import exceptions

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = "global"

# Required datastores for the demo
REQUIRED_DATASTORES = [
    "demo-gmail-datastore",
    "demo-calendar-datastore",
    "demo-drive-datastore"
]


def check_datastores():
    """Check if all required datastores exist and their status"""

    print("=" * 70)
    print("Discovery Engine Datastore Status Check")
    print("=" * 70)
    print(f"\nProject: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print()

    # Initialize client
    try:
        client = discoveryengine_v1.DataStoreServiceClient()
    except Exception as e:
        print(f"❌ Error creating Discovery Engine client: {e}")
        print("\nMake sure you have:")
        print("  1. Enabled Discovery Engine API")
        print("  2. Installed: pip install google-cloud-discoveryengine")
        print("  3. Authenticated: gcloud auth application-default login")
        return

    # List all datastores
    parent = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection"

    try:
        print("📋 Listing all datastores...")
        print()

        request = discoveryengine_v1.ListDataStoresRequest(
            parent=parent
        )

        response = client.list_data_stores(request=request)

        found_datastores = {}
        datastore_count = 0

        for datastore in response:
            datastore_count += 1
            name = datastore.name.split('/')[-1]
            found_datastores[name] = datastore

            print(f"Datastore #{datastore_count}: {name}")
            print(f"  Display Name: {datastore.display_name}")
            print(f"  Content Config: {datastore.content_config}")
            print(f"  Industry Vertical: {datastore.industry_vertical}")

            # Parse full resource name
            print(f"  Full Path: {datastore.name}")
            print()

        if datastore_count == 0:
            print("⚠️  No datastores found in this project.")
            print()

        # Check required datastores
        print("=" * 70)
        print("Required Datastores Status")
        print("=" * 70)
        print()

        all_present = True
        for required_name in REQUIRED_DATASTORES:
            if required_name in found_datastores:
                print(f"✅ {required_name}")
                ds = found_datastores[required_name]
                print(f"   └─ Display Name: {ds.display_name}")
                print(f"   └─ Type: {ds.content_config}")
            else:
                print(f"❌ {required_name} - NOT FOUND")
                all_present = False
            print()

        # Summary
        print("=" * 70)
        print("Summary")
        print("=" * 70)
        print()

        if all_present:
            print("✅ All required datastores are present!")
            print()
            print("Next steps:")
            print("  1. Verify datastores are syncing (check in Cloud Console)")
            print("  2. Register your agents in Gemini Enterprise")
            print("  3. Connect these datastores to your agents")
        else:
            print("⚠️  Missing datastores detected!")
            print()
            print("To create missing datastores:")
            print("  1. Go to: https://console.cloud.google.com/gen-app-builder/data-stores")
            print(f"  2. Select project: {PROJECT_ID}")
            print("  3. Create datastores with these EXACT names:")
            for required_name in REQUIRED_DATASTORES:
                if required_name not in found_datastores:
                    print(f"     - {required_name}")

        print()

    except exceptions.PermissionDenied as e:
        print(f"❌ Permission Denied: {e}")
        print("\nMake sure you have Discovery Engine permissions.")
        print("Required role: roles/discoveryengine.admin or roles/discoveryengine.viewer")
    except exceptions.NotFound as e:
        print(f"❌ Not Found: {e}")
        print("\nMake sure Discovery Engine API is enabled:")
        print("  gcloud services enable discoveryengine.googleapis.com")
    except Exception as e:
        print(f"❌ Error listing datastores: {e}")
        print(f"\nError type: {type(e).__name__}")


if __name__ == "__main__":
    check_datastores()
