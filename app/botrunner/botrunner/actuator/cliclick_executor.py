"""cliclick executor — fast macOS native CLI mouse control."""

import asyncio
import logging
import shutil
import subprocess

from .base import ClickExecutor

logger = logging.getLogger(__name__)


class CliClickExecutor(ClickExecutor):
    name = "cliclick"

    async def tap(self, x: int, y: int) -> bool:
        try:
            await asyncio.to_thread(
                subprocess.run,
                ["cliclick", f"c:{x},{y}"],
                capture_output=True, timeout=3,
            )
            logger.info(f"cliclick tap at ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"cliclick tap failed: {e}")
            return False

    async def drag(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        try:
            await asyncio.to_thread(
                subprocess.run,
                ["cliclick", f"dd:{x1},{y1}", f"du:{x2},{y2}"],
                capture_output=True, timeout=5,
            )
            logger.info(f"cliclick drag ({x1},{y1}) → ({x2},{y2})")
            return True
        except Exception as e:
            logger.error(f"cliclick drag failed: {e}")
            return False

    async def health_check(self) -> bool:
        return shutil.which("cliclick") is not None
