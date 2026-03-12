from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.annotation import Annotation


async def get_by_image(db: AsyncSession, image_id: int) -> list[Annotation]:
    stmt = select(Annotation).where(Annotation.image_id == image_id).order_by(Annotation.id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def replace_all(db: AsyncSession, image_id: int, annotations: list[dict]) -> list[Annotation]:
    await db.execute(delete(Annotation).where(Annotation.image_id == image_id))

    created = []
    for ann_data in annotations:
        ann = Annotation(image_id=image_id, **ann_data)
        db.add(ann)
        created.append(ann)

    await db.commit()
    for ann in created:
        await db.refresh(ann)
    return created


async def delete_all_for_image(db: AsyncSession, image_id: int):
    await db.execute(delete(Annotation).where(Annotation.image_id == image_id))
    await db.commit()
