from datetime import datetime

from pydantic import BaseModel


class ImageOut(BaseModel):
    id: int
    project_id: int
    filename: str
    filepath: str
    width: int
    height: int
    hash: str
    status: str
    assigned_schema: str | None
    suggested_schema: str | None
    schema_confidence: float | None
    review_status: str | None
    annotation_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ImageImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]


VALID_STATUSES = {"new", "in_progress", "labeled", "reviewed", "approved", "rejected", "pre_annotated"}


class ImageStatusUpdate(BaseModel):
    status: str

    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {v}. Must be one of {VALID_STATUSES}")
        return v

    model_config = {"validate_default": True}


class BatchStatusUpdate(BaseModel):
    image_ids: list[int]
    status: str


class BatchSchemaAssign(BaseModel):
    image_ids: list[int]
    schema_name: str
