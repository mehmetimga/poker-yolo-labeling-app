"""FastAPI application for the botrunner service."""

import logging

from fastapi import FastAPI

from .api.control_router import router as control_router
from .api.game_state_router import router as game_state_router
from .api.health_router import router as health_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Poker Bot Runner",
    description="Live poker vision pipeline: screen capture → YOLO → OCR → game state",
    version="0.1.0",
)

app.include_router(health_router, tags=["health"])
app.include_router(control_router, tags=["pipeline"])
app.include_router(game_state_router, tags=["game-state"])
