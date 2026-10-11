import logging
import subprocess
from pathlib import Path
from typing import List, Optional, Callable
from app.config import settings
from app.models.schemas import ShortClipProposal, TranscriptionWord
from app.services.subtitle_generator import generate_ass_subtitles
from app.utils.ffmpeg_checker import find_ffmpeg_executable

logger = logging.getLogger(__name__)


def format_ass_filter_path(subtitle_path: str | Path) -> str:
    """
    Formats the .ass subtitle file path safely for FFmpeg filter syntax on Windows and POSIX.
    Escapes drive colons (e.g., C\\:) and handles paths with spaces by wrapping in single quotes.
    """
    path_obj = Path(subtitle_path).resolve()
    posix_path = path_obj.as_posix().replace(":", r"\:")
    return f"'{posix_path}'"


def render_short(input_video, start_time, end_time, ass_subtitle_file, output_mp4):
    """
    Clips actual video footage and original audio from the downloaded YouTube video.
    Executes fast hardware seeking, center-crops to 9:16 aspect ratio, burns .ass subtitles,
    and renders with universal libx264/aac codecs and +faststart flag.
    """
    ffmpeg_bin = find_ffmpeg_executable() or "ffmpeg"
    formatted_sub_path = format_ass_filter_path(ass_subtitle_file)

    command = [
        ffmpeg_bin,
        "-y",                                                 # Overwrite if exists
        "-ss", str(start_time),                               # Fast seek to start
        "-to", str(end_time),                                 # End point
        "-i", str(input_video),                               # The actual downloaded YouTube video
        "-vf", f"crop=ih*(9/16):ih,ass={formatted_sub_path}", # Crop to 9:16 and burn subtitles
        "-c:v", "libx264",                                    # Universal H.264 video codec
        "-preset", "fast",                                    # Faster rendering speed
        "-c:a", "aac",                                        # Universal AAC audio codec
        "-b:a", "192k",                                       # Standard audio bitrate
        "-movflags", "+faststart",                            # Fixes web playback and corrupted downloads
        str(output_mp4)
    ]

    logger.info(f"Executing render_short FFmpeg command:\n{' '.join(command)}")
    subprocess.run(command, check=True)


def process_and_render_short(
    source_video_path: str,
    clip: ShortClipProposal,
    all_words: List[TranscriptionWord],
    job_id: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> ShortClipProposal:
    """
    Renders a vertical 9:16 Short with dynamic burned-in .ass subtitles
    from the original downloaded YouTube video footage and audio.
    Step 4 of the pipeline.
    """
    ffmpeg_bin = find_ffmpeg_executable() or "ffmpeg"

    # 1. Output file destinations
    output_filename = f"{job_id}_{clip.id}.mp4"
    output_video_path = settings.shorts_dir / output_filename
    subtitle_filename = f"{job_id}_{clip.id}.ass"
    subtitle_path = settings.subtitles_dir / subtitle_filename

    if progress_callback:
        progress_callback(15.0, f"Generating dynamic captions for clip '{clip.title[:20]}...'")

    # 2. Generate .ass subtitle file with word highlight tags
    generate_ass_subtitles(
        words=all_words,
        clip_start_time=clip.start_time,
        clip_end_time=clip.end_time,
        output_path=subtitle_path,
        words_per_batch=3
    )

    if progress_callback:
        progress_callback(40.0, "Trimming original footage, center-cropping to 9:16, and burning subtitles...")

    # 3. Render short using FFmpeg subprocess trimming, cropping, and subtitle burning
    try:
        render_short(
            input_video=source_video_path,
            start_time=clip.start_time,
            end_time=clip.end_time,
            ass_subtitle_file=subtitle_path,
            output_mp4=output_video_path
        )
    except subprocess.CalledProcessError as e:
        logger.warning(f"Initial render with ass subtitles failed: {e}. Attempting fallback without subtitles...")
        # Fallback crop without subtitle burning if fontconfig or libass encountered an issue
        fallback_cmd = [
            ffmpeg_bin,
            "-y",
            "-ss", str(clip.start_time),
            "-to", str(clip.end_time),
            "-i", str(source_video_path),
            "-vf", "crop=ih*(9/16):ih",
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_video_path)
        ]
        subprocess.run(fallback_cmd, check=True)

    if progress_callback:
        progress_callback(100.0, "Short rendered successfully.")

    # Update clip proposal with rendered details
    clip.rendered_filename = output_filename
    clip.rendered_video_url = f"/api/media/shorts/{output_filename}"
    clip.subtitle_filename = subtitle_filename
    clip.status = "ready"
    return clip
