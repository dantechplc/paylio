import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from django.core.mail import send_mail
from django.conf import settings

# === CONFIG ===
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Path to your JSON key
DRIVE_FOLDER_ID = '1EFDKPoY4axt9Iv3lmoXoPkd93tD0cK-N'  # Replace with your Drive folder ID
BACKUP_EMAIL = 'chukwujidan@gmail.com'
DB_PATH = 'db.sqlite3'


def backup_to_drive(file_path, file_name):
    # Authenticate using the service account
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )

    service = build('drive', 'v3', credentials=creds)

    file_metadata = {'name': file_name, 'parents': [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(file_path, mimetype='application/octet-stream')
    uploaded = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    print(f"✅ Backup successful. File ID: {uploaded.get('id')}")

    # Send an email notification
    try:
        send_mail(
            subject="Paylio Backup Completed ✅",
            message=f"Backup file '{file_name}' uploaded successfully to Google Drive.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[BACKUP_EMAIL],
            fail_silently=False,
        )
        print("📧 Email notification sent.")
    except Exception as e:
        print(f"⚠️ Failed to send email: {e}")


if __name__ == "__main__":
    date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_to_drive(DB_PATH, f"backup_database-{date}.db")
