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
