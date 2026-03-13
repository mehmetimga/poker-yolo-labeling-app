"""Draw detection and outs counting."""

from collections import Counter

from ..models.card import Card, Rank


def detect_flush_draw(cards: list[Card]) -> int:
    """Return number of flush outs (9 if 4-to-flush, 0 otherwise)."""
    suit_counts = Counter(c.suit for c in cards)
    max_suited = suit_counts.most_common(1)[0][1]
    if max_suited == 4:
        return 9  # 13 - 4 = 9 remaining of that suit
    return 0


def detect_straight_draw(cards: list[Card]) -> tuple[str, int]:
    """Detect straight draws.
    Returns (draw_type, outs) where draw_type is 'oesd', 'gutshot', or 'none'."""
    unique_ranks = sorted(set(c.rank for c in cards))

    # Check for open-ended straight draw (OESD): 4 consecutive ranks
    # that can extend on both sides
    for i in range(len(unique_ranks) - 3):
        window = unique_ranks[i:i + 4]
        if window[-1] - window[0] == 3:
            # 4 consecutive — check if open on both ends
            low = window[0]
            high = window[-1]
            if low > Rank.TWO and high < Rank.ACE:
                return ("oesd", 8)
            # One end blocked (e.g., A-K-Q-J or 4-3-2-A)
            return ("gutshot", 4)

    # Check for gutshot: 4 ranks within a span of 5 with one gap
    for i in range(len(unique_ranks)):
        for j in range(i + 3, len(unique_ranks)):
            if unique_ranks[j] - unique_ranks[i] == 4:
                # Span of 5, count how many of our ranks fall in this span
                count = sum(
                    1 for r in unique_ranks
                    if unique_ranks[i] <= r <= unique_ranks[j]
                )
                if count == 4:
                    return ("gutshot", 4)

    # Check wheel gutshot: A-2-3-4 or A-3-4-5 etc.
    if Rank.ACE in unique_ranks:
        low_ranks = [r for r in unique_ranks if r <= Rank.FIVE]
        low_ranks_with_ace = low_ranks + [Rank.ACE]  # Treat ace as 1
        if len(set(low_ranks_with_ace)) >= 4:
            # Check if 4 within span of 5 (1-5)
            vals = sorted(set([1 if r == Rank.ACE else int(r) for r in low_ranks_with_ace]))
            for i in range(len(vals) - 3):
                if vals[i + 3] - vals[i] <= 4:
                    return ("gutshot", 4)

    return ("none", 0)


def count_outs(hero: list[Card], board: list[Card]) -> tuple[list[str], int]:
    """Detect all draws and return (draw_names, total_outs).
    Caps combined outs at 15 to avoid double-counting."""
    all_cards = hero + board
    draws = []
    total_outs = 0

    flush_outs = detect_flush_draw(all_cards)
    if flush_outs:
        draws.append("flush_draw")
        total_outs += flush_outs

    straight_type, straight_outs = detect_straight_draw(all_cards)
    if straight_outs:
        draws.append(straight_type)
        total_outs += straight_outs

    # Cap for overlap between flush + straight outs
    total_outs = min(total_outs, 15)
    return draws, total_outs
