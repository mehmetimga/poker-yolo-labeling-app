import asyncio
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from jose import JWTError, jwt as jose_jwt

from ..config import settings
from ..database import get_db
from ..auth.dependencies import get_current_user, require_role, oauth2_scheme_optional
from ..models.user import User
from ..repositories import image_repo, user_repo
from ..schemas.image import ImageOut, ImageStatusUpdate, BatchStatusUpdate, BatchSchemaAssign
from ..schemas.annotation import AnnotationCreate
from ..services import inference_service
from ..services.batch_inference_service import create_task, run_batch_inference

router = APIRouter()

admin_only = require_role("admin")


class BatchInferRequest(BaseModel):
    image_ids: list[int] | None = None
    confidence: float | None = None


@router.get("/projects/{project_id}/images", response_model=list[ImageOut])
async def list_images(
    project_id: int,
    status: str | None = Query(None),
    schema: str | None = Query(None),
    sort: str = Query("filename"),
    limit: int = Query(500, le=2000),
    offset: int = Query(0, ge=0),
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await image_repo.get_by_project(
        db, project_id, status=status, schema=schema, sort=sort, limit=limit, offset=offset
    )
    result = []
    for image, annotation_count in rows:
        out = ImageOut.model_validate(image)
        out.annotation_count = annotation_count
        result.append(out)
    return result


@router.get("/images/{image_id}", response_model=ImageOut)
async def get_image(image_id: int, _: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    image = await image_repo.get_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    out = ImageOut.model_validate(image)
    return out


@router.get("/images/{image_id}/file")
async def get_image_file(
    image_id: int,
    token: str | None = Query(None),
    bearer: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
):
    # Accept auth via query param ?token= (for <img> tags) or Authorization header
    auth_token = bearer or token
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        payload = jose_jwt.decode(auth_token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        uid = payload.get("sub")
        if uid is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await user_repo.get_by_id(db, int(uid))
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    image = await image_repo.get_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    filepath = resolve_image_path(image.filepath)
    if filepath is None:
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    suffix = filepath.suffix.lower()
    media_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    return FileResponse(filepath, media_type=media_types.get(suffix, "image/png"))


def resolve_image_path(stored_path: str) -> Path | None:
    """Resolve a stored filepath to an actual file on disk.

    Handles Docker paths (/app/datasets/...) by stripping the container
    prefix and resolving relative to images_dir.
    """
    # 1. Try as-is (absolute path on current machine)
    fp = Path(stored_path)
    if fp.is_file():
        return fp

    # 2. Try relative to images_dir
    fp = settings.images_dir / stored_path
    if fp.is_file():
        return fp

    # 3. Strip Docker container prefixes and retry
    docker_prefixes = ["/app/datasets/", "/app/", "/data/"]
    for prefix in docker_prefixes:
        if stored_path.startswith(prefix):
            relative = stored_path[len(prefix):]
            fp = settings.images_dir / relative
            if fp.is_file():
                return fp

    # 4. Last resort: find by filename anywhere in images_dir
    filename = Path(stored_path).name
    for candidate in settings.images_dir.rglob(filename):
        if candidate.is_file():
            return candidate

    return None


@router.patch("/images/{image_id}/status", response_model=ImageOut)
async def update_image_status(
    image_id: int,
    body: ImageStatusUpdate,
    _: User = Depends(get_current_user),
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
    _: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    count = await image_repo.batch_update_status(db, body.image_ids, body.status)
    return {"updated": count}


@router.post("/projects/{project_id}/images/batch-schema")
async def batch_assign_schema(
    project_id: int,
    body: BatchSchemaAssign,
    _: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    count = await image_repo.batch_update_schema(db, body.image_ids, body.schema_name)
    return {"updated": count}


@router.post("/images/{image_id}/infer", response_model=list[AnnotationCreate])
async def run_inference(image_id: int, _: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not settings.yolo_model_path:
        raise HTTPException(status_code=404, detail="No YOLO model configured. Set LABELING_YOLO_MODEL_PATH.")
    image = await image_repo.get_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    filepath = resolve_image_path(image.filepath)
    if filepath is None:
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


@router.post("/projects/{project_id}/batch-infer")
async def batch_infer(
    project_id: int,
    body: BatchInferRequest | None = None,
    _: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    if not settings.yolo_model_path:
        raise HTTPException(status_code=404, detail="No YOLO model configured. Set LABELING_YOLO_MODEL_PATH.")

    confidence = (body.confidence if body and body.confidence else None) or settings.yolo_confidence_threshold

    if body and body.image_ids:
        image_ids = body.image_ids
    else:
        # Select all "new" images in the project
        rows = await image_repo.get_by_project(db, project_id, status="new", limit=2000)
        image_ids = [image.id for image, _ in rows]

    if not image_ids:
        return {"task_id": None, "total_images": 0, "message": "No images to process"}

    task_id = create_task(project_id, len(image_ids))
    asyncio.create_task(
        run_batch_inference(task_id, image_ids, settings.yolo_model_path, confidence)
    )
    return {"task_id": task_id, "total_images": len(image_ids)}
