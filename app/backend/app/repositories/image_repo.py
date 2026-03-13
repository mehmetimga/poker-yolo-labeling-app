from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.image import ImageRecord
from ..models.annotation import Annotation


async def get_by_project(
    db: AsyncSession,
    project_id: int,
    status: str | None = None,
    schema: str | None = None,
    sort: str = "filename",
    limit: int = 500,
    offset: int = 0,
) -> list[tuple[ImageRecord, int]]:
    stmt = (
        select(ImageRecord, func.count(Annotation.id).label("annotation_count"))
        .outerjoin(Annotation)
        .where(ImageRecord.project_id == project_id)
    )
    if status:
        stmt = stmt.where(ImageRecord.status == status)
    if schema:
        stmt = stmt.where(ImageRecord.assigned_schema == schema)

    # Sort options
    if sort == "confidence_asc":
        order = ImageRecord.schema_confidence.asc().nullslast()
    elif sort == "confidence_desc":
        order = ImageRecord.schema_confidence.desc().nullsfirst()
    elif sort == "created_at":
        order = ImageRecord.created_at.desc()
    else:
        order = ImageRecord.filename

    stmt = (
        stmt.group_by(ImageRecord.id)
        .order_by(order)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)
    return result.all()


async def get_by_id(db: AsyncSession, image_id: int) -> ImageRecord | None:
    return await db.get(ImageRecord, image_id)


async def get_by_hash(db: AsyncSession, project_id: int, hash_val: str) -> ImageRecord | None:
    stmt = select(ImageRecord).where(
        ImageRecord.project_id == project_id, ImageRecord.hash == hash_val
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create(db: AsyncSession, **kwargs) -> ImageRecord:
    image = ImageRecord(**kwargs)
    db.add(image)
    return image


async def bulk_flush(db: AsyncSession):
    await db.commit()


async def update_status(db: AsyncSession, image_id: int, status: str) -> ImageRecord | None:
    image = await db.get(ImageRecord, image_id)
    if not image:
        return None
    image.status = status
    await db.commit()
    await db.refresh(image)
    return image


async def batch_update_status(db: AsyncSession, image_ids: list[int], status: str) -> int:
    stmt = update(ImageRecord).where(ImageRecord.id.in_(image_ids)).values(status=status)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


async def batch_update_schema(db: AsyncSession, image_ids: list[int], schema_name: str) -> int:
    stmt = update(ImageRecord).where(ImageRecord.id.in_(image_ids)).values(assigned_schema=schema_name)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount
