import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from app.config import settings


def find_ffmpeg_executable() -> Optional[str]:
    """
    Locates the ffmpeg executable across user setting, PATH, and common Windows locations.
    """
    # 1. Check user configured setting
    if settings.FFMPEG_PATH and os.path.exists(settings.FFMPEG_PATH):
        return str(Path(settings.FFMPEG_PATH).resolve())

    # 2. Check system PATH
    found = shutil.which("ffmpeg")
    if found:
        return found

    # 3. Check common Windows paths
    candidates = [
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/ProgramData/chocolatey/bin/ffmpeg.exe"),
        Path(os.path.expanduser("~")) / "AppData/Local/Microsoft/WinGet/Packages",
        Path(os.path.expanduser("~")) / "scoop/shims/ffmpeg.exe",
    ]

    for cand in candidates:
        if cand.is_file() and cand.exists():
            return str(cand.resolve())
        if cand.is_dir():
            # Search winget packages subfolder
            for sub in cand.glob("**/ffmpeg.exe"):
                if sub.is_file():
                    return str(sub.resolve())

    return None


def find_ffprobe_executable() -> Optional[str]:
    """
    Locates the ffprobe executable.
    """
    if settings.FFPROBE_PATH and os.path.exists(settings.FFPROBE_PATH):
        return str(Path(settings.FFPROBE_PATH).resolve())

    found = shutil.which("ffprobe")
    if found:
        return found

    ffmpeg_path = find_ffmpeg_executable()
    if ffmpeg_path:
        probe_cand = Path(ffmpeg_path).parent / "ffprobe.exe"
        if probe_cand.exists():
            return str(probe_cand.resolve())

    return None


def check_ffmpeg_available() -> Tuple[bool, str]:
    """
    Verifies ffmpeg is accessible and executable.
    Returns (is_available, details_message)
    """
    ffmpeg_bin = find_ffmpeg_executable()
    if not ffmpeg_bin:
        return (
            False,
            "FFmpeg executable was not found. Please install FFmpeg (e.g., run `winget install Gyan.FFmpeg`) "
            "or specify FFMPEG_PATH in backend/.env."
        )

    try:
        res = subprocess.run([ffmpeg_bin, "-version"], capture_output=True, text=True, check=False)
        if res.returncode == 0:
            first_line = res.stdout.splitlines()[0] if res.stdout else "FFmpeg ready"
            return (True, f"Found FFmpeg at '{ffmpeg_bin}': {first_line}")
        else:
            return (False, f"FFmpeg at '{ffmpeg_bin}' returned error code {res.returncode}")
    except Exception as e:
        return (False, f"Failed to execute FFmpeg at '{ffmpeg_bin}': {str(e)}")
