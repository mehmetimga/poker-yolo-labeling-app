"""Strategy layer protocol."""

from typing import Protocol

from ..models.decision import Decision, HandStrength
from ..models.game_state import GameState


class StrategyLayer(Protocol):
    def decide(
        self, game_state: GameState, hand_strength: HandStrength
    ) -> Decision | None:
        """Return a Decision, or None to defer to the next layer."""
        ...
