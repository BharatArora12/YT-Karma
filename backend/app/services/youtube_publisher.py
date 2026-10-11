import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from app.config import settings

logger = logging.getLogger(__name__)

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def _get_credentials_file() -> Path:
    return settings.tokens_dir / "youtube_credentials.json"


def _get_client_config() -> Optional[Dict[str, Any]]:
    """Builds OAuth client configuration from env vars or client_secrets.json."""
    secrets_path = Path(settings.GOOGLE_CLIENT_SECRETS_FILE)
    if secrets_path.exists():
        try:
            with open(secrets_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read client_secrets.json: {e}")

    client_id = settings.GOOGLE_CLIENT_ID or os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = settings.GOOGLE_CLIENT_SECRET or os.environ.get("GOOGLE_CLIENT_SECRET")

    if client_id and client_secret and "your_google" not in client_id:
        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        }
    return None


def get_oauth_authorization_url() -> str:
    """Generates the Google OAuth 2.0 authorization URL."""
    config = _get_client_config()
    if not config:
        # Fallback simulation URL if credentials not configured
        return f"http://localhost:8000/api/auth/google/callback?code=mock_oauth_code"

    flow = Flow.from_client_config(
        client_config=config,
        scopes=YOUTUBE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def handle_oauth_callback(code: str) -> Dict[str, Any]:
    """Exchanges authorization code for credentials and saves them."""
    if code == "mock_oauth_code":
        # Save a demo session for developer testing
        demo_creds = {
            "token": "demo_access_token",
            "refresh_token": "demo_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "demo_client_id",
            "scopes": YOUTUBE_SCOPES,
            "channel_title": "Demo YouTube Channel",
            "channel_id": "UC_DEMO123456789",
        }
        with open(_get_credentials_file(), "w", encoding="utf-8") as f:
            json.dump(demo_creds, f, indent=2)
        return {"status": "success", "channel_title": "Demo YouTube Channel"}

    config = _get_client_config()
    if not config:
        raise ValueError("Google OAuth credentials are not configured in settings or client_secrets.json")

    flow = Flow.from_client_config(
        client_config=config,
        scopes=YOUTUBE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    flow.fetch_token(code=code)
    creds = flow.credentials

    # Convert to serialized dict
    creds_dict = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
    }

    with open(_get_credentials_file(), "w", encoding="utf-8") as f:
        json.dump(creds_dict, f, indent=2)

    return get_channel_info()


def get_stored_credentials() -> Optional[Credentials]:
    """Retrieves and refreshes stored credentials."""
    creds_path = _get_credentials_file()
    if not creds_path.exists():
        return None

    try:
        with open(creds_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("token") == "demo_access_token":
            # Mock mode
            return None

        creds = Credentials(
            token=data.get("token"),
            refresh_token=data.get("refresh_token"),
            token_uri=data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            scopes=data.get("scopes", YOUTUBE_SCOPES),
        )

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save refreshed token
            data["token"] = creds.token
            with open(creds_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        return creds
    except Exception as e:
        logger.error(f"Error loading stored credentials: {e}")
        return None


def get_channel_info() -> Dict[str, Any]:
    """Fetches authenticated YouTube channel profile info."""
    creds_path = _get_credentials_file()
    if not creds_path.exists():
        return {"authenticated": False, "message": "No YouTube account connected."}

    try:
        with open(creds_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("token") == "demo_access_token":
            return {
                "authenticated": True,
                "channel_title": data.get("channel_title", "Demo Creator Channel"),
                "channel_id": data.get("channel_id", "UC_DEMO123"),
                "thumbnail_url": "https://api.dicebear.com/7.x/identicon/svg?seed=YouTube",
                "message": "Connected in demo simulation mode.",
            }

        creds = get_stored_credentials()
        if not creds:
            return {"authenticated": False, "message": "Expired or invalid credentials."}

        youtube = build("youtube", "v3", credentials=creds)
        response = youtube.channels().list(mine=True, part="snippet").execute()

        items = response.get("items", [])
        if not items:
            return {"authenticated": True, "channel_title": "YouTube User", "channel_id": ""}

        snippet = items[0]["snippet"]
        return {
            "authenticated": True,
            "channel_title": snippet.get("title"),
            "channel_id": items[0].get("id"),
            "thumbnail_url": snippet.get("thumbnails", {}).get("default", {}).get("url"),
            "message": "Connected to YouTube account.",
        }
    except Exception as e:
        return {"authenticated": False, "message": f"Connection check failed: {str(e)}"}


def upload_short_to_youtube(
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy_status: str = "private",
) -> Dict[str, Any]:
    """
    Uploads the rendered vertical short to YouTube via YouTube Data API v3.
    """
    # Ensure Title includes #Shorts tag for YouTube algorithm
    if "#Shorts" not in title and "#shorts" not in title:
        title = f"{title} #Shorts"

    creds_path = _get_credentials_file()
    if not creds_path.exists():
        raise RuntimeError("No YouTube account connected. Please authenticate with Google first.")

    with open(creds_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Demo Simulation mode
    if data.get("token") == "demo_access_token":
        import uuid
        mock_id = f"demo_{uuid.uuid4().hex[:11]}"
        return {
            "success": True,
            "youtube_video_id": mock_id,
            "youtube_url": f"https://youtube.com/shorts/{mock_id}",
            "message": f"Short published in Demo Simulation mode (ID: {mock_id})",
        }

    creds = get_stored_credentials()
    if not creds:
        raise RuntimeError("Google OAuth credentials expired or invalid. Please re-authenticate.")

    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:20],
            "categoryId": "22",  # People & Blogs
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=1024 * 1024 * 4  # 4MB chunks
    )

    insert_request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = insert_request.next_chunk()
        if status:
            logger.info(f"Upload progress: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    shorts_url = f"https://youtube.com/shorts/{video_id}"

    return {
        "success": True,
        "youtube_video_id": video_id,
        "youtube_url": shorts_url,
        "message": f"Successfully published to YouTube! URL: {shorts_url}",
    }
