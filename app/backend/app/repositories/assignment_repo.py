from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.auth_models import ImageAssignment


async def assign_batch(
    db: AsyncSession,
    image_ids: list[int],
    user_id: int,
    assigned_by: int,
) -> int:
    count = 0
    for image_id in image_ids:
        # Check if already assigned
        stmt = select(ImageAssignment).where(
            ImageAssignment.image_id == image_id,
            ImageAssignment.user_id == user_id,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            continue
        db.add(ImageAssignment(image_id=image_id, user_id=user_id, assigned_by=assigned_by))
        count += 1
    await db.commit()
    return count


async def get_by_project(db: AsyncSession, project_id: int) -> list[ImageAssignment]:
    from ..models.image import ImageRecord
    stmt = (
        select(ImageAssignment)
        .join(ImageRecord, ImageAssignment.image_id == ImageRecord.id)
        .where(ImageRecord.project_id == project_id)
        .order_by(ImageAssignment.assigned_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_by_user(db: AsyncSession, user_id: int, project_id: int | None = None) -> list[ImageAssignment]:
    from ..models.image import ImageRecord
    stmt = select(ImageAssignment).where(ImageAssignment.user_id == user_id)
    if project_id is not None:
        stmt = stmt.join(ImageRecord, ImageAssignment.image_id == ImageRecord.id).where(
            ImageRecord.project_id == project_id
        )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_assigned_image_ids(db: AsyncSession, user_id: int, project_id: int) -> set[int]:
    from ..models.image import ImageRecord
    stmt = (
        select(ImageAssignment.image_id)
        .join(ImageRecord, ImageAssignment.image_id == ImageRecord.id)
        .where(ImageAssignment.user_id == user_id, ImageRecord.project_id == project_id)
    )
    result = await db.execute(stmt)
    return {row[0] for row in result.all()}


async def unassign(db: AsyncSession, image_id: int, user_id: int) -> bool:
    stmt = delete(ImageAssignment).where(
        ImageAssignment.image_id == image_id,
        ImageAssignment.user_id == user_id,
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0
