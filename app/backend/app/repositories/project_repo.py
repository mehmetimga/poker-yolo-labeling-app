from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.project import Project
from ..models.image import ImageRecord


async def get_all(db: AsyncSession) -> list[tuple[Project, int]]:
    stmt = (
        select(Project, func.count(ImageRecord.id).label("image_count"))
        .outerjoin(ImageRecord)
        .group_by(Project.id)
        .order_by(Project.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.all()


async def get_by_id(db: AsyncSession, project_id: int) -> Project | None:
    return await db.get(Project, project_id)


async def create(db: AsyncSession, name: str, description: str, image_root_path: str) -> Project:
    project = Project(name=name, description=description, image_root_path=image_root_path)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_image_count(db: AsyncSession, project_id: int) -> int:
    stmt = select(func.count()).where(ImageRecord.project_id == project_id)
    result = await db.execute(stmt)
    return result.scalar() or 0
