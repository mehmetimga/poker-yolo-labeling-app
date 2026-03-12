from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..repositories import project_repo
from ..services.export_service import export_yolo, export_metadata

router = APIRouter()


@router.post("/projects/{project_id}/export/yolo")
async def export_yolo_endpoint(
    project_id: int,
    output_dir: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not output_dir:
        output_dir = str(Path(project.image_root_path).parent / "labels_yolo")

    try:
        result = await export_yolo(db, project_id, output_dir)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/export/metadata")
async def export_metadata_endpoint(
    project_id: int,
    output_dir: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not output_dir:
        output_dir = str(Path(project.image_root_path).parent / "metadata")

    try:
        result = await export_metadata(db, project_id, output_dir)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
