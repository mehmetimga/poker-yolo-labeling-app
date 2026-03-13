"""Coordinator: resolve action → safety check → execute click."""

import logging

from ..config import settings
from ..models.actuator_models import ClickRequest, ClickResult, DetectionMap
from ..pipeline.detection_map_buffer import detection_map_buffer
from .action_resolver import find_button, to_logical_coords, to_screen_coords, resolve_slider_position
from .base import ClickExecutor
from .factory import create_executor
from .safety import actuator_safety

logger = logging.getLogger(__name__)

# Methods that need screen coords (macOS window-relative)
SCREEN_COORD_METHODS = {"pyautogui", "cliclick", "applescript"}
# Methods that need logical device coords (ADB/Appium handle their own scaling)
DEVICE_COORD_METHODS = {"adb", "appium"}


async def execute_action(request: ClickRequest) -> ClickResult:
    """Full pipeline: resolve → safety → click."""
    method = request.method or settings.actuator_method

    # 1. Get latest detection map
    dmap = detection_map_buffer.get_latest()
    if dmap is None:
        return ClickResult(status="not_found", action=request.action, detail="No detection map available")

    # 2. Find the button
    button = find_button(dmap, request.action)
    if button is None:
        return ClickResult(status="not_found", action=request.action, detail=f"Button for '{request.action}' not found in detections")

    # 3. Convert coordinates based on method
    if method in SCREEN_COORD_METHODS:
        click_x, click_y = to_screen_coords(dmap, button.center_x, button.center_y)
    else:
        click_x, click_y = to_logical_coords(dmap, button.center_x, button.center_y)

    # 4. Safety checks
    safety_result = await actuator_safety.check_and_delay()
    if safety_result == "dry_run":
        logger.info(f"DRY RUN: would {method} tap ({click_x}, {click_y}) for {request.action}")
        return ClickResult(
            status="dry_run", action=request.action,
            screen_x=click_x, screen_y=click_y,
            detail=f"method={method}",
        )
    if safety_result is not None:
        return ClickResult(
            status="safety_blocked", action=request.action,
            detail=safety_result,
        )

    # 5. Handle raise/bet with slider
    if request.action in ("raise", "bet") and request.amount is not None and dmap.slider:
        # Find min/max amounts from available buttons
        min_amt = button.amount or 0.0
        max_amt = min_amt * 10  # rough estimate, will be refined from GameState
        slider_pos = resolve_slider_position(dmap, request.amount, min_amt, max_amt)
        if slider_pos:
            executor = create_executor(method)
            sx, sy = slider_pos
            if method in SCREEN_COORD_METHODS:
                sx, sy = to_screen_coords(dmap, sx, sy)
            else:
                sx, sy = to_logical_coords(dmap, sx, sy)
            await executor.tap(int(sx), int(sy))
            # Brief pause before clicking confirm button
            import asyncio
            await asyncio.sleep(0.2)

    # 6. Execute the click
    executor = create_executor(method)
    success = await executor.tap(click_x, click_y)

    if success:
        return ClickResult(
            status="clicked", action=request.action,
            screen_x=click_x, screen_y=click_y,
            detail=f"method={method}",
        )
    return ClickResult(
        status="click_failed", action=request.action,
        screen_x=click_x, screen_y=click_y,
        detail=f"method={method} tap returned False",
    )
