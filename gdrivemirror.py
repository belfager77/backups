import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# --- Configuration ---
SCOPES = ['https://www.googleapis.com/auth/drive']
LOCAL_FOLDER_PATH = '/home/simon/backup'  # Your local backup folder
DRIVE_FOLDER_NAME = 'BACKUP'              # Desired name in Google Drive

# --- Helper Functions ---
def get_drive_service():
    """Shows basic usage of the Drive v3 API.
    Authenticates the user and returns the service object.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def find_or_create_folder(service, folder_name, parent_id=None):
    """Checks if a folder exists in Google Drive, creates it if not."""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = response.get('files', [])

    if files:
        # Folder exists, return its ID
        print(f'Folder "{folder_name}" found with ID: {files[0]["id"]}')
        return files[0]['id']
    else:
        # Folder does not exist, create it
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]

        file = service.files().create(body=file_metadata, fields='id').execute()
        print(f'Folder "{folder_name}" created with ID: {file["id"]}')
        return file['id']

def upload_file(service, file_path, parent_folder_id):
    """Uploads a single file to a specific Google Drive folder."""
    file_name = os.path.basename(file_path)
    print(f'Uploading: {file_name}')

    # Check if the file already exists in the target folder
    query = f"name='{file_name}' and '{parent_folder_id}' in parents and trashed=false"
    response = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    existing_files = response.get('files', [])

    media = MediaFileUpload(file_path, resumable=True)
    if existing_files:
        # If it exists, update it (this is a simple way to "mirror" by overwriting)
        file_id = existing_files[0]['id']
        print(f'  File exists. Updating...')
        updated_file = service.files().update(fileId=file_id, media_body=media).execute()
        return updated_file['id']
    else:
        # If it's new, create it
        file_metadata = {'name': file_name, 'parents': [parent_folder_id]}
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file['id']

def mirror_local_folder_to_drive(service, local_path, drive_parent_id):
    """Recursively mirrors a local folder to a Google Drive folder."""
    for item in os.listdir(local_path):
        item_path = os.path.join(local_path, item)

        if os.path.isdir(item_path):
            # It's a subfolder: find or create it in Drive, then mirror its contents
            print(f'\nEntering folder: {item}')
            subfolder_drive_id = find_or_create_folder(service, item, drive_parent_id)
            mirror_local_folder_to_drive(service, item_path, subfolder_drive_id)
        else:
            # It's a file: upload it
            upload_file(service, item_path, drive_parent_id)

# --- Main Execution ---
if __name__ == '__main__':
    print("Starting Google Drive Mirror Script...")

    # 1. Authenticate and get the Drive service
    try:
        service = get_drive_service()
        print("Authentication successful.")
    except Exception as e:
        print(f"Authentication failed: {e}")
        exit()

    # 2. Find or create the main 'BACKUP' folder in Drive
    try:
        root_backup_folder_id = find_or_create_folder(service, DRIVE_FOLDER_NAME)
        print(f"Target Drive folder ready with ID: {root_backup_folder_id}")
    except HttpError as error:
        print(f"An API error occurred: {error}")
        exit()

    # 3. Start the mirroring process
    if not os.path.isdir(LOCAL_FOLDER_PATH):
        print(f"Error: Local folder '{LOCAL_FOLDER_PATH}' not found.")
        exit()

    print(f"\nMirroring '{LOCAL_FOLDER_PATH}' to Google Drive folder '{DRIVE_FOLDER_NAME}'...")
    mirror_local_folder_to_drive(service, LOCAL_FOLDER_PATH, root_backup_folder_id)

    print("\nMirroring complete!")
