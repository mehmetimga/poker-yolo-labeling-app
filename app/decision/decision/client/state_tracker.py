"""Track hand state to avoid duplicate decisions."""

import logging

from ..models.game_state import GameState

logger = logging.getLogger(__name__)


class StateTracker:
    """Deduplicates decisions and detects new hands."""

    def __init__(self):
        self._last_frame_id: str | None = None
        self._last_hero_cards: str | None = None
        self._last_phase: str | None = None
        self._decided_this_street: bool = False

    def should_decide(self, game_state: GameState) -> bool:
        """Return True if we should make a decision for this game state."""
        # Skip duplicate frame
        if game_state.frame_id == self._last_frame_id:
            return False

        # Detect new hand (hero cards changed or phase reset to preflop)
        hero_key = self._cards_key(game_state)
        if hero_key != self._last_hero_cards:
            # New hand
            self._last_hero_cards = hero_key
            self._last_phase = game_state.game_phase
            self._decided_this_street = False
            self._last_frame_id = game_state.frame_id
            return True

        # Detect new street
        if game_state.game_phase != self._last_phase:
            self._last_phase = game_state.game_phase
            self._decided_this_street = False
            self._last_frame_id = game_state.frame_id
            return True

        # Already decided this street — skip
        if self._decided_this_street:
            return False

        self._last_frame_id = game_state.frame_id
        return True

    def mark_decided(self):
        """Mark that we've made a decision for the current street."""
        self._decided_this_street = True

    def _cards_key(self, gs: GameState) -> str:
        if not gs.hero_cards:
            return ""
        return ",".join(f"{c.rank}{c.suit}" for c in gs.hero_cards)
