import logging
from collections import deque

from PIL import Image

try:
    import imagehash
    _IMAGEHASH_AVAILABLE = True
except ImportError:
    _IMAGEHASH_AVAILABLE = False

logger = logging.getLogger(__name__)


class FrameDedup:
    """Skip near-duplicate frames using perceptual hashing."""

    def __init__(self, threshold: int = 8, buffer_size: int = 5):
        self.threshold = threshold
        self._recent_hashes: deque = deque(maxlen=buffer_size)

    def is_duplicate(self, pil_image: Image.Image) -> bool:
        """Return True if this frame is too similar to recent frames."""
        if not _IMAGEHASH_AVAILABLE:
            return False

        current_hash = imagehash.phash(pil_image)

        for prev_hash in self._recent_hashes:
            distance = current_hash - prev_hash
            if distance < self.threshold:
                return True

        self._recent_hashes.append(current_hash)
        return False

    def reset(self):
        self._recent_hashes.clear()
