"""Decision output models."""

from pydantic import BaseModel


class HandStrength(BaseModel):
    category: str           # "high_card"|"pair"|"two_pair"|"trips"|"straight"|"flush"|"full_house"|"quads"|"straight_flush"
    draws: list[str] = []   # "flush_draw","oesd","gutshot"
    outs: int = 0
    equity_estimate: float = 0.0


class Decision(BaseModel):
    timestamp: float
    frame_id: str
    game_phase: str
    hero_cards: list[str]       # ["Ah","Ks"]
    community_cards: list[str]
    pot_size: float | None
    action: str                 # "fold"|"call"|"check"|"raise"|"bet"|"all_in"
    amount: float | None = None
    reasoning: str
    hand_strength: HandStrength
    strategy_layer: str
    confidence: float
