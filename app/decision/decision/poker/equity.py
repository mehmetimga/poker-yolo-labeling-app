"""Equity estimation using the Rule of 2 and 4."""


def estimate_equity(outs: int, game_phase: str) -> float:
    """Estimate equity from outs count.

    Rule of 2 and 4:
    - Flop (2 cards to come): equity ~ outs * 4%
    - Turn (1 card to come): equity ~ outs * 2%

    Returns a float between 0.0 and 1.0.
    """
    if outs <= 0:
        return 0.0

    if game_phase == "flop":
        raw = outs * 4.0
    elif game_phase == "turn":
        raw = outs * 2.0
    else:
        # Preflop or river: not applicable for draw equity
        return 0.0

    # Cap at reasonable maximums
    return min(raw / 100.0, 0.54)
