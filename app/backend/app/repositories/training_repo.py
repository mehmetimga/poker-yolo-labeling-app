from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.training import TrainingRun, DatasetSplit


async def get_all(db: AsyncSession, project_id: int) -> list[TrainingRun]:
    stmt = (
        select(TrainingRun)
        .where(TrainingRun.project_id == project_id)
        .order_by(TrainingRun.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, run_id: int) -> TrainingRun | None:
    return await db.get(TrainingRun, run_id)


async def create(db: AsyncSession, **kwargs) -> TrainingRun:
    run = TrainingRun(**kwargs)
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def update(db: AsyncSession, run: TrainingRun, **kwargs) -> TrainingRun:
    for k, v in kwargs.items():
        setattr(run, k, v)
    await db.commit()
    await db.refresh(run)
    return run


async def create_splits(db: AsyncSession, run_id: int, splits: list[dict]) -> int:
    for s in splits:
        db.add(DatasetSplit(training_run_id=run_id, **s))
    await db.commit()
    return len(splits)


async def get_splits(db: AsyncSession, run_id: int) -> list[DatasetSplit]:
    stmt = select(DatasetSplit).where(DatasetSplit.training_run_id == run_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_split_summary(db: AsyncSession, run_id: int) -> dict:
    stmt = (
        select(DatasetSplit.split, func.count(DatasetSplit.id))
        .where(DatasetSplit.training_run_id == run_id)
        .group_by(DatasetSplit.split)
    )
    result = await db.execute(stmt)
    return {row[0]: row[1] for row in result.all()}
