from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..config import load_schemas, load_taxonomy
from ..repositories import image_repo
from ..schemas.schema import SchemaScoreRequest, SchemaScoreResponse, SchemaMatchOut, SchemaAssign
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
