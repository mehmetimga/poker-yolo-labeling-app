"""Resolve a decision action to button coordinates + slider logic."""

import logging

from ..config import settings
from ..models.actuator_models import ButtonLocation, ClickResult, DetectionMap

logger = logging.getLogger(__name__)

# Map decision action names to possible button labels
ACTION_TO_LABELS = {
    "fold": ["fold_button"],
    "call": ["call_button"],
    "check": ["check_button"],
    "raise": ["raise_button", "bet_button"],
    "bet": ["bet_button", "raise_button"],
    "all_in": ["all_in_button"],
}


def find_button(detection_map: DetectionMap, action: str) -> ButtonLocation | None:
    """Find the button matching the requested action."""
    labels = ACTION_TO_LABELS.get(action, [])
    for label in labels:
        for btn in detection_map.buttons:
            if btn.label == label:
                return btn
    # Fallback: match by action name
    for btn in detection_map.buttons:
        if btn.action == action:
            return btn
    return None


def to_screen_coords(
    detection_map: DetectionMap,
    capture_x: float,
    capture_y: float,
) -> tuple[int, int]:
    """Convert capture-space coords to screen coords (for macOS click methods)."""
    scale = detection_map.retina_scale or 1.0
    logical_x = capture_x / scale
    logical_y = capture_y / scale
    screen_x = round(detection_map.window_left + logical_x)
    screen_y = round(detection_map.window_top + logical_y)
    return screen_x, screen_y


def to_logical_coords(
    detection_map: DetectionMap,
    capture_x: float,
    capture_y: float,
) -> tuple[int, int]:
    """Convert capture-space coords to logical window coords (for ADB/Appium)."""
    scale = detection_map.retina_scale or 1.0
    return round(capture_x / scale), round(capture_y / scale)


def resolve_slider_position(
    detection_map: DetectionMap,
    target_amount: float,
    min_amount: float,
    max_amount: float,
) -> tuple[float, float] | None:
    """Calculate capture-space coords for a slider position."""
    if detection_map.slider is None:
        return None
    if max_amount <= min_amount:
        return None

    fraction = max(0.0, min(1.0, (target_amount - min_amount) / (max_amount - min_amount)))
    slider = detection_map.slider
    click_x = slider.x_min + fraction * (slider.x_max - slider.x_min)
    click_y = slider.center_y
    return click_x, click_y
