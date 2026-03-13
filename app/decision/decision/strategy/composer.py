"""Strategy composer: evaluate hand and chain strategy layers."""

import logging
import time

from ..config import settings
from ..models.decision import Decision, HandStrength
from ..models.game_state import GameState
from ..poker.card import parse_card_value
from ..poker.equity import estimate_equity
from ..poker.hand_eval import evaluate_hand, hand_category_name
from ..poker.outs import count_outs
from .base import StrategyLayer
from .layer1_rules import RuleBasedStrategy

logger = logging.getLogger(__name__)


def _evaluate_hand_strength(game_state: GameState) -> HandStrength:
    """Build HandStrength from game state."""
    hero = [parse_card_value(cv) for cv in game_state.hero_cards]
    hero = [c for c in hero if c is not None]
    board = [parse_card_value(cv) for cv in game_state.community_cards]
    board = [c for c in board if c is not None]

    if not hero:
        return HandStrength(category="unknown", draws=[], outs=0, equity_estimate=0.0)

    all_cards = hero + board

    # Hand evaluation
    if len(all_cards) >= 5:
        score = evaluate_hand(all_cards)
        category = hand_category_name(score)
    elif len(hero) == 2 and not board:
        category = "preflop"
    else:
        category = "high_card"

    # Draw detection (only on flop/turn)
    draws = []
    outs = 0
    if board and game_state.game_phase in ("flop", "turn"):
        draws, outs = count_outs(hero, board)

    equity = estimate_equity(outs, game_state.game_phase)

    return HandStrength(
        category=category,
        draws=draws,
        outs=outs,
        equity_estimate=round(equity, 3),
    )


class StrategyComposer:
    """Chains strategy layers. First non-None decision wins."""

    def __init__(self):
        self.layers: list[StrategyLayer] = []
        self._init_layers()

    def _init_layers(self):
        layer_names = [l.strip() for l in settings.active_layers.split(",")]
        for name in layer_names:
            if name == "rules":
                self.layers.append(RuleBasedStrategy())
            # Future: "odds" -> Layer2, "position" -> Layer3
        if not self.layers:
            self.layers.append(RuleBasedStrategy())

    def decide(self, game_state: GameState) -> Decision | None:
        """Evaluate hand and run through strategy layers."""
        # Gate: skip low-confidence states
        if game_state.schema_confidence < settings.min_schema_confidence:
            logger.debug("Skipping low schema confidence: %.3f", game_state.schema_confidence)
            return None

        # Gate: skip if hero cards are low confidence
        if game_state.hero_cards:
            min_conf = min(c.confidence for c in game_state.hero_cards)
            if min_conf < settings.min_card_confidence:
                logger.debug("Skipping low card confidence: %.3f", min_conf)
                return None

        hand_strength = _evaluate_hand_strength(game_state)

        for layer in self.layers:
            decision = layer.decide(game_state, hand_strength)
            if decision is not None:
                return decision

        # Ultimate fallback: fold
        return Decision(
            timestamp=time.time(),
            frame_id=game_state.frame_id,
            game_phase=game_state.game_phase,
            hero_cards=[f"{c.rank}{c.suit}" for c in game_state.hero_cards],
            community_cards=[f"{c.rank}{c.suit}" for c in game_state.community_cards],
            pot_size=game_state.pot_size,
            action="fold",
            reasoning="No strategy layer produced a decision, default fold",
            hand_strength=hand_strength,
            strategy_layer="fallback",
            confidence=0.1,
        )
