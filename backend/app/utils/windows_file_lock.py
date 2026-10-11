import os
import sys
import time
import logging

logger = logging.getLogger(__name__)

_orig_rename = os.rename
_orig_replace = os.replace


def robust_replace(src, dst, *args, **kwargs):
    """
    On Windows (especially in directories synced with OneDrive or scanned by antivirus/search indexing),
    files just written by FFmpeg or subprocesses may be temporarily locked with [WinError 32]
    ("The process cannot access the file because it is being used by another process")
    or [WinError 5] ("Access is denied").

    This helper retries replace/rename with backoff up to 20 seconds so background sync
    scanners have time to release their read lock.
    """
    max_retries = 35
    delay = 0.4
    for attempt in range(max_retries):
        try:
            return _orig_replace(src, dst, *args, **kwargs)
        except (PermissionError, OSError) as e:
            winerror = getattr(e, "winerror", None)
            is_lock = winerror in (32, 5) or isinstance(e, PermissionError)
            if is_lock and attempt < max_retries - 1:
                logger.warning(
                    f"[WinFileLock] Retrying file replace ({attempt + 1}/{max_retries}): "
                    f"'{src}' -> '{dst}' in {delay:.1f}s (Error: {e})"
                )
                time.sleep(delay)
                delay = min(1.5, delay * 1.1)
            else:
                logger.error(f"[WinFileLock] Final replace failure after {attempt + 1} retries: {e}")
                raise


def patch_os_rename():
    """Globally patches os.rename and os.replace on Windows to withstand OneDrive/Defender locks."""
    if sys.platform == "win32":
        os.rename = robust_replace
        os.replace = robust_replace
        logger.info("[WinFileLock] Global robust file rename/replace patch enabled for Windows & OneDrive.")
