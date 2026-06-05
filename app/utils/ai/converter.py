from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import FileResponse
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import os

router = APIRouter()

# Path to your service account JSON
SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# Authenticate with Google
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build("drive", "v3", credentials=creds)


def extract_file_id(drive_link: str) -> str:
    """Extract file ID from Google Drive link"""
    if "id=" in drive_link:
        return drive_link.split("id=")[1].split("&")[0]
    return drive_link.split("/d/")[1].split("/")[0]


def download_as_pdf(file_id: str, output_file: str = "output.pdf") -> str:
    """Download a Google Drive file as PDF and save locally"""
    file = service.files().get(fileId=file_id, fields="mimeType, name").execute()
    mime_type = file.get("mimeType")
    file_name = file.get("name")

    print(f"📂 Found file: {file_name} ({mime_type})")

    # Google Docs/Sheets/Slides → export to PDF
    if mime_type.startswith("application/vnd.google-apps"):
        request = service.files().export_media(fileId=file_id, mimeType="application/pdf")
    else:
        # Already a PDF or another type → just download
        request = service.files().get_media(fileId=file_id)

    with open(output_file, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"⬇️ Download {int(status.progress() * 100)}%")

    return output_file


@router.get("/download-pdf")
def download_pdf(drive_link: str = Query(..., description="Google Drive file link")):
    try:
        file_id = extract_file_id(drive_link)
        output_file = "downloaded.pdf"
        file_path = download_as_pdf(file_id, output_file)
        return FileResponse(file_path, filename=output_file, media_type="application/pdf")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


# import os
# import io
# import requests
# from googleapiclient.discovery import build
# from googleapiclient.http import MediaIoBaseDownload
# from google.oauth2 import service_account

# SERVICE_ACCOUNT_FILE = "service_account.json"
# SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# if not os.path.exists(SERVICE_ACCOUNT_FILE):
#     print("⚠️ service_account.json not found, creating a placeholder...")
#     with open(SERVICE_ACCOUNT_FILE, "w") as f:
#         f.write('{\n  "your_service_account_credentials_here": ""\n}')
#     print("Created service_account.json. Please download your real credentials from Google Cloud Console and replace the content.")
#     exit(1)  

# creds = service_account.Credentials.from_service_account_file(
#     SERVICE_ACCOUNT_FILE, scopes=SCOPES
# )
# service = build("drive", "v3", credentials=creds)

# def download_as_pdf(drive_link, output_file="output.pdf"):
#     if "id=" in drive_link:
#         file_id = drive_link.split("id=")[1].split("&")[0]
#     else:
#         file_id = drive_link.split("/d/")[1].split("/")[0]

#     file = service.files().get(fileId=file_id, fields="mimeType, name").execute()
#     mime_type = file.get("mimeType")
#     file_name = file.get("name")

#     print(f" Found file: {file_name} ({mime_type})")

#     if mime_type.startswith("application/vnd.google-apps"):
#         request = service.files().export_media(fileId=file_id, mimeType="application/pdf")
#     else:
#         request = service.files().get_media(fileId=file_id)

#     with open(output_file, "wb") as f:
#         downloader = MediaIoBaseDownload(f, request)
#         done = False
#         while not done:
#             status, done = downloader.next_chunk()
#             if status:
#                 print(f"⬇️ Download {int(status.progress() * 100)}%")

#     print(f"✅ File saved as {output_file}")


# download_as_pdf("https://drive.google.com/file/d/1F3LTa7sA4r6Qw5o31Ir1gF1fu4OLknJn/view")
