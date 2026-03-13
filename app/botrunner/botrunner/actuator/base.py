"""Abstract base for click executors (adapter pattern)."""

from abc import ABC, abstractmethod


class ClickExecutor(ABC):
    """All click methods implement this interface.
    Swap methods by changing BOT_ACTUATOR_METHOD config."""

    name: str = "base"

    @abstractmethod
    async def tap(self, x: int, y: int) -> bool:
        """Tap at screen coordinates. Returns True on success."""
        ...

    @abstractmethod
    async def drag(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        """Drag from (x1,y1) to (x2,y2). Returns True on success."""
        ...

    async def health_check(self) -> bool:
        """Verify this executor method is available and working."""
        return True
