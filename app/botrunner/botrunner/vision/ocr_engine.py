import logging

import numpy as np
from PIL import Image

from ..models.pipeline_models import Detection, OCRResult

logger = logging.getLogger(__name__)

try:
    import easyocr
    _EASYOCR_AVAILABLE = True
except ImportError:
    _EASYOCR_AVAILABLE = False

_reader = None

# Labels that contain readable text worth OCR-ing
OCR_LABELS = {
    "hero_card", "board_card", "opponent_card",
    "pot_amount", "stack_amount", "bet_amount",
    "call_button", "raise_button", "bet_button",
    "blinds_label",
}


def init_ocr(gpu: bool = False, languages: list[str] | None = None):
    global _reader
    if not _EASYOCR_AVAILABLE:
        logger.warning("easyocr is not installed — OCR disabled")
        return
    langs = languages or ["en"]
    logger.info(f"Initializing EasyOCR (gpu={gpu}, langs={langs})")
    _reader = easyocr.Reader(langs, gpu=gpu)


def run_ocr(
    image: np.ndarray,
    detections: list[Detection],
    padding: int = 4,
) -> list[OCRResult]:
    """Run OCR on bounding boxes of text-bearing labels."""
    if _reader is None:
        return []

    results = []
    h, w = image.shape[:2]

    for i, det in enumerate(detections):
        if det.label not in OCR_LABELS:
            continue

        # Crop with padding
        x1 = max(0, int(det.x_min) - padding)
        y1 = max(0, int(det.y_min) - padding)
        x2 = min(w, int(det.x_max) + padding)
        y2 = min(h, int(det.y_max) + padding)

        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        try:
            ocr_output = _reader.readtext(crop, detail=1)
            if ocr_output:
                # Concatenate all text segments
                raw_text = " ".join(seg[1] for seg in ocr_output)
                avg_conf = sum(seg[2] for seg in ocr_output) / len(ocr_output)
                results.append(OCRResult(
                    detection_index=i,
                    label=det.label,
                    raw_text=raw_text.strip(),
                    confidence=round(avg_conf, 3),
                ))
        except Exception as e:
            logger.debug(f"OCR failed for detection {i} ({det.label}): {e}")

    return results
