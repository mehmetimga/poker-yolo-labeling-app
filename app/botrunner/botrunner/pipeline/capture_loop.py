"""Main async loop: capture → dedup → detect → classify → OCR → game state → buffer."""

import asyncio
import logging
import time
import uuid
from collections import deque
from statistics import mean, quantiles

from ..capture.frame_dedup import FrameDedup
from ..capture.screen_capture import capture_screen, get_window_bounds
from ..config import settings
from ..engine.game_state import assemble_game_state, build_detection_map
from ..models.pipeline_models import FrameResult
from ..vision.detector import detect
from ..vision.ocr_engine import init_ocr, run_ocr
from ..vision.schema_classifier import classify_schema
from .detection_map_buffer import detection_map_buffer
from .state_buffer import state_buffer

logger = logging.getLogger(__name__)


class PipelineManager:
    def __init__(self):
        self._task: asyncio.Task | None = None
        self._running = False
        self._dedup = FrameDedup(threshold=settings.phash_threshold)
        self._frames_processed = 0
        self._frames_skipped = 0
        self._latency_history: deque[dict] = deque(maxlen=200)

    def is_running(self) -> bool:
        return self._running

    async def start(self):
        if self._running:
            return
        # Initialize OCR
        langs = [l.strip() for l in settings.ocr_languages.split(",")]
        init_ocr(gpu=settings.ocr_gpu, languages=langs)
        self._running = True
        self._dedup.reset()
        self._task = asyncio.create_task(self._loop())
        logger.info("Pipeline started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        logger.info("Pipeline stopped")

    async def _loop(self):
        interval = settings.capture_interval_ms / 1000.0
        while self._running:
            try:
                await self._process_frame()
            except Exception:
                logger.exception("Pipeline frame error")
            await asyncio.sleep(interval)

    async def _process_frame(self):
        t_start = time.perf_counter()

        # 1. Capture
        t0 = time.perf_counter()
        result = capture_screen(settings.window_title, settings.capture_region)
        if result is None:
            return
        np_image, pil_image = result
        capture_ms = (time.perf_counter() - t0) * 1000

        # Get window bounds for coordinate conversion (actuator needs this)
        window_bounds = get_window_bounds(settings.window_title)

        # 2. Dedup
        if self._dedup.is_duplicate(pil_image):
            self._frames_skipped += 1
            return

        frame_id = uuid.uuid4().hex[:12]
        h, w = np_image.shape[:2]

        # 3. YOLO detection
        t0 = time.perf_counter()
        if not settings.yolo_model_path:
            logger.warning("No YOLO model configured (BOT_YOLO_MODEL_PATH)")
            return
        detections = detect(np_image, settings.yolo_model_path, settings.yolo_confidence)
        inference_ms = (time.perf_counter() - t0) * 1000

        # 4. Schema classification
        schema_name, schema_conf = classify_schema(detections, w, h)

        # 5. OCR on text-bearing detections
        t0 = time.perf_counter()
        ocr_results = run_ocr(np_image, detections)
        ocr_ms = (time.perf_counter() - t0) * 1000

        total_ms = (time.perf_counter() - t_start) * 1000

        # 6. Build FrameResult
        frame_result = FrameResult(
            frame_id=frame_id,
            timestamp=time.time(),
            detections=detections,
            ocr_results=ocr_results,
            schema_name=schema_name,
            schema_confidence=schema_conf,
            capture_ms=round(capture_ms, 1),
            inference_ms=round(inference_ms, 1),
            ocr_ms=round(ocr_ms, 1),
            total_ms=round(total_ms, 1),
        )

        # 7. Assemble GameState
        game_state = assemble_game_state(frame_result)

        # 7b. Build DetectionMap for actuator (retains button pixel coords)
        if window_bounds:
            retina_scale = w / window_bounds["width"] if window_bounds["width"] > 0 else 1.0
            dmap = build_detection_map(frame_result, window_bounds, retina_scale)
            detection_map_buffer.update(dmap)

        # 8. Gate: only emit if confidence is above threshold
        if game_state.schema_confidence >= settings.confidence_gate:
            state_buffer.update(game_state)

        self._frames_processed += 1
        self._latency_history.append({
            "capture_ms": capture_ms,
            "inference_ms": inference_ms,
            "ocr_ms": ocr_ms,
            "total_ms": total_ms,
        })

    def get_status(self) -> dict:
        return {
            "running": self._running,
            "frames_processed": self._frames_processed,
            "frames_skipped": self._frames_skipped,
            "model_path": settings.yolo_model_path or None,
            "capture_interval_ms": settings.capture_interval_ms,
        }

    def get_metrics(self) -> dict:
        if not self._latency_history:
            return {"frames_processed": 0, "stages": {}}

        def _stats(values: list[float]) -> dict:
            if not values:
                return {}
            sorted_vals = sorted(values)
            qs = quantiles(sorted_vals, n=100) if len(sorted_vals) >= 2 else sorted_vals
            return {
                "avg": round(mean(values), 1),
                "p50": round(qs[49] if len(qs) > 49 else sorted_vals[len(sorted_vals) // 2], 1),
                "p95": round(qs[94] if len(qs) > 94 else sorted_vals[-1], 1),
                "p99": round(qs[98] if len(qs) > 98 else sorted_vals[-1], 1),
            }

        history = list(self._latency_history)
        return {
            "frames_processed": self._frames_processed,
            "frames_skipped": self._frames_skipped,
            "stages": {
                "capture": _stats([h["capture_ms"] for h in history]),
                "inference": _stats([h["inference_ms"] for h in history]),
                "ocr": _stats([h["ocr_ms"] for h in history]),
                "total": _stats([h["total_ms"] for h in history]),
            },
        }


pipeline_manager = PipelineManager()
