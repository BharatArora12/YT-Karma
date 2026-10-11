from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.models.schemas import (
    PublishRequest,
    PublishResponse,
    GoogleAuthUrlResponse,
    GoogleAuthStatusResponse,
)
from app.services.pipeline_worker import ShortsPipelineWorker
from app.services.youtube_publisher import (
    get_oauth_authorization_url,
    handle_oauth_callback,
    get_channel_info,
)

router = APIRouter(prefix="/api", tags=["Publishing & Google OAuth"])


@router.get("/auth/google/url", response_model=GoogleAuthUrlResponse)
def get_auth_url():
    """Generates the Google OAuth 2.0 authorization URL for YouTube upload scope."""
    try:
        url = get_oauth_authorization_url()
        return GoogleAuthUrlResponse(auth_url=url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate OAuth URL: {str(e)}")


@router.get("/auth/google/callback")
def oauth_callback(code: str = Query(...)):
    """Receives the authorization code from Google OAuth redirect."""
    try:
        result = handle_oauth_callback(code)
        # Redirect back to frontend dashboard with success flag
        return RedirectResponse(url="http://localhost:3000/?auth=success")
    except Exception as e:
        return RedirectResponse(url=f"http://localhost:3000/?auth=error&msg={str(e)}")


@router.get("/auth/google/status", response_model=GoogleAuthStatusResponse)
def get_auth_status():
    """Checks whether a valid Google/YouTube account is currently connected."""
    info = get_channel_info()
    return GoogleAuthStatusResponse(
        authenticated=info.get("authenticated", False),
        channel_title=info.get("channel_title"),
        channel_id=info.get("channel_id"),
        thumbnail_url=info.get("thumbnail_url"),
        message=info.get("message"),
    )


@router.post("/publish", response_model=PublishResponse)
def publish_short(req: PublishRequest):
    """
    Step 5: Uploads the rendered short directly to YouTube with AI-generated metadata.
    """
    try:
        result = ShortsPipelineWorker.publish_clip(
            job_id=req.job_id,
            clip_id=req.clip_id,
            title=req.title,
            description=req.description,
            tags=req.tags,
            privacy_status=req.privacy_status,
        )
        return PublishResponse(
            success=result.get("success", True),
            youtube_video_id=result.get("youtube_video_id"),
            youtube_url=result.get("youtube_url"),
            message=result.get("message", "Uploaded successfully!"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
