import datetime
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']


def authenticate():
    creds = None
    # Check if the token.json file already exists for stored credentials
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If credentials are not valid or don't exist, authenticate the user
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Use credentials.json to request new authorization
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the new credentials to token.json for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds


def backup_to_drive(file_path, file_name):
    creds = authenticate()
    # Create Google Drive service
    service = build('drive', 'v3', credentials=creds)

    # Define file metadata and upload
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, mimetype='application/octet-stream')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"Backup successful. File ID: {file.get('id')}")


# Replace with your actual SQLite database path
db_path = 'db.sqlite3'
date = datetime.datetime.now().strftime("%Y-%m-%d")
backup_to_drive(db_path, f'backup_database-{date}.db')
