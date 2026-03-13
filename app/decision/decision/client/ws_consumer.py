"""WebSocket client that connects to botrunner and feeds game states to strategy."""

import asyncio
import json
import logging

import websockets

from ..config import settings
from ..models.game_state import GameState

logger = logging.getLogger(__name__)


class BotrunnerConsumer:
    """Connects to botrunner WebSocket and yields GameState objects."""

    def __init__(self, on_state):
        self._on_state = on_state
        self._running = False
        self._task: asyncio.Task | None = None
        self._connected = False
        self._backoff = 1.0

    @property
    def ws_url(self) -> str:
        return (
            f"ws://{settings.botrunner_host}:{settings.botrunner_port}"
            f"/state/stream?only_hero_turn=true"
        )

    @property
    def connected(self) -> bool:
        return self._connected

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._consume_loop())
        logger.info(f"Consumer started, connecting to {self.ws_url}")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._connected = False
        logger.info("Consumer stopped")

    async def _consume_loop(self):
        while self._running:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self._connected = True
                    self._backoff = 1.0
                    logger.info("Connected to botrunner WebSocket")
                    async for message in ws:
                        if not self._running:
                            break
                        try:
                            data = json.loads(message)
                        except json.JSONDecodeError:
                            continue
                        if "heartbeat" in data:
                            continue
                        try:
                            state = GameState(**data)
                        except Exception as e:
                            logger.warning(f"Failed to parse GameState: {e}")
                            continue
                        if not state.is_hero_turn:
                            continue
                        await self._on_state(state)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._connected = False
                logger.warning(f"WebSocket disconnected: {e}. Reconnecting in {self._backoff}s")
                await asyncio.sleep(self._backoff)
                self._backoff = min(self._backoff * 2, 30.0)
