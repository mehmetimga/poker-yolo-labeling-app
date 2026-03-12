from datetime import datetime

from pydantic import BaseModel


class AnnotationCreate(BaseModel):
    label: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    source: str = "manual"
    confidence: float | None = None


class AnnotationOut(BaseModel):
    id: int
    image_id: int
    label: str
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    normalized_x_center: float
    normalized_y_center: float
    normalized_width: float
    normalized_height: float
    source: str
    confidence: float | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnnotationsBulkSave(BaseModel):
    annotations: list[AnnotationCreate]
