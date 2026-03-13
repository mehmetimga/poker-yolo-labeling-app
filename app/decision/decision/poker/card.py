"""Parse botrunner CardValue into internal Card representation."""

from ..models.card import Card, CHAR_TO_RANK, CHAR_TO_SUIT, Rank, Suit, rank_to_char
from ..models.game_state import CardValue


def parse_card_value(cv: CardValue) -> Card | None:
    """Convert botrunner CardValue to internal Card. Returns None if unparseable."""
    rank = CHAR_TO_RANK.get(cv.rank.upper())
    suit = CHAR_TO_SUIT.get(cv.suit.lower())
    if rank is None or suit is None:
        return None
    return Card(rank=rank, suit=suit)


def hand_notation(c1: Card, c2: Card) -> str:
    """Return standard hand notation like 'AKs', 'QJo', 'TT'."""
    high, low = sorted([c1, c2], key=lambda c: c.rank, reverse=True)
    hr = rank_to_char(high.rank)
    lr = rank_to_char(low.rank)
    if high.rank == low.rank:
        return f"{hr}{lr}"  # "AA", "KK"
    suffix = "s" if high.suit == low.suit else "o"
    return f"{hr}{lr}{suffix}"  # "AKs", "AKo"
