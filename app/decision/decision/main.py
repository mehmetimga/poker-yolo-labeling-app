"""FastAPI application for the decision engine."""

import asyncio
import logging

from contextlib import asynccontextmanager
from fastapi import FastAPI

from .api.decision_router import router as decision_router
from .api.health_router import router as health_router, set_consumer
from .client.actuator_client import close_client, send_to_actuator
from .client.state_tracker import StateTracker
from .client.ws_consumer import BotrunnerConsumer
from .log.decision_buffer import decision_buffer
from .log.file_logger import log_decision
from .strategy.composer import StrategyComposer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

composer = StrategyComposer()
state_tracker = StateTracker()
consumer: BotrunnerConsumer | None = None


async def _on_game_state(game_state):
    """Called by WS consumer when a hero-turn state arrives."""
    if not state_tracker.should_decide(game_state):
        return

    decision = composer.decide(game_state)
    if decision is None:
        return

    state_tracker.mark_decided()
    decision_buffer.update(decision)
    log_decision(decision)
    logger.info(
        "Decision: %s %s | %s | %s",
        decision.action,
        f"${decision.amount:.2f}" if decision.amount else "",
        decision.reasoning,
        decision.hand_strength.category,
    )

    # Send to actuator (non-blocking — fire and forget)
    asyncio.create_task(send_to_actuator(decision.action, decision.amount))


@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer
    consumer = BotrunnerConsumer(on_state=_on_game_state)
    set_consumer(consumer)
    await consumer.start()
    yield
    await consumer.stop()
    await close_client()


app = FastAPI(
    title="Poker Decision Engine",
    description="TAG strategy engine consuming botrunner game state",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health_router, tags=["health"])
app.include_router(decision_router, tags=["decisions"])
