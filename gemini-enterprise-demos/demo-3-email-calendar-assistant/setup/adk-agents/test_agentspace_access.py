#!/usr/bin/env python3
"""
Test access to AgentSpace datastores specifically
and diagnose permission issues
"""

from google.cloud import discoveryengine_v1
from google.auth import default
import google.auth

PROJECT_ID = "ai-testing-458318"
PROJECT_NUMBER = "805114253837"

# AgentSpace datastores (from the Gemini Enterprise UI)
AGENTSPACE_DATASTORES = {
    "AgentSpace Calendar": "projects/805114253837/locations/global/collections/default_collection/dataStores/agentspace-calendar_1747805896635_google_calendar",
    "AgentSpace Gmail": "projects/805114253837/locations/global/collections/default_collection/dataStores/agentspace-gmail_1747805749796_google_mail",
}


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

        # Try to get token info
        if hasattr(credentials, 'token'):
            print(f"Has token: {credentials.token is not None}")

        return credentials, project

    except Exception as e:
        print(f"Error getting credentials: {e}")
        return None, None


def test_datastore_access(name, datastore_path):
    """Test if we can access a specific datastore"""

    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"{'='*80}")
    print(f"Path: {datastore_path}")

    client = discoveryengine_v1.SearchServiceClient()

    # Try to search
    serving_config = f"{datastore_path}/servingConfigs/default_search"

    try:
        print(f"\nAttempting search...")
        request = discoveryengine_v1.SearchRequest(
            serving_config=serving_config,
            query="*",
            page_size=5
        )

        response = client.search(request)
        results = list(response.results)

        if len(results) > 0:
            print(f"✅ SUCCESS - Found {len(results)} documents")
            print(f"\nSample document:")
            doc = results[0].document
            print(f"   ID: {doc.id}")
            if hasattr(doc, 'derived_struct_data') and doc.derived_struct_data:
                print(f"   Fields: {list(doc.derived_struct_data.keys())}")
            return True
        else:
            print(f"⚠️  No documents returned (but no error)")
            return False

    except google.auth.exceptions.RefreshError as e:
        print(f"❌ AUTHENTICATION ERROR")
        print(f"   {e}")
        print(f"\n   This means:")
        print(f"   - Credentials are invalid or expired")
        print(f"   - Need to run: gcloud auth application-default login")
        return False

    except Exception as e:
        error_str = str(e)

        if "PERMISSION_DENIED" in error_str or "403" in error_str:
            print(f"❌ PERMISSION DENIED")
            print(f"   Error: {error_str}")
            print(f"\n   This means:")
            print(f"   - The service account doesn't have access to this datastore")
            print(f"   - Need to grant 'Discovery Engine Viewer' role")
            print(f"\n   Solution:")
            print(f"   1. Find your service account email (shown above)")
            print(f"   2. Go to IAM page:")
            print(f"      https://console.cloud.google.com/iam-admin/iam?project={PROJECT_ID}")
            print(f"   3. Grant role: 'Discovery Engine Viewer'")
            print(f"   4. Or grant at datastore level in Discovery Engine console")

        elif "NOT_FOUND" in error_str:
            print(f"❌ DATASTORE NOT FOUND")
            print(f"   Error: {error_str}")
            print(f"   The datastore path might be incorrect")

        else:
            print(f"❌ ERROR: {error_str}")

        return False


def main():
    """Run diagnostics"""

    print("="*80)
    print("AgentSpace Datastore Access Diagnostic")
    print("="*80)
    print()

    # Check credentials
    creds, project = check_current_credentials()

    if not creds:
        print("\n❌ Cannot proceed without credentials")
        print("\nRun this first:")
        print("  gcloud auth application-default login")
        return

    # Test each AgentSpace datastore
    print("\n\n" + "="*80)
    print("Testing AgentSpace Datastores")
    print("="*80)

    results = {}
    for name, path in AGENTSPACE_DATASTORES.items():
        results[name] = test_datastore_access(name, path)

    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)

    accessible = [name for name, success in results.items() if success]
    denied = [name for name, success in results.items() if not success]

    if accessible:
        print(f"\n✅ Accessible datastores: {', '.join(accessible)}")
        print(f"\nYou can use these in your agent code!")

    if denied:
        print(f"\n❌ Permission denied datastores: {', '.join(denied)}")
        print(f"\nThese need IAM permissions configured.")
        print(f"\nNext steps:")
        print(f"1. Grant 'Discovery Engine Viewer' role to your service account")
        print(f"2. Or run with user credentials: gcloud auth application-default login")
        print(f"3. Wait a few minutes for permissions to propagate")
        print(f"4. Re-run this script")

    if not accessible and not denied:
        print(f"\n⚠️  All datastores returned empty (no permission errors)")
        print(f"\nThis could mean:")
        print(f"1. Datastores are genuinely empty")
        print(f"2. Service account can read but there's no data indexed yet")
        print(f"3. Data is only accessible via user credentials")

    print()


if __name__ == '__main__':
    main()
