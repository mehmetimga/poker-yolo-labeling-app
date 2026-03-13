"""AppleScript executor — zero-dependency macOS fallback."""

import asyncio
import logging
import subprocess

from .base import ClickExecutor

logger = logging.getLogger(__name__)


class AppleScriptExecutor(ClickExecutor):
    name = "applescript"

    async def tap(self, x: int, y: int) -> bool:
        script = f'tell application "System Events" to click at {{{x}, {y}}}'
        try:
            await asyncio.to_thread(
                subprocess.run,
                ["osascript", "-e", script],
                capture_output=True, timeout=3,
            )
            logger.info(f"applescript tap at ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"applescript tap failed: {e}")
            return False

    async def drag(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        # AppleScript doesn't support drag natively — fall back to basic click at target
        logger.warning("AppleScript drag not supported, tapping target instead")
        return await self.tap(x2, y2)

    async def health_check(self) -> bool:
        return True  # Always available on macOS
