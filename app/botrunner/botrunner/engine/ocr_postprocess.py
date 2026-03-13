"""Post-processing for OCR text: card values, dollar amounts, button actions."""

import re

# --- Card parsing ---
# Matches standard poker card notation: rank + suit
_CARD_PATTERN = re.compile(r"([2-9TJQKA])([hdcsHDCS])", re.IGNORECASE)

# Common OCR misreads for card characters
_CARD_FIXES = {
    "1O": "10", "l0": "10", "IO": "10",
    "0": "O", "o": "O",
}

_RANK_MAP = {
    "10": "T", "1": "A", "l": "1",
}

_SUIT_MAP = {
    "H": "h", "D": "d", "C": "c", "S": "s",
}


def parse_card(raw_text: str) -> tuple[str, str] | None:
    """Parse a card value like 'Ah', 'Kd', 'Ts' from OCR text.
    Returns (rank, suit) or None if not parseable."""
    text = raw_text.strip()

    # Apply common OCR fix-ups
    for wrong, right in _CARD_FIXES.items():
        text = text.replace(wrong, right)

    # Try to map '10' -> 'T' before regex
    text = text.replace("10", "T")

    match = _CARD_PATTERN.search(text)
    if not match:
        return None

    rank = match.group(1).upper()
    suit = _SUIT_MAP.get(match.group(2), match.group(2).lower())
    return rank, suit


# --- Dollar amount parsing ---
_DOLLAR_PATTERN = re.compile(r"\$?\s*([\d,]+\.?\d*)")


def parse_dollar_amount(raw_text: str) -> float | None:
    """Parse a dollar amount from text like '$12.50', 'Pot: $100', '$1,234.56'."""
    text = raw_text.strip()
    match = _DOLLAR_PATTERN.search(text)
    if not match:
        return None
    try:
        cleaned = match.group(1).replace(",", "")
        return float(cleaned)
    except ValueError:
        return None


# --- Button text parsing ---
_ACTION_PATTERNS = [
    (re.compile(r"(?i)all[\s-]*in", re.IGNORECASE), "all_in"),
    (re.compile(r"(?i)fold"), "fold"),
    (re.compile(r"(?i)check"), "check"),
    (re.compile(r"(?i)call"), "call"),
    (re.compile(r"(?i)raise"), "raise"),
    (re.compile(r"(?i)bet"), "bet"),
]


def parse_button_text(raw_text: str) -> tuple[str, float | None]:
    """Parse a button label like 'Call $5.00', 'Raise to $15'.
    Returns (action, amount_or_none)."""
    text = raw_text.strip()

    action = "unknown"
    for pattern, action_name in _ACTION_PATTERNS:
        if pattern.search(text):
            action = action_name
            break

    amount = parse_dollar_amount(text)
    return action, amount


# --- Blinds parsing ---
_BLINDS_PATTERN = re.compile(r"\$?([\d,.]+)\s*/\s*\$?([\d,.]+)")


def parse_blinds(raw_text: str) -> tuple[float, float] | None:
    """Parse blinds text like '$0.25/$0.50'. Returns (small, big) or None."""
    match = _BLINDS_PATTERN.search(raw_text)
    if not match:
        return None
    try:
        small = float(match.group(1).replace(",", ""))
        big = float(match.group(2).replace(",", ""))
        return small, big
    except ValueError:
        return None
