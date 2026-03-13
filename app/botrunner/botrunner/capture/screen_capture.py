import logging
import subprocess
import re
import time

import numpy as np
from PIL import Image

try:
    import mss
    _MSS_AVAILABLE = True
except ImportError:
    _MSS_AVAILABLE = False

logger = logging.getLogger(__name__)

_cached_bounds: dict | None = None
_bounds_fetched_at: float = 0.0
_BOUNDS_CACHE_SECONDS = 5.0


def get_window_bounds(window_title: str) -> dict | None:
    """Get the bounds of a macOS window by title using osascript."""
    global _cached_bounds, _bounds_fetched_at

    now = time.time()
    if _cached_bounds and (now - _bounds_fetched_at) < _BOUNDS_CACHE_SECONDS:
        return _cached_bounds

    script = f'''
    tell application "System Events"
        set targetWindow to missing value
        repeat with proc in (every process whose background only is false)
            repeat with w in (every window of proc)
                if name of w contains "{window_title}" then
                    set targetWindow to w
                    exit repeat
                end if
            end repeat
            if targetWindow is not missing value then exit repeat
        end repeat
        if targetWindow is missing value then
            return "NOT_FOUND"
        else
            set pos to position of targetWindow
            set sz to size of targetWindow
            return (item 1 of pos as text) & "," & (item 2 of pos as text) & "," & (item 1 of sz as text) & "," & (item 2 of sz as text)
        end if
    end tell
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=3
        )
        output = result.stdout.strip()
        if output == "NOT_FOUND" or not output:
            logger.warning(f"Window '{window_title}' not found")
            return None

        parts = output.split(",")
        if len(parts) != 4:
            return None

        bounds = {
            "left": int(parts[0].strip()),
            "top": int(parts[1].strip()),
            "width": int(parts[2].strip()),
            "height": int(parts[3].strip()),
        }
        _cached_bounds = bounds
        _bounds_fetched_at = now
        return bounds
    except (subprocess.TimeoutExpired, Exception) as e:
        logger.error(f"Failed to get window bounds: {e}")
        return None


def capture_screen(window_title: str, region_override: str | None = None) -> tuple[np.ndarray, Image.Image] | None:
    """Capture a screenshot. Returns (numpy_array, pil_image) or None on failure."""
    if not _MSS_AVAILABLE:
        logger.error("mss is not installed")
        return None

    if region_override:
        parts = [int(x) for x in region_override.split(",")]
        monitor = {"left": parts[0], "top": parts[1], "width": parts[2], "height": parts[3]}
    else:
        bounds = get_window_bounds(window_title)
        if not bounds:
            return None
        monitor = bounds

    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
        np_array = np.array(img)
        return np_array, img
