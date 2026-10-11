import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.utils.windows_file_lock import patch_os_rename
from app.utils.ffmpeg_checker import check_ffmpeg_available
from app.services.youtube_publisher import get_channel_info
from app.api.routes_jobs import router as jobs_router
from app.api.routes_publish import router as publish_router
from app.api.routes_media import router as media_router

# Apply global Windows file locking patch immediately on startup
patch_os_rename()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("yt_shorts_backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("==================================================")
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info("Initializing storage folders...")
    _ = settings.downloads_dir
    _ = settings.transcripts_dir
    _ = settings.subtitles_dir
    _ = settings.shorts_dir
    _ = settings.tokens_dir

    # Check FFmpeg
    has_ffmpeg, ffmpeg_msg = check_ffmpeg_available()
    if has_ffmpeg:
        logger.info(f"[OK] {ffmpeg_msg}")
    else:
        logger.warning(f"[NOTICE] {ffmpeg_msg}")

    # Check Gemini API Key
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here":
        logger.info("[OK] Google Gemini 1.5 Flash API Key is configured.")
    else:
        logger.warning("[NOTICE] GEMINI_API_KEY is not set. Intelligent heuristic clip selection will be used as fallback.")

    logger.info("Backend service is fully initialized and ready.")
    logger.info("==================================================")
    yield
    logger.info("Shutting down YT Shorts Management System backend.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Automated YouTube-to-Shorts repurposing and publishing platform backend.",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow local frontend Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(jobs_router)
app.include_router(publish_router)
app.include_router(media_router)


@app.get("/")
def read_root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
    }


@app.get("/api/health")
def health_check():
    """Returns diagnostic health status of all subsystems."""
    has_ffmpeg, ffmpeg_msg = check_ffmpeg_available()
    channel_info = get_channel_info()

    return {
        "status": "healthy",
        "python_version": sys.version.split()[0],
        "ffmpeg": {
            "available": has_ffmpeg,
            "message": ffmpeg_msg,
        },
        "gemini": {
            "configured": bool(settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "your_gemini_api_key_here"),
            "model": settings.GEMINI_MODEL,
        },
        "youtube_oauth": {
            "authenticated": channel_info.get("authenticated", False),
            "channel_title": channel_info.get("channel_title"),
            "channel_id": channel_info.get("channel_id"),
        },
        "whisper": {
            "model_size": settings.WHISPER_MODEL_SIZE,
            "device": settings.WHISPER_DEVICE,
            "compute_type": settings.WHISPER_COMPUTE_TYPE,
        },
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
