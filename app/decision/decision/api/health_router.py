import time

from fastapi import APIRouter

from ..config import settings

router = APIRouter()

_start_time = time.time()
_consumer_ref = None


def set_consumer(consumer):
    global _consumer_ref
    _consumer_ref = consumer


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "uptime_s": round(time.time() - _start_time, 1),
        "botrunner_connected": _consumer_ref.connected if _consumer_ref else False,
        "botrunner_url": f"ws://{settings.botrunner_host}:{settings.botrunner_port}",
        "active_layers": settings.active_layers,
        "big_blind": settings.big_blind,
    }
