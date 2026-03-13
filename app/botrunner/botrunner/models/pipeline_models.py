from pydantic import BaseModel
import numpy as np


class Detection(BaseModel):
    label: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float

    model_config = {"arbitrary_types_allowed": True}

    @property
    def center_x(self) -> float:
        return (self.x_min + self.x_max) / 2

    @property
    def center_y(self) -> float:
        return (self.y_min + self.y_max) / 2

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        return self.y_max - self.y_min


class OCRResult(BaseModel):
    detection_index: int
    label: str
    raw_text: str
    parsed_value: str | float | None = None
    confidence: float


class FrameResult(BaseModel):
    """Result of processing a single frame through the pipeline."""
    frame_id: str
    timestamp: float
    detections: list[Detection] = []
    ocr_results: list[OCRResult] = []
    schema_name: str = "unknown"
    schema_confidence: float = 0.0
    capture_ms: float = 0.0
    inference_ms: float = 0.0
    ocr_ms: float = 0.0
    state_ms: float = 0.0
    total_ms: float = 0.0

    model_config = {"arbitrary_types_allowed": True}
