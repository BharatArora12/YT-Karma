import json
from pathlib import Path
from typing import Optional, Callable
from faster_whisper import WhisperModel
from app.config import settings
from app.models.schemas import TranscriptData, TranscriptionSegment, TranscriptionWord

# Global cached Whisper model instance
_whisper_model_instance = None


def get_whisper_model() -> WhisperModel:
    """Returns a singleton WhisperModel instance with configured device and model size."""
    global _whisper_model_instance
    if _whisper_model_instance is None:
        model_size = settings.WHISPER_MODEL_SIZE or "base"
        device = settings.WHISPER_DEVICE or "cpu"
        compute_type = settings.WHISPER_COMPUTE_TYPE or "int8"
        _whisper_model_instance = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )
    return _whisper_model_instance


def transcribe_audio(
    audio_path: str,
    job_id: str,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> TranscriptData:
    """
    Transcribes the audio file using faster-whisper and generates
    detailed word-level timestamps. Caches results to JSON.
    """
    transcript_cache_file = settings.transcripts_dir / f"{job_id}.json"
    if transcript_cache_file.exists():
        try:
            with open(transcript_cache_file, "r", encoding="utf-8") as f:
                cached_dict = json.load(f)
                return TranscriptData(**cached_dict)
        except Exception:
            pass  # Recompute if cache is corrupted

    if progress_callback:
        progress_callback(10.0, "Loading Whisper transcription model...")

    model = get_whisper_model()

    if progress_callback:
        progress_callback(25.0, "Transcribing audio with word-level timestamps...")

    segments, info = model.transcribe(
        audio_path,
        language="hi",
        beam_size=5,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    all_segments: list[TranscriptionSegment] = []
    full_text_parts: list[str] = []

    seg_idx = 0
    for segment in segments:
        seg_idx += 1
        word_models: list[TranscriptionWord] = []
        if segment.words:
            for w in segment.words:
                word_models.append(
                    TranscriptionWord(
                        word=w.word.strip(),
                        start=round(w.start, 2),
                        end=round(w.end, 2),
                        probability=round(w.probability, 3)
                    )
                )

        clean_seg_text = segment.text.strip()
        full_text_parts.append(clean_seg_text)

        all_segments.append(
            TranscriptionSegment(
                id=seg_idx,
                start=round(segment.start, 2),
                end=round(segment.end, 2),
                text=clean_seg_text,
                words=word_models
            )
        )

        if progress_callback and info.duration and info.duration > 0:
            est_pct = min(90.0, 25.0 + (segment.end / info.duration) * 65.0)
            progress_callback(est_pct, f"Transcribing ({segment.end:.0f}s / {info.duration:.0f}s)...")

    transcript_data = TranscriptData(
        language=info.language if hasattr(info, "language") and info.language else "hi",
        duration=round(info.duration, 2) if hasattr(info, "duration") else 0.0,
        text=" ".join(full_text_parts),
        segments=all_segments
    )

    # Cache transcript to disk
    with open(transcript_cache_file, "w", encoding="utf-8") as f:
        json.dump(transcript_data.model_dump(), f, indent=2, ensure_ascii=False)

    if progress_callback:
        progress_callback(100.0, f"Transcription completed. Found {len(all_segments)} segments.")

    return transcript_data
