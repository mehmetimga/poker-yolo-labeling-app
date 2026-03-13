"""Layer 1: Rule-based TAG strategy for micro-stakes 6-max."""

import random
import time

from ..config import settings
from ..models.card import Card
from ..models.decision import Decision, HandStrength
from ..models.game_state import AvailableAction, GameState
from ..poker.card import parse_card_value
from ..poker.hand_eval import (
    FLUSH,
    FOUR_OF_A_KIND,
    FULL_HOUSE,
    ONE_PAIR,
    STRAIGHT,
    STRAIGHT_FLUSH,
    THREE_OF_A_KIND,
    TWO_PAIR,
    evaluate_hand,
    hand_category_name,
)
from ..poker.equity import estimate_equity
from ..poker.outs import count_outs
from ..poker.preflop_chart import get_preflop_tier


def _find_action(available: list[AvailableAction], desired: str) -> AvailableAction | None:
    """Find an available action matching the desired action name."""
    for a in available:
        if a.action == desired:
            return a
    return None


def _find_bet_or_raise(available: list[AvailableAction]) -> AvailableAction | None:
    """Find a raise or bet action."""
    for name in ("raise", "bet"):
        a = _find_action(available, name)
        if a:
            return a
    return None


def _can_check(available: list[AvailableAction]) -> bool:
    return _find_action(available, "check") is not None


def _make_decision(
    game_state: GameState,
    hand_strength: HandStrength,
    action: str,
    amount: float | None,
    reasoning: str,
) -> Decision:
    return Decision(
        timestamp=time.time(),
        frame_id=game_state.frame_id,
        game_phase=game_state.game_phase,
        hero_cards=[f"{c.rank}{c.suit}" for c in game_state.hero_cards],
        community_cards=[f"{c.rank}{c.suit}" for c in game_state.community_cards],
        pot_size=game_state.pot_size,
        action=action,
        amount=amount,
        reasoning=reasoning,
        hand_strength=hand_strength,
        strategy_layer="layer1_rules",
        confidence=0.7,
    )


def _detect_scenario(game_state: GameState) -> str:
    """Detect preflop scenario: 'open', 'facing_raise', 'facing_3bet'."""
    bet = game_state.current_bet_to_call
    bb = settings.big_blind

    if bet is None or bet <= bb:
        return "open"
    if bet <= bb * 10:
        return "facing_raise"
    return "facing_3bet"


class RuleBasedStrategy:
    """Tight-aggressive rule-based strategy."""

    def decide(self, game_state: GameState, hand_strength: HandStrength) -> Decision | None:
        if game_state.game_phase == "preflop":
            return self._preflop(game_state, hand_strength)
        if game_state.game_phase in ("flop", "turn", "river"):
            return self._postflop(game_state, hand_strength)
        return None

    def _preflop(self, gs: GameState, hs: HandStrength) -> Decision | None:
        hero_cards = [parse_card_value(cv) for cv in gs.hero_cards]
        hero_cards = [c for c in hero_cards if c is not None]
        if len(hero_cards) < 2:
            return None

        tier = get_preflop_tier(hero_cards[0], hero_cards[1])
        scenario = _detect_scenario(gs)
        available = gs.available_actions
        bb = settings.big_blind

        # Tier 1: Always raise/re-raise
        if tier == 1:
            raise_action = _find_bet_or_raise(available)
            if raise_action:
                if scenario == "open":
                    amt = bb * 3
                elif scenario == "facing_raise":
                    amt = (gs.current_bet_to_call or bb) * 3
                else:  # facing_3bet
                    # 4-bet shove
                    all_in = _find_action(available, "all_in")
                    if all_in:
                        return _make_decision(gs, hs, "all_in", all_in.amount,
                            f"Tier 1 hand, 4-bet shove vs 3-bet")
                    amt = (gs.current_bet_to_call or bb) * 3
                return _make_decision(gs, hs, raise_action.action,
                    raise_action.amount or amt,
                    f"Tier {tier} premium hand, raise {scenario}")

        # Tier 2: Raise or call 3-bet
        if tier == 2:
            if scenario in ("open", "facing_raise"):
                raise_action = _find_bet_or_raise(available)
                if raise_action:
                    amt = bb * 3 if scenario == "open" else (gs.current_bet_to_call or bb) * 2.5
                    return _make_decision(gs, hs, raise_action.action,
                        raise_action.amount or amt,
                        f"Tier {tier} strong hand, raise {scenario}")
            if scenario == "facing_3bet":
                call_action = _find_action(available, "call")
                if call_action:
                    return _make_decision(gs, hs, "call", call_action.amount,
                        f"Tier {tier} calling 3-bet")

        # Tier 3: Raise open, call raise, fold to 3-bet
        if tier == 3:
            if scenario == "open":
                raise_action = _find_bet_or_raise(available)
                if raise_action:
                    return _make_decision(gs, hs, raise_action.action,
                        raise_action.amount or bb * 3,
                        f"Tier {tier} good hand, open raise")
            if scenario == "facing_raise":
                call_action = _find_action(available, "call")
                if call_action:
                    return _make_decision(gs, hs, "call", call_action.amount,
                        f"Tier {tier} calling raise")

        # Tier 4: Raise in position, call raises
        if tier == 4:
            if scenario == "open":
                raise_action = _find_bet_or_raise(available)
                if raise_action:
                    return _make_decision(gs, hs, raise_action.action,
                        raise_action.amount or bb * 3,
                        f"Tier {tier} playable hand, open raise")
            if scenario == "facing_raise":
                call_action = _find_action(available, "call")
                if call_action:
                    return _make_decision(gs, hs, "call", call_action.amount,
                        f"Tier {tier} calling raise")

        # Tier 5: Call in late position only
        if tier == 5:
            if scenario == "open":
                call_action = _find_action(available, "call")
                raise_action = _find_bet_or_raise(available)
                if raise_action:
                    return _make_decision(gs, hs, raise_action.action,
                        raise_action.amount or bb * 2.5,
                        f"Tier {tier} speculative hand, min-raise")
                if call_action:
                    return _make_decision(gs, hs, "call", call_action.amount,
                        f"Tier {tier} speculative hand, limp")

        # Tiers 6-8: Fold (or check if free)
        if _can_check(available):
            return _make_decision(gs, hs, "check", None,
                f"Tier {tier} weak hand, free check")

        return _make_decision(gs, hs, "fold", None,
            f"Tier {tier} hand, fold {scenario}")

    def _postflop(self, gs: GameState, hs: HandStrength) -> Decision | None:
        available = gs.available_actions
        pot = gs.pot_size or settings.big_blind * 2
        category = hs.category

        # Strong hand: two pair or better — bet/raise
        if category in ("two_pair", "trips", "straight", "flush",
                        "full_house", "quads", "straight_flush"):
            bet_fraction = 0.65 if category in ("two_pair", "trips") else 0.75
            bet_amt = pot * bet_fraction
            raise_action = _find_bet_or_raise(available)
            if raise_action:
                return _make_decision(gs, hs, raise_action.action,
                    raise_action.amount or bet_amt,
                    f"Strong hand ({category}), value bet {int(bet_fraction*100)}% pot")
            # If can't bet/raise, call
            call_action = _find_action(available, "call")
            if call_action:
                return _make_decision(gs, hs, "call", call_action.amount,
                    f"Strong hand ({category}), calling")

        # Medium hand: one pair — bet smaller or call
        if category == "pair":
            if _can_check(available) and gs.current_bet_to_call:
                # Facing a bet with just a pair — call small bets, fold large
                call_action = _find_action(available, "call")
                if call_action and call_action.amount and call_action.amount <= pot * 0.5:
                    return _make_decision(gs, hs, "call", call_action.amount,
                        "Medium hand (pair), calling small bet")
                return _make_decision(gs, hs, "fold", None,
                    "Medium hand (pair), bet too large to call")
            # No bet to call — bet for value
            raise_action = _find_bet_or_raise(available)
            if raise_action:
                bet_amt = pot * settings.bet_size_fraction
                return _make_decision(gs, hs, raise_action.action,
                    raise_action.amount or bet_amt,
                    f"Medium hand (pair), bet {int(settings.bet_size_fraction*100)}% pot")

        # Draw: semi-bluff or call with odds
        if hs.outs >= 8:
            raise_action = _find_bet_or_raise(available)
            if raise_action:
                bet_amt = pot * 0.5
                return _make_decision(gs, hs, raise_action.action,
                    raise_action.amount or bet_amt,
                    f"Drawing hand ({', '.join(hs.draws)}, {hs.outs} outs), semi-bluff")
            call_action = _find_action(available, "call")
            if call_action:
                return _make_decision(gs, hs, "call", call_action.amount,
                    f"Drawing hand ({', '.join(hs.draws)}, {hs.outs} outs), calling")

        # Weak draw (4 outs gutshot) — call if cheap
        if hs.outs >= 4:
            call_action = _find_action(available, "call")
            if call_action and call_action.amount and call_action.amount <= pot * 0.25:
                return _make_decision(gs, hs, "call", call_action.amount,
                    f"Gutshot draw, cheap call")

        # Air: c-bet sometimes on flop if we can bet
        if gs.game_phase == "flop" and random.random() < settings.cbet_frequency:
            raise_action = _find_bet_or_raise(available)
            if raise_action:
                bet_amt = pot * 0.4
                return _make_decision(gs, hs, raise_action.action,
                    raise_action.amount or bet_amt,
                    "Air, continuation bet on flop")

        # Default: check or fold
        if _can_check(available):
            return _make_decision(gs, hs, "check", None,
                f"Weak hand ({category}), check")

        return _make_decision(gs, hs, "fold", None,
            f"Weak hand ({category}), fold")
