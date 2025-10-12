import os
import datetime
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'paylio.settings_pro')
django.setup()

from django.core.mail import send_mail
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Google Drive API scope
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Backup file path
DB_PATH = 'db.sqlite3'
RECEIVER_EMAIL = 'chukwujidan@gmail.com'


def authenticate():
    """Authenticate with Google Drive API."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def send_notification(subject, message):
    """Send email using Django's configured SMTP."""
    try:
        send_mail(
            subject,
            message,
            None,  # Uses DEFAULT_FROM_EMAIL from settings.py
            [RECEIVER_EMAIL],
            fail_silently=False,
        )
        print("✅ Email notification sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")


def backup_to_drive(file_path, file_name):
    """Upload backup file to Google Drive."""
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)

    try:
        file_metadata = {'name': file_name}
        media = MediaFileUpload(file_path, mimetype='application/octet-stream')
        uploaded = service.files().create(
            body=file_metadata, media_body=media, fields='id'
        ).execute()

        file_id = uploaded.get('id')
        print(f"✅ Backup successful. File ID: {file_id}")
        send_notification(
            "✅ Database Backup Successful",
            f"The backup '{file_name}' was uploaded to Google Drive successfully.\nFile ID: {file_id}"
        )
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        send_notification(
            "❌ Database Backup Failed",
            f"An error occurred during backup:\n\n{e}"
        )


if __name__ == "__main__":
    date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_to_drive(DB_PATH, f'backup_database-{date}.db')
