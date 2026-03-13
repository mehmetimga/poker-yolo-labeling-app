import asyncio
import json
import time

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from starlette.responses import Response

from ..pipeline.state_buffer import state_buffer

router = APIRouter()


@router.get("/state")
async def get_latest_state():
    state = state_buffer.get_latest()
    if state is None:
        return Response(status_code=204)
    response = Response(
        content=state.model_dump_json(),
        media_type="application/json",
    )
    age_ms = (time.time() - state.timestamp) * 1000
    response.headers["X-State-Age-Ms"] = str(round(age_ms))
    return response


@router.get("/state/history")
async def get_state_history(limit: int = Query(10, le=100)):
    states = state_buffer.get_history(limit)
    return [s.model_dump() for s in states]


@router.websocket("/state/stream")
async def state_stream(websocket: WebSocket, only_hero_turn: bool = False):
    await websocket.accept()

    # Send latest state immediately if available
    latest = state_buffer.get_latest()
    if latest and (not only_hero_turn or latest.is_hero_turn):
        await websocket.send_text(latest.model_dump_json())

    queue: asyncio.Queue = asyncio.Queue(maxsize=50)
    state_buffer.add_subscriber(queue)
    try:
        while True:
            try:
                state = await asyncio.wait_for(queue.get(), timeout=5.0)
                if only_hero_turn and not state.is_hero_turn:
                    continue
                await websocket.send_text(state.model_dump_json())
            except asyncio.TimeoutError:
                # Send ping/heartbeat
                await websocket.send_text('{"heartbeat":true}')
    except WebSocketDisconnect:
        pass
    finally:
        state_buffer.remove_subscriber(queue)
