import asyncio
import threading
from collections import deque

from ..models.game_state_models import GameState


class StateBuffer:
    """Thread-safe buffer holding latest game state and a ring history."""

    def __init__(self, max_history: int = 100):
        self._latest: GameState | None = None
        self._history: deque[GameState] = deque(maxlen=max_history)
        self._lock = threading.Lock()
        self._subscribers: list[asyncio.Queue] = []
        self._sub_lock = threading.Lock()

    def update(self, state: GameState):
        with self._lock:
            self._latest = state
            self._history.append(state)
        # Broadcast to WebSocket subscribers
        with self._sub_lock:
            for q in self._subscribers:
                try:
                    q.put_nowait(state)
                except asyncio.QueueFull:
                    pass  # Drop if subscriber is slow

    def get_latest(self) -> GameState | None:
        with self._lock:
            return self._latest

    def get_history(self, limit: int = 10) -> list[GameState]:
        with self._lock:
            items = list(self._history)
        return items[-limit:]

    def add_subscriber(self, queue: asyncio.Queue):
        with self._sub_lock:
            self._subscribers.append(queue)

    def remove_subscriber(self, queue: asyncio.Queue):
        with self._sub_lock:
            self._subscribers = [q for q in self._subscribers if q is not queue]

    def clear(self):
        with self._lock:
            self._latest = None
            self._history.clear()


state_buffer = StateBuffer()
