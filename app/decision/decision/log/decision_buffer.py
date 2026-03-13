"""Ring buffer for recent decisions (mirrors botrunner's state_buffer)."""

import threading
from collections import deque

from ..models.decision import Decision


class DecisionBuffer:
    def __init__(self, max_history: int = 200):
        self._latest: Decision | None = None
        self._history: deque[Decision] = deque(maxlen=max_history)
        self._lock = threading.Lock()

    def update(self, decision: Decision):
        with self._lock:
            self._latest = decision
            self._history.append(decision)

    def get_latest(self) -> Decision | None:
        with self._lock:
            return self._latest

    def get_history(self, limit: int = 20) -> list[Decision]:
        with self._lock:
            items = list(self._history)
        return items[-limit:]


decision_buffer = DecisionBuffer()
