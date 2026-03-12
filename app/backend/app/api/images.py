from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..repositories import image_repo
from ..schemas.image import ImageOut, ImageStatusUpdate, BatchStatusUpdate, BatchSchemaAssign
from ..schemas.annotation import AnnotationCreate
from ..services import inference_service

router = APIRouter()


@router.get("/projects/{project_id}/images", response_model=list[ImageOut])
async def list_images(
    project_id: int,
    status: str | None = Query(None),
    schema: str | None = Query(None),
    limit: int = Query(500, le=2000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    rows = await image_repo.get_by_project(
        db, project_id, status=status, schema=schema, limit=limit, offset=offset
    )
    result = []
    for image, annotation_count in rows:
        out = ImageOut.model_validate(image)
        out.annotation_count = annotation_count
        result.append(out)
    return result


@router.get("/images/{image_id}", response_model=ImageOut)
async def get_image(image_id: int, db: AsyncSession = Depends(get_db)):
    image = await image_repo.get_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    out = ImageOut.model_validate(image)
    return out


@router.get("/images/{image_id}/file")
async def get_image_file(image_id: int, db: AsyncSession = Depends(get_db)):
    image = await image_repo.get_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    filepath = Path(image.filepath)
    if not filepath.is_file():
        # Try resolving relative to images_dir as fallback
        filepath = settings.images_dir / image.filepath
    if not filepath.is_file():
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    suffix = filepath.suffix.lower()
    media_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    return FileResponse(filepath, media_type=media_types.get(suffix, "image/png"))


@router.patch("/images/{image_id}/status", response_model=ImageOut)
async def update_image_status(
    image_id: int,
    body: ImageStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    image = await image_repo.update_status(db, image_id, body.status)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return ImageOut.model_validate(image)


@router.patch("/projects/{project_id}/images/batch-status")
async def batch_update_status(
    project_id: int,
    body: BatchStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    count = await image_repo.batch_update_status(db, body.image_ids, body.status)
    return {"updated": count}


@router.post("/projects/{project_id}/images/batch-schema")
async def batch_assign_schema(
    project_id: int,
    body: BatchSchemaAssign,
    db: AsyncSession = Depends(get_db),
):
    count = await image_repo.batch_update_schema(db, body.image_ids, body.schema_name)
    return {"updated": count}


@router.post("/images/{image_id}/infer", response_model=list[AnnotationCreate])
async def run_inference(image_id: int, db: AsyncSession = Depends(get_db)):
    if not settings.yolo_model_path:
        raise HTTPException(status_code=404, detail="No YOLO model configured. Set LABELING_YOLO_MODEL_PATH.")
    image = await image_repo.get_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    filepath = Path(image.filepath)
    if not filepath.is_file():
        filepath = settings.images_dir / image.filepath
    if not filepath.is_file():
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    try:
        detections = inference_service.run_inference(
            str(filepath), settings.yolo_model_path, settings.yolo_confidence_threshold
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return detections
