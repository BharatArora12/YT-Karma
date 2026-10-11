import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, List
from app.config import settings
from app.models.schemas import (
    JobResponse,
    JobStatus,
    ShortClipProposal,
    TranscriptData,
    TranscriptionWord,
)
from app.services.ingestion import download_youtube_media
from app.services.transcription import transcribe_audio
from app.services.ai_clip_selector import select_viral_clips
from app.services.video_processor import process_and_render_short
from app.services.youtube_publisher import upload_short_to_youtube

logger = logging.getLogger(__name__)

# In-memory job registry
_job_store: Dict[str, JobResponse] = {}
_job_store_lock = threading.Lock()


def _get_job_file(job_id: str) -> Path:
    p = settings.base_storage_path / "jobs"
    p.mkdir(parents=True, exist_ok=True)
    return p / f"{job_id}.json"


def save_job(job: JobResponse) -> None:
    """Updates in-memory store and serializes job to disk."""
    job.updated_at = datetime.now(timezone.utc).isoformat()
    with _job_store_lock:
        _job_store[job.job_id] = job

    try:
        fpath = _get_job_file(job.job_id)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(job.model_dump(), f, indent=2)
    except Exception as e:
        logger.error(f"Failed to persist job {job.job_id} to disk: {e}")


def get_job(job_id: str) -> Optional[JobResponse]:
    """Retrieves a job by ID from cache or disk."""
    with _job_store_lock:
        if job_id in _job_store:
            return _job_store[job_id]

    fpath = _get_job_file(job_id)
    if fpath.exists():
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                job = JobResponse(**data)
                with _job_store_lock:
                    _job_store[job_id] = job
                return job
        except Exception as e:
            logger.error(f"Failed to load job {job_id} from disk: {e}")
    return None


def list_jobs() -> List[JobResponse]:
    """Lists all recent jobs."""
    jobs_dir = settings.base_storage_path / "jobs"
    if jobs_dir.exists():
        for f in jobs_dir.glob("*.json"):
            jid = f.stem
            get_job(jid)
    with _job_store_lock:
        return sorted(_job_store.values(), key=lambda j: j.created_at, reverse=True)


class ShortsPipelineWorker:
    """
    Core Pipeline Worker Service executing the 5 Sequential Steps:
    1. Ingestion: yt-dlp download & info extraction
    2. Transcription: faster-whisper with word timestamps
    3. AI Selection: Gemini 1.5 Flash structured clip & metadata extraction
    4. Video Processing: FFmpeg 9:16 vertical crop + dynamic .ass caption burning
    5. Publishing: YouTube Data API v3 upload
    """

    @classmethod
    def execute_pipeline(
        cls,
        job_id: str,
        youtube_url: str,
        clip_count: int = 3,
        min_duration: int = 30,
        max_duration: int = 60,
    ) -> None:
        """Sequential execution runner run in background worker thread."""
        job = get_job(job_id)
        if not job:
            logger.error(f"Job {job_id} not found.")
            return

        try:
            logger.info(f"Starting pipeline execution for Job: {job_id} (URL: {youtube_url})")

            # ----------------------------------------------------
            # STEP 1: INGESTION (yt-dlp)
            # ----------------------------------------------------
            job.status = JobStatus.DOWNLOADING
            job.progress = 10
            job.current_step = "Step 1/5: Downloading video and audio streams via yt-dlp..."
            save_job(job)

            def dl_cb(pct: float, msg: str):
                job.progress = int(10 + (pct * 0.20))  # 10% to 30%
                job.current_step = f"Step 1/5: {msg}"
                save_job(job)

            media_info = download_youtube_media(youtube_url, job_id, progress_callback=dl_cb)
            job.video_title = media_info.get("title")
            job.video_author = media_info.get("author")
            job.video_thumbnail = media_info.get("thumbnail")
            job.original_duration = media_info.get("duration")
            job.progress = 30
            save_job(job)

            video_path = media_info["video_path"]
            audio_path = media_info["audio_path"]

            # ----------------------------------------------------
            # STEP 2: TRANSCRIPTION (faster-whisper)
            # ----------------------------------------------------
            job.status = JobStatus.TRANSCRIBING
            job.progress = 32
            job.current_step = "Step 2/5: Transcribing audio with faster-whisper (word-level timestamps)..."
            save_job(job)

            def trans_cb(pct: float, msg: str):
                job.progress = int(32 + (pct * 0.23))  # 32% to 55%
                job.current_step = f"Step 2/5: {msg}"
                save_job(job)

            transcript: TranscriptData = transcribe_audio(audio_path, job_id, progress_callback=trans_cb)
            job.progress = 55
            save_job(job)

            # ----------------------------------------------------
            # STEP 3: AI CLIP SELECTION & METADATA (Google Gemini 1.5 Flash)
            # ----------------------------------------------------
            job.status = JobStatus.ANALYZING
            job.progress = 58
            job.current_step = "Step 3/5: Prompting Gemini 1.5 Flash for high-CTR 30-60s clip segments..."
            save_job(job)

            clips = select_viral_clips(
                transcript=transcript,
                clip_count=clip_count,
                min_duration=min_duration,
                max_duration=max_duration
            )
            job.clips = clips
            job.progress = 70
            job.current_step = f"Step 3/5: AI identified {len(clips)} viral segments."
            save_job(job)

            # Collect all word timestamps for subtitle slicing
            all_words: List[TranscriptionWord] = []
            for seg in transcript.segments:
                all_words.extend(seg.words)

            # ----------------------------------------------------
            # STEP 4: VIDEO PROCESSING (FFmpeg 9:16 crop & dynamic .ass captions)
            # ----------------------------------------------------
            job.status = JobStatus.RENDERING
            job.progress = 72
            job.current_step = "Step 4/5: Cropping to 9:16 and burning dynamic subtitles with FFmpeg..."
            save_job(job)

            rendered_clips: List[ShortClipProposal] = []
            total_clips = max(1, len(clips))

            for idx, clip in enumerate(clips):
                step_start_pct = 72 + int((idx / total_clips) * 23)
                clip_step_pct = int(23 / total_clips)

                def render_cb(pct: float, msg: str):
                    job.progress = min(96, step_start_pct + int((pct / 100.0) * clip_step_pct))
                    job.current_step = f"Step 4/5 [Clip {idx+1}/{total_clips}]: {msg}"
                    save_job(job)

                clip.status = "rendering"
                save_job(job)

                try:
                    rendered_clip = process_and_render_short(
                        source_video_path=video_path,
                        clip=clip,
                        all_words=all_words,
                        job_id=job_id,
                        progress_callback=render_cb
                    )
                    rendered_clips.append(rendered_clip)
                except Exception as render_err:
                    logger.error(f"Failed to render clip {clip.id}: {render_err}")
                    clip.status = "failed"
                    clip.hook_reason = f"{clip.hook_reason} (Render notice: {str(render_err)})"
                    rendered_clips.append(clip)

            job.clips = rendered_clips
            job.progress = 98
            save_job(job)

            # ----------------------------------------------------
            # STEP 5: READY FOR REVIEW & ONE-CLICK PUBLISH
            # ----------------------------------------------------
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.current_step = "Completed: All Shorts ready for preview and YouTube publishing!"
            save_job(job)
            logger.info(f"Pipeline finished successfully for Job: {job_id}")

        except Exception as e:
            logger.exception(f"Pipeline error for Job {job_id}: {e}")
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.current_step = f"Pipeline failed: {str(e)}"
            save_job(job)

    @classmethod
    def publish_clip(
        cls,
        job_id: str,
        clip_id: str,
        title: str,
        description: str,
        tags: List[str],
        privacy_status: str = "private"
    ) -> Dict[str, any]:
        """
        Step 5 Execution: Uploads the selected rendered Short to YouTube.
        """
        job = get_job(job_id)
        if not job:
            raise ValueError(f"Job '{job_id}' not found.")

        target_clip = next((c for c in job.clips if c.id == clip_id), None)
        if not target_clip:
            raise ValueError(f"Clip '{clip_id}' not found in job '{job_id}'.")

        if not target_clip.rendered_filename:
            raise ValueError("Clip has not been rendered into MP4 yet.")

        video_file_path = str(settings.shorts_dir / target_clip.rendered_filename)

        result = upload_short_to_youtube(
            video_path=video_file_path,
            title=title or target_clip.title,
            description=description or target_clip.description,
            tags=tags or target_clip.tags,
            privacy_status=privacy_status
        )

        # Update clip with publishing metadata
        target_clip.published_youtube_id = result.get("youtube_video_id")
        target_clip.published_url = result.get("youtube_url")
        target_clip.status = "published"
        save_job(job)

        return result
