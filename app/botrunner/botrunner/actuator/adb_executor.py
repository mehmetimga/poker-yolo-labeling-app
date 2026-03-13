"""ADB executor — Android emulator taps with density multiplier."""

import asyncio
import logging
import shutil
import subprocess

from ..config import settings
from .base import ClickExecutor

logger = logging.getLogger(__name__)


class ADBExecutor(ClickExecutor):
    name = "adb"

    def __init__(self):
        self._density_multiplier: float | None = None

    def _adb_cmd(self) -> list[str]:
        cmd = ["adb"]
        if settings.adb_device:
            cmd.extend(["-s", settings.adb_device])
        return cmd

    async def _get_density_multiplier(self) -> float:
        """Auto-detect density multiplier from emulator, fallback to config."""
        if self._density_multiplier is not None:
            return self._density_multiplier

        try:
            result = await asyncio.to_thread(
                subprocess.run,
                self._adb_cmd() + ["shell", "wm", "density"],
                capture_output=True, text=True, timeout=3,
            )
            # Output: "Physical density: 480"
            for line in result.stdout.strip().split("\n"):
                if "density" in line.lower():
                    density = int(line.split(":")[-1].strip())
                    self._density_multiplier = density / 160.0
                    logger.info(f"ADB density: {density} → multiplier: {self._density_multiplier}")
                    return self._density_multiplier
        except Exception as e:
            logger.warning(f"Failed to detect ADB density: {e}")

        self._density_multiplier = settings.adb_density_multiplier
        logger.info(f"Using config density multiplier: {self._density_multiplier}")
        return self._density_multiplier

    async def tap(self, x: int, y: int) -> bool:
        multiplier = await self._get_density_multiplier()
        pixel_x = round(x * multiplier)
        pixel_y = round(y * multiplier)

        try:
            cmd = self._adb_cmd() + ["shell", "input", "tap", str(pixel_x), str(pixel_y)]
            await asyncio.to_thread(
                subprocess.run, cmd,
                capture_output=True, timeout=5,
            )
            logger.info(f"adb tap at logical ({x},{y}) → pixel ({pixel_x},{pixel_y})")
            return True
        except Exception as e:
            logger.error(f"adb tap failed: {e}")
            return False

    async def drag(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        multiplier = await self._get_density_multiplier()
        px1, py1 = round(x1 * multiplier), round(y1 * multiplier)
        px2, py2 = round(x2 * multiplier), round(y2 * multiplier)

        try:
            cmd = self._adb_cmd() + [
                "shell", "input", "swipe",
                str(px1), str(py1), str(px2), str(py2), str(duration_ms),
            ]
            await asyncio.to_thread(
                subprocess.run, cmd,
                capture_output=True, timeout=10,
            )
            logger.info(f"adb swipe ({px1},{py1}) → ({px2},{py2}) {duration_ms}ms")
            return True
        except Exception as e:
            logger.error(f"adb swipe failed: {e}")
            return False

    async def health_check(self) -> bool:
        if not shutil.which("adb"):
            return False
        try:
            result = await asyncio.to_thread(
                subprocess.run,
                self._adb_cmd() + ["devices"],
                capture_output=True, text=True, timeout=3,
            )
            return "device" in result.stdout
        except Exception:
            return False
