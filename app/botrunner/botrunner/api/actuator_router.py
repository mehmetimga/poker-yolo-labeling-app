"""Actuator API: execute clicks, manage state."""

from fastapi import APIRouter

from ..actuator.coordinator import execute_action
from ..actuator.safety import actuator_safety
from ..config import settings
from ..models.actuator_models import ClickRequest, ClickResult
from ..pipeline.detection_map_buffer import detection_map_buffer

router = APIRouter()


@router.post("/actuator/execute")
async def actuator_execute(request: ClickRequest) -> ClickResult:
    return await execute_action(request)


@router.get("/actuator/status")
async def actuator_status():
    dmap = detection_map_buffer.get_latest()
    return {
        "enabled": settings.actuator_enabled,
        "dry_run": settings.actuator_dry_run,
        "method": settings.actuator_method,
        "kill_switch": actuator_safety.is_killed,
        "detection_map": {
            "available": dmap is not None,
            "frame_id": dmap.frame_id if dmap else None,
            "buttons": len(dmap.buttons) if dmap else 0,
            "has_slider": dmap.slider is not None if dmap else False,
        } if True else None,
    }


@router.post("/actuator/enable")
async def actuator_enable():
    settings.actuator_enabled = True
    settings.actuator_dry_run = False
    return {"message": "Actuator enabled (live mode)"}


@router.post("/actuator/disable")
async def actuator_disable():
    settings.actuator_enabled = False
    return {"message": "Actuator disabled"}


@router.post("/actuator/kill")
async def actuator_kill():
    actuator_safety.kill()
    return {"message": "KILL SWITCH activated — all automation stopped"}
