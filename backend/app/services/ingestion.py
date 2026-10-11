import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Callable, Optional
import yt_dlp
from app.config import settings
from app.utils.windows_file_lock import robust_replace
from app.utils.ffmpeg_checker import find_ffmpeg_executable

logger = logging.getLogger(__name__)


def extract_video_info(youtube_url: str) -> Dict[str, Any]:
    """Extracts metadata from a YouTube video without downloading."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        return {
            "title": info.get("title", "Untitled Video"),
            "author": info.get("uploader", "Unknown Creator"),
            "duration": float(info.get("duration", 0.0)),
            "thumbnail": info.get("thumbnail", ""),
            "description": info.get("description", ""),
        }


def download_youtube_media(
    youtube_url: str,
    job_id: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Dict[str, Any]:
    """
    Downloads the YouTube video and extracts high-quality video and audio files.
    Robustly handles OneDrive / Windows file locks ([WinError 32]) with retry mechanisms.
    Returns metadata and paths to local media files.
    """
    downloads_dir = settings.downloads_dir
    video_output_template = str(downloads_dir / f"{job_id}_raw.%(ext)s")
    target_mp4 = downloads_dir / f"{job_id}_raw.mp4"
    audio_wav_path = downloads_dir / f"{job_id}.wav"

    # 1. Pre-check: recover from previous interrupted/temp download if present
    temp_mp4 = downloads_dir / f"{job_id}_raw.temp.mp4"
    if temp_mp4.exists():
        try:
            logger.info(f"Recovering existing temp file: {temp_mp4} -> {target_mp4}")
            robust_replace(str(temp_mp4), str(target_mp4))
        except Exception as e:
            logger.warning(f"Could not rename leftover temp file: {e}")

    # Check if a valid downloaded video already exists for this job (e.g., resumed or retried)
    if target_mp4.exists() and target_mp4.stat().st_size > 1024 * 1024:
        logger.info(f"Existing valid video found for job {job_id} ({target_mp4.stat().st_size} bytes). Skipping re-download.")
        if progress_callback:
            progress_callback(80.0, "Found already downloaded video stream, preparing audio...")
        meta = extract_video_info(youtube_url)
        actual_video = target_mp4
    else:
        # Download via yt-dlp
        def ydl_hook(d):
            if d["status"] == "downloading" and progress_callback:
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                if total_bytes > 0:
                    pct = (downloaded / total_bytes) * 100
                    progress_callback(pct, f"Downloading video stream: {pct:.1f}%")

        ydl_opts = {
            "format": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": video_output_template,
            "merge_output_format": "mp4",
            "progress_hooks": [ydl_hook],
            "quiet": False,
            "no_warnings": True,
            "keepvideo": True,
            "overwrites": True,
            "file_access_retries": 20,
            "retries": 15,
            "windowsfilenames": True,
        }

        ffmpeg_bin = find_ffmpeg_executable()
        if ffmpeg_bin:
            ydl_opts["ffmpeg_location"] = str(Path(ffmpeg_bin).parent)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            meta = {
                "title": info.get("title", "Untitled Video"),
                "author": info.get("uploader", "Unknown Creator"),
                "duration": float(info.get("duration", 0.0)),
                "thumbnail": info.get("thumbnail", ""),
                "description": info.get("description", ""),
            }

        # Handle post-download temp rename if yt-dlp left .temp.mp4 due to OneDrive race condition
        if temp_mp4.exists() and not target_mp4.exists():
            robust_replace(str(temp_mp4), str(target_mp4))

        # Find the downloaded video file
        actual_video = None
        if target_mp4.exists():
            actual_video = target_mp4
        else:
            for f in downloads_dir.glob(f"{job_id}*"):
                if f.suffix.lower() == ".mp4" and "temp" not in f.name:
                    actual_video = f
                    break

    if not actual_video or not Path(actual_video).exists():
        raise RuntimeError(f"Video download failed: No valid .mp4 file produced in {downloads_dir}")

    # 2. Extract clean 16kHz mono WAV audio directly via FFmpeg for faster-whisper
    # Doing this directly avoids yt-dlp's FFmpegExtractAudio post-processor file-locking issues on Windows
    actual_audio = None
    if not audio_wav_path.exists():
        if progress_callback:
            progress_callback(90.0, "Extracting clean speech audio track for faster-whisper...")
        ffmpeg_bin = find_ffmpeg_executable() or "ffmpeg"
        try:
            cmd = [
                ffmpeg_bin,
                "-y",
                "-i", str(actual_video),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(audio_wav_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            actual_audio = audio_wav_path
        except Exception as e:
            logger.warning(f"Direct WAV extraction failed: {e}. Whisper will read video file audio directly.")
            actual_audio = actual_video
    else:
        actual_audio = audio_wav_path

    meta["video_path"] = str(actual_video)
    meta["audio_path"] = str(actual_audio)
    return meta
