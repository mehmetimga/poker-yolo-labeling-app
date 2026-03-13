"""Thread-safe buffer for the latest DetectionMap."""

import threading

from ..models.actuator_models import DetectionMap


class DetectionMapBuffer:
    def __init__(self):
        self._latest: DetectionMap | None = None
        self._lock = threading.Lock()

    def update(self, detection_map: DetectionMap):
        with self._lock:
            self._latest = detection_map

    def get_latest(self) -> DetectionMap | None:
        with self._lock:
            return self._latest


detection_map_buffer = DetectionMapBuffer()
