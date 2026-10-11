import subprocess
from pathlib import Path

ass_text = """[Script Info]
Title: Hindi Subtitle Test
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Nirmala UI,64,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,1,0,0,0,100,100,1,0,1,4.5,2.0,2,80,80,360,1
Style: Highlight,Nirmala UI,68,&H0000FFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,110,110,1,0,1,5.0,2.5,2,80,80,360,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,यह एक बहुत ही रोमांचक कहानी है
"""

p = Path("test_hindi.ass")
p.write_text(ass_text, encoding="utf-8")

subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc=duration=2:size=1920x1080:rate=30", "-f", "lavfi", "-i", "sine=frequency=1000:duration=2", "-c:v", "libx264", "-c:a", "aac", "test_in.mp4"], check=True, capture_output=True)

sub_arg = str(p.resolve().as_posix()).replace(":", r"\:")
cmd = [
    "ffmpeg", "-y",
    "-ss", "0", "-to", "2",
    "-i", "test_in.mp4",
    "-vf", f"crop=ih*(9/16):ih,ass='{sub_arg}'",
    "-c:v", "libx264", "-preset", "fast",
    "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart",
    "test_hindi_out.mp4"
]
res = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
if res.returncode != 0:
    print("Stderr:", res.stderr[-300:])
else:
    print("HINDI SUBTITLES RENDERED SUCCESSFULLY WITH NIRMALA UI!")
