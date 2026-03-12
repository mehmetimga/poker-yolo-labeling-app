from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    image_root_path: str


class ProjectOut(BaseModel):
    id: int
    name: str
    description: str
    image_root_path: str
    taxonomy_version: int
    schema_version: int
    image_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
