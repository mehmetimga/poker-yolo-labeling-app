from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import require_role, get_current_user
from ..database import get_db
from ..models.user import User
from ..models.image import ImageRecord
from ..models.annotation import Annotation
from ..repositories import review_repo, audit_repo, image_repo
from ..schemas.review import ReviewDecisionCreate

router = APIRouter()

reviewer_or_admin = require_role("admin", "reviewer")


@router.get("/projects/{project_id}/review-queue")
async def get_review_queue(
    project_id: int,
    _: User = Depends(reviewer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get images with status 'labeled' awaiting review."""
    stmt = (
        select(ImageRecord, func.count(Annotation.id).label("ann_count"))
        .outerjoin(Annotation)
        .where(ImageRecord.project_id == project_id, ImageRecord.status == "labeled")
        .group_by(ImageRecord.id)
        .order_by(ImageRecord.updated_at.desc())
    )
    result = await db.execute(stmt)
    items = []
    for image, ann_count in result.all():
        items.append({
            "id": image.id,
            "filename": image.filename,
            "status": image.status,
            "assigned_schema": image.assigned_schema,
            "annotation_count": ann_count,
            "labeled_by": image.labeled_by,
            "updated_at": image.updated_at.isoformat() if image.updated_at else None,
        })
    return items


@router.post("/images/{image_id}/review")
async def submit_review(
    image_id: int,
    body: ReviewDecisionCreate,
    current_user: User = Depends(reviewer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    if body.decision not in ("approved", "rejected", "needs_work"):
        raise HTTPException(status_code=400, detail="Invalid decision")

    image = await image_repo.get_by_id(db, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    # Create review comment
    await review_repo.create_comment(
        db,
        image_id=image_id,
        reviewer_id=current_user.id,
        comment=body.comment,
        decision=body.decision,
    )

    # Update image status
    new_status = body.decision if body.decision in ("approved", "rejected") else "labeled"
    image.status = new_status
    image.review_status = body.decision
    image.reviewed_by = current_user.id
    from datetime import datetime
    image.reviewed_at = datetime.utcnow()
    await db.commit()

    # Audit log
    await audit_repo.log_action(
        db, current_user.id, body.decision, "image", image_id,
        f'{{"comment":"{body.comment[:200]}"}}'
    )

    return {"message": f"Image {body.decision}", "status": new_status}


@router.get("/images/{image_id}/review-comments")
async def get_review_comments(
    image_id: int,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await review_repo.get_by_image(db, image_id)


@router.get("/projects/{project_id}/review-stats")
async def get_review_stats(
    project_id: int,
    _: User = Depends(reviewer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    return await review_repo.get_review_stats(db, project_id)
