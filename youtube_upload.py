"""
YouTube uploader — uploads a video to YOUR channel via the YouTube Data API v3
(videos.insert) using OAuth 2.0.

ONE-TIME SETUP
--------------
1. In Google Cloud Console (same project as your API key), enable
   "YouTube Data API v3".
2. APIs & Services -> OAuth consent screen -> External -> add yourself as a
   Test user (your Google account).
3. APIs & Services -> Credentials -> Create Credentials -> OAuth client ID ->
   Application type: "Desktop app" -> download the JSON.
4. Save that file as:  .credentials/client_secret.json  (in this project root)

The first upload opens a browser for consent and stores a refresh token in
.credentials/youtube_token.json, so subsequent uploads need no interaction.

QUOTA: each upload costs ~1600 of your 10,000/day units (~6 uploads/day),
shared with the footage-search quota.

Usage (standalone test):
    venv\\Scripts\\python.exe youtube_upload.py "path\\to\\final-1.mp4" "My Title"
"""

import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from loguru import logger

from app.config import config
from app.utils import utils

# youtube.upload covers videos.insert, including setting publishAt for scheduling.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

CRED_DIR = os.path.join(utils.root_dir(), ".credentials")
CLIENT_SECRET_FILE = os.path.join(CRED_DIR, "client_secret.json")
TOKEN_FILE = os.path.join(CRED_DIR, "youtube_token.json")


def get_authenticated_service():
    os.makedirs(CRED_DIR, exist_ok=True)
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CLIENT_SECRET_FILE):
                raise FileNotFoundError(
                    f"Missing OAuth client secret: {CLIENT_SECRET_FILE}\n"
                    "See the setup steps at the top of youtube_upload.py."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        logger.info(f"saved youtube token to {TOKEN_FILE}")
    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    tags=None,
    category_id: str = None,
    privacy: str = None,
    publish_at: str = None,
) -> dict:
    """
    Upload one video. Returns {"success": bool, "video_id": str, "url": str}.

    privacy   : "private" | "unlisted" | "public" (default from config)
    publish_at: RFC3339 UTC, e.g. "2026-06-20T09:00:00Z". If set, the video is
                uploaded private and auto-published by YouTube at that time.
    category_id: YouTube category; default 27 = Education.
    """
    if not os.path.exists(video_path):
        return {"success": False, "error": f"file not found: {video_path}"}

    privacy = privacy or config.app.get("youtube_upload_privacy", "private")
    category_id = category_id or str(config.app.get("youtube_upload_category_id", "27"))

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }
    if publish_at:
        # Scheduled publish requires the video to start private.
        body["status"]["privacyStatus"] = "private"
        body["status"]["publishAt"] = publish_at

    try:
        youtube = get_authenticated_service()
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/*")
        request = youtube.videos().insert(
            part="snippet,status", body=body, media_body=media
        )
        logger.info(f"uploading '{title}' ({privacy}) from {video_path}")
        response = None
        while response is None:
            _, response = request.next_chunk()
        video_id = response["id"]
        url = f"https://youtu.be/{video_id}"
        logger.success(f"uploaded: {url}")
        return {"success": True, "video_id": video_id, "url": url}
    except HttpError as e:
        logger.error(f"youtube upload failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"youtube upload failed: {e}")
        return {"success": False, "error": str(e)}


def set_thumbnail(video_id: str, image_path: str) -> dict:
    """
    Set a custom thumbnail on an existing video. Requires the channel to be
    verified for custom thumbnails (youtube.com/verify) — otherwise YouTube
    returns a 403 and we surface a clear hint instead of crashing the upload.
    """
    if not image_path or not os.path.exists(image_path):
        return {"success": False, "error": f"thumbnail not found: {image_path}"}
    try:
        youtube = get_authenticated_service()
        media = MediaFileUpload(image_path, mimetype="image/jpeg")
        youtube.thumbnails().set(videoId=video_id, media_body=media).execute()
        logger.success(f"thumbnail set for {video_id}")
        return {"success": True}
    except HttpError as e:
        msg = str(e)
        if "forbidden" in msg.lower() or "403" in msg:
            logger.warning(
                "thumbnail rejected — the channel is likely not verified for custom "
                "thumbnails yet. Verify at https://www.youtube.com/verify, then it will work."
            )
        else:
            logger.error(f"set_thumbnail failed: {e}")
        return {"success": False, "error": msg}
    except Exception as e:
        logger.error(f"set_thumbnail failed: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Usage: python youtube_upload.py "<video_path>" "<title>" [privacy]')
        sys.exit(1)
    path, title = sys.argv[1], sys.argv[2]
    priv = sys.argv[3] if len(sys.argv) > 3 else None
    result = upload_video(path, title, description="Uploaded via automated pipeline.", privacy=priv)
    print(result)
    sys.exit(0 if result.get("success") else 1)
