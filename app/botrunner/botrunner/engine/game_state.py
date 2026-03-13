"""Assemble GameState from detections, OCR results, and schema classification."""

import logging
import time
import uuid

from ..models.actuator_models import ButtonLocation, DetectionMap, SliderLocation
from ..models.game_state_models import (
    AvailableAction,
    CardValue,
    GameState,
    PlayerInfo,
)
from ..models.pipeline_models import Detection, FrameResult, OCRResult
from .label_mapping import (
    BOARD_LABELS,
    BUTTON_LABELS,
    HERO_LABELS,
    HERO_TURN_INDICATORS,
    POT_LABELS,
    STACK_LABELS,
    get_game_phase,
    is_hero_turn,
)
from .ocr_postprocess import parse_button_text, parse_card, parse_dollar_amount

logger = logging.getLogger(__name__)


def _build_cards(
    detections: list[Detection],
    ocr_results: list[OCRResult],
    target_labels: set[str],
) -> list[CardValue]:
    """Build CardValue list from OCR results matching target labels."""
    cards = []
    for ocr in ocr_results:
        if ocr.label not in target_labels:
            continue
        parsed = parse_card(ocr.raw_text)
        if parsed:
            rank, suit = parsed
            cards.append(CardValue(
                rank=rank,
                suit=suit,
                raw_text=ocr.raw_text,
                confidence=ocr.confidence,
            ))
    return cards


def _build_actions(
    detections: list[Detection],
    ocr_results: list[OCRResult],
) -> list[AvailableAction]:
    """Build AvailableAction list from button detections + OCR."""
    actions = []
    # Map detection index to OCR
    ocr_by_idx = {ocr.detection_index: ocr for ocr in ocr_results}

    for i, det in enumerate(detections):
        if det.label not in BUTTON_LABELS:
            continue
        ocr = ocr_by_idx.get(i)
        if ocr:
            action_name, amount = parse_button_text(ocr.raw_text)
        else:
            # Infer action from label name
            action_name = det.label.replace("_button", "")
            amount = None
        actions.append(AvailableAction(
            action=action_name,
            amount=amount,
            confidence=det.confidence,
        ))
    return actions


def _extract_amount(
    ocr_results: list[OCRResult],
    target_labels: set[str],
) -> float | None:
    """Extract the first dollar amount from OCR results matching target labels."""
    for ocr in ocr_results:
        if ocr.label not in target_labels:
            continue
        amount = parse_dollar_amount(ocr.raw_text)
        if amount is not None:
            return amount
    return None


def assemble_game_state(frame_result: FrameResult) -> GameState:
    """Convert a FrameResult into a full GameState."""
    detections = frame_result.detections
    ocr_results = frame_result.ocr_results

    detection_labels = {d.label for d in detections}
    game_phase = get_game_phase(frame_result.schema_name)
    hero_turn = is_hero_turn(detection_labels)

    hero_cards = _build_cards(detections, ocr_results, {"hero_card"})
    community_cards = _build_cards(detections, ocr_results, BOARD_LABELS)
    available_actions = _build_actions(detections, ocr_results)

    pot_size = _extract_amount(ocr_results, POT_LABELS)
    hero_stack = _extract_amount(ocr_results, {"hero_stack", "stack_amount"})

    # Average detection confidence
    avg_conf = 0.0
    if detections:
        avg_conf = sum(d.confidence for d in detections) / len(detections)

    return GameState(
        timestamp=frame_result.timestamp,
        frame_id=frame_result.frame_id,
        game_phase=game_phase,
        schema_name=frame_result.schema_name,
        schema_confidence=frame_result.schema_confidence,
        is_hero_turn=hero_turn,
        hero_cards=hero_cards,
        community_cards=community_cards,
        pot_size=pot_size,
        hero_stack=hero_stack,
        players=[],
        available_actions=available_actions,
        capture_ms=frame_result.capture_ms,
        inference_ms=frame_result.inference_ms,
        ocr_ms=frame_result.ocr_ms,
        total_ms=frame_result.total_ms,
        raw_detections=len(detections),
        detection_confidence_avg=round(avg_conf, 3),
    )


def build_detection_map(
    frame_result: FrameResult,
    window_bounds: dict,
    retina_scale: float,
) -> DetectionMap:
    """Extract button/slider pixel coordinates from detections into a DetectionMap.

    This preserves the coordinate data that _build_actions() discards,
    enabling the actuator to know where to click.
    """
    detections = frame_result.detections
    ocr_results = frame_result.ocr_results
    ocr_by_idx = {ocr.detection_index: ocr for ocr in ocr_results}

    buttons: list[ButtonLocation] = []
    slider: SliderLocation | None = None

    for i, det in enumerate(detections):
        # Buttons
        if det.label in BUTTON_LABELS:
            ocr = ocr_by_idx.get(i)
            if ocr:
                action_name, amount = parse_button_text(ocr.raw_text)
            else:
                action_name = det.label.replace("_button", "")
                amount = None
            buttons.append(ButtonLocation(
                action=action_name,
                label=det.label,
                amount=amount,
                center_x=det.center_x,
                center_y=det.center_y,
                x_min=det.x_min,
                y_min=det.y_min,
                x_max=det.x_max,
                y_max=det.y_max,
                confidence=det.confidence,
            ))
        # Slider
        elif det.label == "slider":
            slider = SliderLocation(
                x_min=det.x_min,
                y_min=det.y_min,
                x_max=det.x_max,
                y_max=det.y_max,
                center_y=det.center_y,
            )

    return DetectionMap(
        frame_id=frame_result.frame_id,
        timestamp=frame_result.timestamp,
        window_left=window_bounds["left"],
        window_top=window_bounds["top"],
        window_width=window_bounds["width"],
        window_height=window_bounds["height"],
        retina_scale=retina_scale,
        buttons=buttons,
        slider=slider,
    )
