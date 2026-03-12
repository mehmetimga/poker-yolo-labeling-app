from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..repositories import image_repo
from ..schemas.image import ImageOut

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
