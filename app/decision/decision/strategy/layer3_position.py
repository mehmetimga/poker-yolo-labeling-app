"""Layer 3: Position-aware adjustments (stub for future implementation)."""

from ..models.decision import Decision, HandStrength
from ..models.game_state import GameState


class PositionStrategy:
    """Adjust preflop ranges and aggression based on table position."""

    def decide(self, game_state: GameState, hand_strength: HandStrength) -> Decision | None:
        # TODO: Detect position from dealer button + seat count
        # Adjust preflop tiers: -1 tier in CO/BTN, +1 tier in EP/UTG
        # Adjust postflop aggression based on position
        return None
