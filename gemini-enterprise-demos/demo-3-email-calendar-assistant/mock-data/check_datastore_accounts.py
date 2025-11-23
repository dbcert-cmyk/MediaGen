#!/usr/bin/env python3
"""
Check which Google Workspace accounts your Discovery Engine datastores are connected to
"""

import os
from google.cloud import discoveryengine_v1

PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
LOCATION = "global"

# Your datastores
DATASTORES = {
    "Gmail": "demo-gmail-datastore_1763851937069_google_mail",
    "Calendar": "demo-calendar-datastore_1763851980966_google_calendar",
    "Drive": "demo-drive-datastore_1763851832394_google_drive"
}

def get_datastore_info():
    """Get information about each datastore including connected account"""

    print("="*60)
    print("Discovery Engine Datastore Account Info")
    print("="*60)
    print()

    client = discoveryengine_v1.DataStoreServiceClient()

    for name, datastore_id in DATASTORES.items():
        print(f"\n{name} Datastore:")
        print(f"  ID: {datastore_id}")

        try:
            # Get datastore details
            datastore_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/dataStores/{datastore_id}"

            datastore = client.get_data_store(name=datastore_path)

            print(f"  Status: {datastore.content_config}")
            print(f"  Type: {datastore.industry_vertical}")

            # Try to get data source info
            if hasattr(datastore, 'document_processing_config'):
                print(f"  Processing: {datastore.document_processing_config}")

            print(f"\n  ℹ️  To see connected account:")
            print(f"     1. Go to: https://console.cloud.google.com/gen-app-builder/data-stores?project={PROJECT_ID}")
            print(f"     2. Click on '{datastore_id.split('_')[0]}'")
            print(f"     3. Look for 'Data source' or 'Connected account' section")

        except Exception as e:
            print(f"  ⚠️  Could not retrieve details: {e}")
            print(f"\n  View in Console:")
            print(f"     https://console.cloud.google.com/gen-app-builder/data-stores?project={PROJECT_ID}")

    print(f"\n{'='*60}")
    print("Quick Access")
    print(f"{'='*60}")
    print(f"\nDirect link to datastores:")
    print(f"https://console.cloud.google.com/gen-app-builder/data-stores?project={PROJECT_ID}")
    print()

if __name__ == '__main__':
    get_datastore_info()
