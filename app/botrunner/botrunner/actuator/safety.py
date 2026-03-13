"""Safety checks: delay, rate limit, dry-run, kill switch."""

import asyncio
import logging
import random
import time
from collections import deque

from ..config import settings

logger = logging.getLogger(__name__)


class ActuatorSafety:
    def __init__(self):
        self._kill_switch = False
        self._action_timestamps: deque[float] = deque(maxlen=100)

    @property
    def is_killed(self) -> bool:
        return self._kill_switch

    def kill(self):
        self._kill_switch = True
        logger.warning("KILL SWITCH ACTIVATED — all automation stopped")

    def reset_kill(self):
        self._kill_switch = False
        logger.info("Kill switch reset")

    async def check_and_delay(self) -> str | None:
        """Run all safety checks. Returns error message or None if safe to proceed."""
        if not settings.actuator_enabled:
            return "actuator_disabled"

        if self._kill_switch:
            return "kill_switch_active"

        if settings.actuator_dry_run:
            return "dry_run"

        # Rate limit
        now = time.time()
        cutoff = now - 60.0
        recent = [t for t in self._action_timestamps if t > cutoff]
        if len(recent) >= settings.actuator_max_actions_per_minute:
            return "rate_limited"

        # Random delay (human-like timing)
        delay_ms = random.randint(
            settings.actuator_min_delay_ms,
            settings.actuator_max_delay_ms,
        )
        logger.debug(f"Safety delay: {delay_ms}ms")
        await asyncio.sleep(delay_ms / 1000.0)

        self._action_timestamps.append(time.time())
        return None


actuator_safety = ActuatorSafety()
