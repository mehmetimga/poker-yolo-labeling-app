import time

from fastapi import APIRouter, Query
from starlette.responses import Response

from ..log.decision_buffer import decision_buffer

router = APIRouter()


@router.get("/decision/latest")
async def get_latest_decision():
    decision = decision_buffer.get_latest()
    if decision is None:
        return Response(status_code=204)
    return Response(
        content=decision.model_dump_json(),
        media_type="application/json",
    )


@router.get("/decision/history")
async def get_decision_history(limit: int = Query(20, le=200)):
    decisions = decision_buffer.get_history(limit)
    return [d.model_dump() for d in decisions]
