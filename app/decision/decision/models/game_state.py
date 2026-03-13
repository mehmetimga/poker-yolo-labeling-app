"""Re-declared GameState models matching botrunner JSON output."""

from pydantic import BaseModel


class CardValue(BaseModel):
    rank: str
    suit: str
    raw_text: str
    confidence: float


class PlayerInfo(BaseModel):
    seat_index: int
    name: str | None = None
    stack: float | None = None
    bet: float | None = None
    is_hero: bool = False
    is_folded: bool = False
    is_all_in: bool = False
    cards: list[CardValue] = []


class AvailableAction(BaseModel):
    action: str
    amount: float | None = None
    confidence: float


class GameState(BaseModel):
    timestamp: float
    frame_id: str
    game_phase: str
    schema_name: str
    schema_confidence: float
    is_hero_turn: bool
    hero_cards: list[CardValue] = []
    community_cards: list[CardValue] = []
    pot_size: float | None = None
    current_bet_to_call: float | None = None
    hero_stack: float | None = None
    players: list[PlayerInfo] = []
    available_actions: list[AvailableAction] = []
    capture_ms: float = 0.0
    inference_ms: float = 0.0
    ocr_ms: float = 0.0
    total_ms: float = 0.0
    raw_detections: int = 0
    detection_confidence_avg: float = 0.0
