#!/usr/bin/env python3
"""
Populate Google Drive with mock demo data
Uses Drive API to create realistic demo documents
"""

import json
import os
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
import io

# Configuration
PROJECT_ID = os.environ.get("PROJECT_ID", "ai-testing-458318")
SCOPES = ['https://www.googleapis.com/auth/drive']


def create_drive_service():
    """Create Drive API service"""
    from google.auth import default
    credentials, _ = default(scopes=SCOPES)

    service = build('drive', 'v3', credentials=credentials)
    return service


def create_or_get_folder(service, folder_name, parent_id=None):
    """Create folder in Drive or get existing"""

    # Check if folder already exists
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()

    folders = results.get('files', [])

    if folders:
        return folders[0]['id']

    # Create new folder
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_id:
        file_metadata['parents'] = [parent_id]

    folder = service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()

    return folder['id']


def create_text_file(service, name, content, folder_id, mime_type='text/plain'):
    """Create a text-based file in Drive"""

    file_metadata = {
        'name': name,
        'parents': [folder_id]
    }

    # Convert mime type for Google Workspace formats
    if mime_type == 'application/vnd.google-apps.document':
        # Create as Google Doc
        file_metadata['mimeType'] = 'application/vnd.google-apps.document'
        media = MediaInMemoryUpload(
            content.encode('utf-8'),
            mimetype='text/plain',
            resumable=True
        )
    elif mime_type == 'application/vnd.google-apps.spreadsheet':
        # Create as Google Sheet (with CSV content)
        file_metadata['mimeType'] = 'application/vnd.google-apps.spreadsheet'
        media = MediaInMemoryUpload(
            content.encode('utf-8'),
            mimetype='text/csv',
            resumable=True
        )
    else:
        # Create as regular file (PDF, etc.)
        file_metadata['mimeType'] = mime_type
        media = MediaInMemoryUpload(
            content.encode('utf-8'),
            mimetype=mime_type,
            resumable=True
        )

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, mimeType, webViewLink'
    ).execute()

    return file


def populate_drive_from_json(service, json_file='drive_mock_data.json'):
    """Populate Drive with documents from JSON file"""

    print("Loading mock Drive data...")
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Create root Demo Data folder
    root_folder_id = create_or_get_folder(service, 'Demo Data')
    print(f"✓ Root folder created/found: Demo Data\n")

    # Create all folders first
    folders = data.get('folders', [])
    folder_ids = {}

    print("Creating folders...")
    for folder_name in folders:
        folder_id = create_or_get_folder(service, folder_name, root_folder_id)
        folder_ids[folder_name] = folder_id
        print(f"  ✓ {folder_name}")

    print()

    # Create documents
    documents = data['documents']
    print(f"Creating {len(documents)} documents...\n")

    created_count = 0

    for doc in documents:
        print(f"Creating: {doc['name']}")

        try:
            folder_id = folder_ids.get(doc['folder'], root_folder_id)

            file = create_text_file(
                service,
                name=doc['name'],
                content=doc['content'],
                folder_id=folder_id,
                mime_type=doc.get('type', 'text/plain')
            )

            print(f"  ✓ Created: {file['id']}")
            print(f"    Type: {file['mimeType']}")
            print(f"    Link: {file.get('webViewLink', 'N/A')}")
            created_count += 1

        except Exception as e:
            print(f"  ✗ Error: {e}")

    print(f"\n{'='*60}")
    print(f"✅ Successfully created {created_count}/{len(documents)} documents")
    print(f"{'='*60}")

    print("\n📊 Drive Summary:")
    print(f"- Total folders: {len(folders)}")
    print(f"- Total documents: {created_count}")
    print(f"- Root folder: Demo Data")

    print("\nNote: Discovery Engine will sync these documents within 1-2 hours.")
    print("Check sync status with: python ../setup/adk-agents/check_datastores.py")


def list_demo_files(service):
    """List all files in Demo Data folder"""

    # Find Demo Data folder
    query = "name='Demo Data' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()

    folders = results.get('files', [])
    if not folders:
        print("No Demo Data folder found")
        return

    folder_id = folders[0]['id']

    # List all files in folder and subfolders
    query = f"'{folder_id}' in parents and trashed=false"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name, mimeType, webViewLink)',
        pageSize=100
    ).execute()

    files = results.get('files', [])

    print(f"\nFiles in Demo Data ({len(files)} items):")
    for file in files:
        print(f"- {file['name']} ({file['mimeType']})")


def verify_drive_access(service, target_email=None):
    """Verify we can access Drive for the target account"""
    try:
        about = service.about().get(fields='user').execute()
        current_email = about['user']['emailAddress']

        print(f"\n✓ Authenticated as: {current_email}")

        if target_email and target_email.lower() != current_email.lower():
            print(f"❌ ERROR: You specified {target_email}")
            print(f"   But you're authenticated as {current_email}")
            print(f"\nPlease authenticate as {target_email} or use {current_email}")
            return None

        return current_email

    except Exception as e:
        print(f"❌ Error accessing Drive: {e}")
        return None


def main():
    """Main entry point"""
    print("="*60)
    print("Google Drive Mock Data Population Tool")
    print("="*60)
    print()

    print("⚠️  IMPORTANT:")
    print("1. Make sure you have Drive API enabled")
    print("2. Run: gcloud auth application-default login")
    print("3. Grant Drive permissions when prompted")
    print("4. Files will be created in 'Demo Data' folder")
    print()

    # Ask for target email (unless already set by populate_all.py)
    target_email = os.environ.get('DEMO_TARGET_EMAIL', '').strip()

    if not target_email:
        print("Which Drive account should receive the mock data?")
        print("(This should match your Discovery Engine datastore connection)")
        target_email = input("Enter email address: ").strip()

        if not target_email:
            print("❌ Error: Email address is required")
            return

    print()

    try:
        service = create_drive_service()
        print("✓ Drive API authenticated")

        # Verify we can access the target account
        verified_email = verify_drive_access(service, target_email)
        if not verified_email:
            return

        print(f"\n🎯 Mock data will be created in: {verified_email}")
        print()

        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return

        populate_drive_from_json(service)

        # Optionally list created files
        print("\n" + "="*60)
        list_demo_files(service)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Run: gcloud services enable drive.googleapis.com")
        print("2. Run: gcloud auth application-default login")
        print("3. Ensure you have Drive API access")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
