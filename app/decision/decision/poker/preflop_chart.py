"""169 starting hands mapped to tiers 1-8 for TAG 6-max micro-stakes."""

from ..models.card import Card
from .card import hand_notation

# Tier 1: Premium — always raise/3-bet
# Tier 2: Strong — raise, call 3-bet
# Tier 3: Good — raise, call raises, fold to 3-bet
# Tier 4: Playable — raise in position, call
# Tier 5: Speculative — call in late position
# Tier 6: Marginal — play only LP/blinds
# Tier 7: Weak — rarely play
# Tier 8: Trash — fold

PREFLOP_TIERS: dict[str, int] = {
    # Tier 1: Premium
    "AA": 1, "KK": 1, "QQ": 1, "AKs": 1,
    # Tier 2: Strong
    "JJ": 2, "TT": 2, "AQs": 2, "AKo": 2, "AJs": 2,
    # Tier 3: Good
    "99": 3, "88": 3, "ATs": 3, "AQo": 3, "KQs": 3, "KJs": 3, "QJs": 3,
    # Tier 4: Playable
    "77": 4, "66": 4,
    "A9s": 4, "A8s": 4, "A7s": 4, "A6s": 4, "A5s": 4, "A4s": 4, "A3s": 4, "A2s": 4,
    "KTs": 4, "QTs": 4, "JTs": 4, "T9s": 4,
    "AJo": 4, "KQo": 4,
    # Tier 5: Speculative
    "55": 5, "44": 5, "33": 5, "22": 5,
    "K9s": 5, "K8s": 5, "K7s": 5, "K6s": 5,
    "Q9s": 5, "J9s": 5, "T8s": 5, "98s": 5, "87s": 5, "76s": 5, "65s": 5,
    # Tier 6: Marginal
    "ATo": 6, "A9o": 6, "A8o": 6,
    "K5s": 6, "K4s": 6, "K3s": 6, "K2s": 6,
    "Q8s": 6, "J8s": 6, "T7s": 6, "97s": 6, "86s": 6, "75s": 6, "64s": 6, "54s": 6,
    # Tier 7: Weak
    "KJo": 7, "KTo": 7, "QJo": 7, "QTo": 7, "JTo": 7,
    "A7o": 7, "A6o": 7, "A5o": 7, "A4o": 7, "A3o": 7, "A2o": 7,
    "Q7s": 7, "Q6s": 7, "Q5s": 7, "Q4s": 7, "Q3s": 7, "Q2s": 7,
    "J7s": 7, "J6s": 7, "J5s": 7, "J4s": 7, "J3s": 7, "J2s": 7,
    "T6s": 7, "T5s": 7, "T4s": 7, "T3s": 7, "T2s": 7,
    "96s": 7, "95s": 7, "94s": 7, "93s": 7, "92s": 7,
    "85s": 7, "84s": 7, "83s": 7, "82s": 7,
    "74s": 7, "73s": 7, "72s": 7,
    "63s": 7, "62s": 7,
    "53s": 7, "52s": 7,
    "43s": 7, "42s": 7,
    "32s": 7,
}
# Everything not listed is tier 8 (trash offsuit combos)


def get_preflop_tier(c1: Card, c2: Card) -> int:
    """Return tier 1-8 for a starting hand. 8 = trash (fold)."""
    notation = hand_notation(c1, c2)
    return PREFLOP_TIERS.get(notation, 8)
