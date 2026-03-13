"""Maps YOLO detection labels to game state field roles."""

# Which labels represent hero-related elements
HERO_LABELS = {"hero_card", "hero_stack", "hero_seat", "hero_name", "hero_dealer"}

# Which labels represent opponent/player elements
OPPONENT_LABELS = {"opponent_card", "opponent_stack", "opponent_seat", "opponent_name"}

# Community cards
BOARD_LABELS = {"board_card"}

# Pot / betting
POT_LABELS = {"pot_amount"}
BET_LABELS = {"bet_amount"}
STACK_LABELS = {"stack_amount", "hero_stack", "opponent_stack"}

# Action buttons
BUTTON_LABELS = {
    "fold_button", "call_button", "check_button",
    "raise_button", "bet_button", "all_in_button",
}

# Dealer / position
DEALER_LABELS = {"dealer_button", "hero_dealer"}

# Game phase indicators
PHASE_LABELS = {"blinds_label"}

# Non-game labels
NON_GAME_LABELS = {"lobby_element", "menu_element", "chat_message"}

# Labels that indicate hero's turn (action buttons visible)
HERO_TURN_INDICATORS = {"fold_button", "call_button", "check_button", "raise_button", "bet_button"}

# Schema-to-game-phase mapping
SCHEMA_PHASE_MAP = {
    "preflop_no_board": "preflop",
    "preflop_hero_turn": "preflop",
    "flop_3_cards": "flop",
    "flop_hero_turn": "flop",
    "turn_4_cards": "turn",
    "turn_hero_turn": "turn",
    "river_5_cards": "river",
    "river_hero_turn": "river",
    "showdown": "showdown",
    "all_in_run": "showdown",
    "waiting_for_hand": "non_game",
    "lobby": "non_game",
    "sit_out": "non_game",
    "table_overview": "non_game",
    "hand_result": "showdown",
    "tournament_info": "non_game",
}


def get_game_phase(schema_name: str) -> str:
    """Map schema name to game phase."""
    return SCHEMA_PHASE_MAP.get(schema_name, "unknown")


def is_hero_turn(detections_labels: set[str]) -> bool:
    """Check if hero's turn based on visible action buttons."""
    return bool(detections_labels & HERO_TURN_INDICATORS)
