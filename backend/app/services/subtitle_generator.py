from pathlib import Path
from typing import List
from app.models.schemas import TranscriptionWord


def format_ass_time(seconds: float) -> str:
    """Converts seconds into ASS timestamp format: H:MM:SS.cs"""
    if seconds < 0:
        seconds = 0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        centis = 99
    return f"{hrs}:{mins:02d}:{secs:02d}.{centis:02d}"


def generate_ass_subtitles(
    words: List[TranscriptionWord],
    clip_start_time: float,
    clip_end_time: float,
    output_path: Path,
    words_per_batch: int = 4
) -> Path:
    """
    Generates dynamic modern .ass subtitles (Hormozi / MrBeast style)
    with highlighted active words for the specified clip window.
    """
    # 1. Filter words that fall inside [clip_start_time, clip_end_time]
    clip_words = []
    for w in words:
        if w.end >= clip_start_time and w.start <= clip_end_time:
            # Adjust word start/end to be relative to clip_start_time
            rel_start = max(0.0, w.start - clip_start_time)
            rel_end = min(clip_end_time - clip_start_time, w.end - clip_start_time)
            clean_word = w.word.strip().upper()
            if clean_word:
                clip_words.append({
                    "word": clean_word,
                    "start": rel_start,
                    "end": rel_end
                })

    ass_header = """[Script Info]
Title: Dynamic YT Shorts Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Nirmala UI,64,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,1,0,1,4.5,2.0,2,80,80,360,1
Style: Highlight,Nirmala UI,68,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,110,110,1,0,1,5.0,2.5,2,80,80,360,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = []

    # Batch words into punchy short phrases (3-4 words max)
    i = 0
    n = len(clip_words)
    while i < n:
        batch = clip_words[i : min(i + words_per_batch, n)]
        i += len(batch)

        batch_start = batch[0]["start"]
        batch_end = batch[-1]["end"]
        if batch_end <= batch_start:
            batch_end = batch_start + 0.5

        # Within the batch, emit a dialogue event per word highlight
        for idx, active_word in enumerate(batch):
            w_start = active_word["start"]
            # Active duration lasts until next word or batch end
            if idx < len(batch) - 1:
                w_end = batch[idx + 1]["start"]
            else:
                w_end = active_word["end"]

            if w_end <= w_start:
                w_end = w_start + 0.25

            # Build line text: active word highlighted in Yellow with scale bump
            styled_words = []
            for j, bw in enumerate(batch):
                if j == idx:
                    # Glowing yellow & larger font
                    styled_words.append(r"{\c&H0000FFFF&\t(0,100,\fscx112\fscy112)}" + bw["word"] + r"{\r}")
                else:
                    # Crisp white with dark outline
                    styled_words.append(r"{\c&H00FFFFFF&}" + bw["word"])

            full_line_text = " ".join(styled_words)
            dialogue_lines.append(
                f"Dialogue: 0,{format_ass_time(w_start)},{format_ass_time(w_end)},Default,,0,0,0,,{full_line_text}"
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ass_header)
        f.write("\n".join(dialogue_lines))
        f.write("\n")

    return output_path
