"""Poker hand evaluator: rank the best 5-card hand from up to 7 cards."""

from itertools import combinations

from ..models.card import Card, Rank


# Hand categories (higher = better)
HIGH_CARD = 0
ONE_PAIR = 1
TWO_PAIR = 2
THREE_OF_A_KIND = 3
STRAIGHT = 4
FLUSH = 5
FULL_HOUSE = 6
FOUR_OF_A_KIND = 7
STRAIGHT_FLUSH = 8

CATEGORY_NAMES = {
    HIGH_CARD: "high_card",
    ONE_PAIR: "pair",
    TWO_PAIR: "two_pair",
    THREE_OF_A_KIND: "trips",
    STRAIGHT: "straight",
    FLUSH: "flush",
    FULL_HOUSE: "full_house",
    FOUR_OF_A_KIND: "quads",
    STRAIGHT_FLUSH: "straight_flush",
}


def _rank_five(cards: tuple[Card, ...]) -> tuple[int, ...]:
    """Score a 5-card hand as a comparable tuple (category, tiebreakers...)."""
    ranks = sorted([c.rank for c in cards], reverse=True)
    suits = [c.suit for c in cards]

    is_flush = len(set(suits)) == 1

    # Check straight (including A-5 wheel)
    unique_ranks = sorted(set(ranks), reverse=True)
    is_straight = False
    straight_high = 0

    if len(unique_ranks) >= 5:
        for i in range(len(unique_ranks) - 4):
            if unique_ranks[i] - unique_ranks[i + 4] == 4:
                is_straight = True
                straight_high = unique_ranks[i]
                break
        # Wheel: A-2-3-4-5
        if not is_straight and set(unique_ranks) >= {Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE}:
            is_straight = True
            straight_high = Rank.FIVE  # 5-high straight

    if is_straight and is_flush:
        return (STRAIGHT_FLUSH, straight_high)

    # Count rank occurrences
    from collections import Counter
    rank_counts = Counter(ranks)
    groups = sorted(rank_counts.items(), key=lambda x: (x[1], x[0]), reverse=True)

    counts = [g[1] for g in groups]
    group_ranks = [g[0] for g in groups]

    if counts[0] == 4:
        return (FOUR_OF_A_KIND, group_ranks[0], group_ranks[1])

    if counts[0] == 3 and counts[1] == 2:
        return (FULL_HOUSE, group_ranks[0], group_ranks[1])

    if is_flush:
        return (FLUSH, *ranks)

    if is_straight:
        return (STRAIGHT, straight_high)

    if counts[0] == 3:
        return (THREE_OF_A_KIND, group_ranks[0], group_ranks[1], group_ranks[2])

    if counts[0] == 2 and counts[1] == 2:
        high_pair = max(group_ranks[0], group_ranks[1])
        low_pair = min(group_ranks[0], group_ranks[1])
        kicker = group_ranks[2]
        return (TWO_PAIR, high_pair, low_pair, kicker)

    if counts[0] == 2:
        return (ONE_PAIR, group_ranks[0], group_ranks[1], group_ranks[2], group_ranks[3])

    return (HIGH_CARD, *ranks)


def evaluate_hand(cards: list[Card]) -> tuple[int, ...]:
    """Evaluate the best 5-card hand from a list of 5-7 cards.
    Returns a comparable tuple: (category, tiebreakers...)."""
    if len(cards) < 5:
        # Pad with placeholder low ranks — shouldn't happen in normal play
        return (HIGH_CARD, *sorted([c.rank for c in cards], reverse=True))

    if len(cards) == 5:
        return _rank_five(tuple(cards))

    # Best of all 5-card combinations
    best = max(
        (_rank_five(combo) for combo in combinations(cards, 5)),
    )
    return best


def hand_category_name(score: tuple[int, ...]) -> str:
    """Return human-readable category name from evaluation score."""
    return CATEGORY_NAMES.get(score[0], "unknown")
