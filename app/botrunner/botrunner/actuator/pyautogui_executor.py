"""PyAutoGUI executor — works on any macOS window (desktop app, iOS simulator)."""

import asyncio
import logging

from .base import ClickExecutor

logger = logging.getLogger(__name__)

try:
    import pyautogui
    pyautogui.FAILSAFE = True  # move mouse to corner to abort
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


class PyAutoGUIExecutor(ClickExecutor):
    name = "pyautogui"

    async def tap(self, x: int, y: int) -> bool:
        if not _AVAILABLE:
            logger.error("pyautogui not installed")
            return False
        try:
            await asyncio.to_thread(pyautogui.click, x, y)
            logger.info(f"pyautogui tap at ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"pyautogui tap failed: {e}")
            return False

    async def drag(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        if not _AVAILABLE:
            return False
        try:
            def _drag():
                pyautogui.moveTo(x1, y1)
                pyautogui.drag(x2 - x1, y2 - y1, duration=duration_ms / 1000.0)
            await asyncio.to_thread(_drag)
            logger.info(f"pyautogui drag ({x1},{y1}) → ({x2},{y2})")
            return True
        except Exception as e:
            logger.error(f"pyautogui drag failed: {e}")
            return False

    async def health_check(self) -> bool:
        return _AVAILABLE
