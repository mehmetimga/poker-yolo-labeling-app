"""Layer 2: Pot odds vs equity strategy (stub for future implementation)."""

from ..models.decision import Decision, HandStrength
from ..models.game_state import GameState


class PotOddsStrategy:
    """Compare pot odds to estimated equity for call/fold decisions."""

    def decide(self, game_state: GameState, hand_strength: HandStrength) -> Decision | None:
        # TODO: Implement pot odds calculation
        # pot_odds = call_amount / (pot_size + call_amount)
        # if equity > pot_odds * 1.1: call/raise
        # elif equity < pot_odds * 0.8: fold
        return None
