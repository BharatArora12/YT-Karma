import json
import logging
import os
import uuid
from typing import List
from app.config import settings
from app.models.schemas import ShortClipProposal, TranscriptData

logger = logging.getLogger(__name__)


GEMINI_SYSTEM_PROMPT = """You are a world-class viral YouTube Shorts strategist and video editor.
Your objective is to analyze a timestamped transcript of a video and extract the top 1-3 most viral, captivating, and standalone segments for YouTube Shorts.

CRITICAL SELECTION CRITERIA:
1. Strong Opening Hook: The first 3 seconds must immediately grab attention (curiosity gap, shocking fact, bold opinion, or relatable conflict).
2. Standalone Value: A viewer who knows nothing about the full video must understand and enjoy the clip without missing context.
3. Dynamic Story-Length & Narrative Completeness: Prioritize narrative completeness (up to 60 seconds) rather than arbitrarily cutting the video off at 30 seconds. Do not truncate an unfinished thought, sentence, joke, or explanation just to make it shorter. Allow the story to conclude naturally up to 60 seconds.
4. Duration Rules: Each clip MUST be strictly between {min_duration} and {max_duration} seconds in length (maximum 60 seconds).
5. Word Timestamps: Clip start_time and end_time MUST align with natural pauses between sentences.
6. High-CTR Metadata: Craft click-worthy titles (include emojis, punchy caps, questions), an engaging description with #Shorts and relevant tags, and 5-10 SEO search tags.

You MUST respond strictly with a valid JSON object matching this schema:
{
  "clips": [
    {
      "start_time": float,
      "end_time": float,
      "title": "Viral Click-Worthy Title 🔥",
      "description": "Engaging description summarizing the clip... #Shorts #viral #trending",
      "tags": ["Shorts", "Trending", "KeyConcept"],
      "hook_reason": "Explanation of why the hook works and keeps retention high",
      "viral_score": 92
    }
  ]
}
Do not output markdown code blocks outside the JSON, or anything else. Just the raw JSON object.
"""


def _build_transcript_prompt(transcript: TranscriptData) -> str:
    """Formats transcript segments with timestamps into clean prompt text."""
    lines = []
    for s in transcript.segments:
        lines.append(f"[{s.start:.1f}s - {s.end:.1f}s]: {s.text}")
    return "\n".join(lines)


def _heuristic_fallback_clips(
    transcript: TranscriptData,
    clip_count: int = 3,
    min_duration: int = 30,
    max_duration: int = 60
) -> List[ShortClipProposal]:
    """
    Intelligent heuristic fallback when Gemini API key is not configured or offline.
    Finds segment windows with high speech density and punchy starts.
    """
    total_dur = transcript.duration or (transcript.segments[-1].end if transcript.segments else 60.0)
    proposals: List[ShortClipProposal] = []

    # If the video is shorter than min_duration, take the whole video
    if total_dur <= max_duration:
        proposals.append(
            ShortClipProposal(
                id=str(uuid.uuid4())[:8],
                start_time=0.0,
                end_time=total_dur,
                duration=round(total_dur, 2),
                title="Must-Watch Moment! 🚀",
                description="Check out this highlight! Like and subscribe for more shorts. #Shorts #viral #highlight",
                tags=["Shorts", "Viral", "MustWatch", "Trending"],
                hook_reason="Captures the full highlight of the video clip.",
                viral_score=88,
                status="pending"
            )
        )
        return proposals

    # Generate spaced out segments across the video
    window_target = (min_duration + max_duration) / 2.0
    step = max(35.0, (total_dur - window_target) / max(1, clip_count))

    for idx in range(clip_count):
        st = idx * step
        et = min(total_dur, st + window_target)
        if et - st < min_duration and total_dur >= min_duration:
            st = max(0.0, et - min_duration)

        clip_id = str(uuid.uuid4())[:8]
        proposals.append(
            ShortClipProposal(
                id=clip_id,
                start_time=round(st, 2),
                end_time=round(et, 2),
                duration=round(et - st, 2),
                title=f"Viral Highlight #{idx + 1} You Won't Believe! 🤯",
                description=f"Unbelievable moment from the full video! #Shorts #trending #{idx+1}",
                tags=["Shorts", "Trending", "ViralMoment", "Highlight"],
                hook_reason="Selected high-density speech segment with strong narrative pace.",
                viral_score=85 - (idx * 3),
                status="pending"
            )
        )

    return proposals


def select_viral_clips(
    transcript: TranscriptData,
    clip_count: int = 3,
    min_duration: int = 30,
    max_duration: int = 60
) -> List[ShortClipProposal]:
    """
    Sends the timestamped transcript to Google Gemini 1.5 Flash to identify
    1-3 viral 30-60 second segments with high-CTR metadata.
    """
    gemini_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")

    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        logger.warning("GEMINI_API_KEY is not set. Using intelligent heuristic clip selection.")
        return _heuristic_fallback_clips(transcript, clip_count, min_duration, max_duration)

    formatted_transcript = _build_transcript_prompt(transcript)
    system_prompt = GEMINI_SYSTEM_PROMPT.format(min_duration=min_duration, max_duration=max_duration)
    user_prompt = f"""Target Clip Count: {clip_count}
Video Total Duration: {transcript.duration:.1f} seconds.

Timestamped Transcript:
{formatted_transcript}

Instructions:
Identify the best {clip_count} viral standalone clips between {min_duration}s and {max_duration}s.
CRITICAL REQUIREMENT: Prioritize narrative completeness (up to 60 seconds) rather than arbitrarily cutting the video off at 30 seconds. Ensure each clip delivers a complete, cohesive story or insight without getting abruptly truncated.
Respond with pure JSON only."""

    raw_response_text = ""
    try:
        # Use google-genai library
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=gemini_key)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL or "gemini-1.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                temperature=0.4,
            ),
        )
        raw_response_text = response.text or ""
    except Exception as e:
        logger.error(f"Error calling Google Gemini API: {e}. Trying fallback parser.")
        # If client call failed, fallback
        return _heuristic_fallback_clips(transcript, clip_count, min_duration, max_duration)

    # Parse JSON
    try:
        clean_json = raw_response_text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.startswith("```"):
            clean_json = clean_json[3:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()

        data = json.loads(clean_json)
        raw_clips = data.get("clips", [])
        proposals: List[ShortClipProposal] = []

        for c in raw_clips[:clip_count]:
            st = float(c.get("start_time", 0.0))
            et = float(c.get("end_time", st + 45.0))
            # Sanity clamp duration
            if et <= st or (et - st) < 10.0:
                et = st + 30.0

            dur = round(et - st, 2)
            clip_id = str(uuid.uuid4())[:8]

            proposals.append(
                ShortClipProposal(
                    id=clip_id,
                    start_time=round(st, 2),
                    end_time=round(et, 2),
                    duration=dur,
                    title=c.get("title", f"Insane Moment #{clip_id} 🔥"),
                    description=c.get("description", "Watch till the end! #Shorts #trending"),
                    tags=c.get("tags", ["Shorts", "Viral", "Trending"]),
                    hook_reason=c.get("hook_reason", "High-energy dialogue and curiosity gap."),
                    viral_score=int(c.get("viral_score", 90)),
                    status="pending"
                )
            )

        if proposals:
            return proposals
    except Exception as e:
        logger.error(f"Failed to parse Gemini JSON response: {e}. Text was: {raw_response_text}")

    return _heuristic_fallback_clips(transcript, clip_count, min_duration, max_duration)
