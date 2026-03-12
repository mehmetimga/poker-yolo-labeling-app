from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.image import ImageRecord
from ..models.annotation import Annotation


async def get_by_project(
    db: AsyncSession,
    project_id: int,
    status: str | None = None,
    schema: str | None = None,
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
    stmt = (
        stmt.group_by(ImageRecord.id)
        .order_by(ImageRecord.filename)
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
