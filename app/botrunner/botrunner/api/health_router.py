import time

from fastapi import APIRouter

from ..config import settings

router = APIRouter()

_start_time = time.time()


@router.get("/health")
async def health():
    from ..pipeline.capture_loop import pipeline_manager
    status = pipeline_manager.get_status()
    return {
        "status": "ok",
        "uptime_s": round(time.time() - _start_time, 1),
        "pipeline_running": status["running"],
        "model_path": settings.yolo_model_path or None,
        "capture_interval_ms": settings.capture_interval_ms,
    }


@router.get("/metrics")
async def metrics():
    from ..pipeline.capture_loop import pipeline_manager
    return pipeline_manager.get_metrics()
