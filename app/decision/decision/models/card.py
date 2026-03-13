"""Internal card representation for poker math."""

from dataclasses import dataclass
from enum import IntEnum


class Rank(IntEnum):
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14


class Suit(IntEnum):
    CLUBS = 0
    DIAMONDS = 1
    HEARTS = 2
    SPADES = 3


@dataclass(frozen=True)
class Card:
    rank: Rank
    suit: Suit

    def __str__(self) -> str:
        return f"{rank_to_char(self.rank)}{suit_to_char(self.suit)}"


RANK_CHARS = {
    Rank.TWO: "2", Rank.THREE: "3", Rank.FOUR: "4", Rank.FIVE: "5",
    Rank.SIX: "6", Rank.SEVEN: "7", Rank.EIGHT: "8", Rank.NINE: "9",
    Rank.TEN: "T", Rank.JACK: "J", Rank.QUEEN: "Q", Rank.KING: "K",
    Rank.ACE: "A",
}

CHAR_TO_RANK = {v: k for k, v in RANK_CHARS.items()}

SUIT_CHARS = {
    Suit.CLUBS: "c", Suit.DIAMONDS: "d", Suit.HEARTS: "h", Suit.SPADES: "s",
}

CHAR_TO_SUIT = {v: k for k, v in SUIT_CHARS.items()}


def rank_to_char(rank: Rank) -> str:
    return RANK_CHARS[rank]


def suit_to_char(suit: Suit) -> str:
    return SUIT_CHARS[suit]


def card_from_str(s: str) -> Card:
    """Parse 'Ah', 'Td', '2c' etc. into Card."""
    if len(s) != 2:
        raise ValueError(f"Invalid card string: {s}")
    return Card(rank=CHAR_TO_RANK[s[0].upper()], suit=CHAR_TO_SUIT[s[1].lower()])
