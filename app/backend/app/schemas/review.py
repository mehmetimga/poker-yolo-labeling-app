from pydantic import BaseModel


class ReviewDecisionCreate(BaseModel):
    decision: str  # approved|rejected|needs_work
    comment: str


class AssignmentCreate(BaseModel):
    image_ids: list[int]
    user_id: int
