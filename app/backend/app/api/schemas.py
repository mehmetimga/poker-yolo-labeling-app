from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..config import load_schemas, load_taxonomy
from ..models.image import ImageRecord
from ..models.annotation import Annotation
from ..repositories import image_repo
from ..schemas.schema import SchemaScoreRequest, SchemaScoreResponse, SchemaMatchOut, SchemaAssign
from ..schemas.annotation import AnnotationOut
from ..services.schema_service import score_schemas

router = APIRouter()


@router.get("")
async def list_schemas():
    schemas_config = load_schemas()
    return schemas_config


@router.get("/taxonomy")
async def get_taxonomy():
    return load_taxonomy()


@router.post("/score", response_model=SchemaScoreResponse)
async def score(body: SchemaScoreRequest, db: AsyncSession = Depends(get_db)):
    try:
        results = await score_schemas(db, body.image_id)
        return SchemaScoreResponse(
            top_matches=[SchemaMatchOut(**r) for r in results[:10]]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/images/{image_id}/schema")
async def assign_schema(
    image_id: int, body: SchemaAssign, db: AsyncSession = Depends(get_db)
):
    image = await image_repo.get_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.assigned_schema = body.schema_name
    await db.commit()
    return {"status": "ok", "assigned_schema": body.schema_name}


@router.get("/templates/{schema_name}", response_model=list[AnnotationOut])
async def get_schema_template(schema_name: str, db: AsyncSession = Depends(get_db)):
    """Get annotations from the most recently labeled image with this schema as a template."""
    # Find the most recent image with this schema that has annotations
    stmt = (
        select(ImageRecord)
        .where(ImageRecord.assigned_schema == schema_name)
        .order_by(ImageRecord.updated_at.desc())
        .limit(10)
    )
    result = await db.execute(stmt)
    images = result.scalars().all()

    for img in images:
        ann_stmt = select(Annotation).where(Annotation.image_id == img.id).order_by(Annotation.id)
        ann_result = await db.execute(ann_stmt)
        annotations = list(ann_result.scalars().all())
        if annotations:
            return annotations

    raise HTTPException(status_code=404, detail=f"No template found for schema '{schema_name}'")
