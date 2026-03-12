from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..repositories import project_repo
from ..schemas.project import ProjectCreate, ProjectOut
from ..schemas.image import ImageImportResult
from ..services.image_service import import_images_from_folder, IMAGE_EXTENSIONS

router = APIRouter()


@router.get("", response_model=list[ProjectOut])
async def list_projects(db: AsyncSession = Depends(get_db)):
    rows = await project_repo.get_all(db)
    result = []
    for project, image_count in rows:
        out = ProjectOut.model_validate(project)
        out.image_count = image_count
        result.append(out)
    return result


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    # Auto-create the image directory
    image_dir = settings.resolve_image_path(body.image_root_path)
    image_dir.mkdir(parents=True, exist_ok=True)

    project = await project_repo.create(
        db, name=body.name, description=body.description, image_root_path=body.image_root_path
    )
    out = ProjectOut.model_validate(project)
    out.image_count = 0
    return out


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    image_count = await project_repo.get_image_count(db, project_id)
    out = ProjectOut.model_validate(project)
    out.image_count = image_count
    return out


@router.post("/{project_id}/upload-images", response_model=ImageImportResult)
async def upload_images(
    project_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload image files, save to project's image directory, then import them."""
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    image_dir = settings.resolve_image_path(project.image_root_path)
    image_dir.mkdir(parents=True, exist_ok=True)

    saved = 0
    skipped_files = 0
    for f in files:
        from pathlib import Path
        suffix = Path(f.filename or "").suffix.lower()
        if suffix not in IMAGE_EXTENSIONS:
            skipped_files += 1
            continue
        dest = image_dir / f.filename
        if dest.exists():
            skipped_files += 1
            continue
        content = await f.read()
        dest.write_bytes(content)
        saved += 1

    # Now import the saved files into the database
    result = await import_images_from_folder(db, project_id, project.image_root_path)
    result["uploaded"] = saved
    return result


@router.post("/{project_id}/import-images", response_model=ImageImportResult)
async def import_images(project_id: int, db: AsyncSession = Depends(get_db)):
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    result = await import_images_from_folder(db, project_id, project.image_root_path)
    return result
