from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.auth_models import ReviewComment
from ..models.user import User


async def create_comment(db: AsyncSession, **kwargs) -> ReviewComment:
    comment = ReviewComment(**kwargs)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def get_by_image(db: AsyncSession, image_id: int) -> list[dict]:
    stmt = (
        select(ReviewComment, User.username)
        .join(User, ReviewComment.reviewer_id == User.id)
        .where(ReviewComment.image_id == image_id)
        .order_by(ReviewComment.created_at.desc())
    )
    result = await db.execute(stmt)
    return [
        {
            "id": comment.id,
            "image_id": comment.image_id,
            "reviewer_id": comment.reviewer_id,
            "reviewer_username": username,
            "comment": comment.comment,
            "decision": comment.decision,
            "created_at": comment.created_at.isoformat() if comment.created_at else None,
        }
        for comment, username in result.all()
    ]


async def get_review_stats(db: AsyncSession, project_id: int) -> list[dict]:
    from ..models.image import ImageRecord
    stmt = (
        select(
            ReviewComment.reviewer_id,
            User.username,
            ReviewComment.decision,
            func.count(ReviewComment.id),
        )
        .join(User, ReviewComment.reviewer_id == User.id)
        .join(ImageRecord, ReviewComment.image_id == ImageRecord.id)
        .where(ImageRecord.project_id == project_id)
        .group_by(ReviewComment.reviewer_id, User.username, ReviewComment.decision)
    )
    result = await db.execute(stmt)
    stats: dict[int, dict] = {}
    for reviewer_id, username, decision, count in result.all():
        if reviewer_id not in stats:
            stats[reviewer_id] = {"reviewer_id": reviewer_id, "username": username, "approved": 0, "rejected": 0, "needs_work": 0}
        stats[reviewer_id][decision] = count
    return list(stats.values())
