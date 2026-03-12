from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..repositories import annotation_repo
from ..schemas.annotation import AnnotationOut, AnnotationsBulkSave
from ..services.annotation_service import save_annotations

router = APIRouter()


@router.get("/images/{image_id}/annotations", response_model=list[AnnotationOut])
async def get_annotations(image_id: int, db: AsyncSession = Depends(get_db)):
    annotations = await annotation_repo.get_by_image(db, image_id)
    return [AnnotationOut.model_validate(a) for a in annotations]


@router.put("/images/{image_id}/annotations", response_model=list[AnnotationOut])
async def save_annotations_endpoint(
    image_id: int, body: AnnotationsBulkSave, db: AsyncSession = Depends(get_db)
):
    try:
        saved = await save_annotations(db, image_id, body.annotations)
        return [AnnotationOut.model_validate(a) for a in saved]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/images/{image_id}/annotations/autosave", response_model=list[AnnotationOut])
async def autosave_annotations(
    image_id: int, body: AnnotationsBulkSave, db: AsyncSession = Depends(get_db)
):
    try:
        saved = await save_annotations(db, image_id, body.annotations)
        return [AnnotationOut.model_validate(a) for a in saved]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
