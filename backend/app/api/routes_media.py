from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config import settings

router = APIRouter(prefix="/api/media", tags=["Media Streaming"])


@router.get("/shorts/{filename}")
def stream_rendered_short(filename: str):
    """Streams the rendered vertical 9:16 Short MP4 video."""
    target_file = settings.shorts_dir / filename
    if not target_file.exists() or not target_file.is_file():
        raise HTTPException(status_code=404, detail="Short video file not found.")

    return FileResponse(
        path=str(target_file),
        media_type="video/mp4",
        filename=filename,
    )


@router.get("/subtitles/{filename}")
def get_subtitle_file(filename: str):
    """Retrieves the generated ASS subtitle file."""
    target_file = settings.subtitles_dir / filename
    if not target_file.exists() or not target_file.is_file():
        raise HTTPException(status_code=404, detail="Subtitle file not found.")

    return FileResponse(
        path=str(target_file),
        media_type="text/plain",
        filename=filename,
    )


@router.get("/raw/{job_id}")
def stream_raw_download(job_id: str):
    """Streams the original source video downloaded from YouTube."""
    target_file = settings.downloads_dir / f"{job_id}.mp4"
    if not target_file.exists():
        candidates = list(settings.downloads_dir.glob(f"{job_id}*"))
        for c in candidates:
            if c.suffix.lower() == ".mp4":
                target_file = c
                break

    if not target_file.exists():
        raise HTTPException(status_code=404, detail="Source video not found.")

    return FileResponse(
        path=str(target_file),
        media_type="video/mp4",
    )
