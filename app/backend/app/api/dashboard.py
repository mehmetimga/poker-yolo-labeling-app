from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import require_role, get_current_user
from ..database import get_db
from ..models.user import User
from ..models.image import ImageRecord
from ..models.annotation import Annotation
from ..models.auth_models import AuditLog, ImageAssignment
from ..repositories import audit_repo

router = APIRouter()

admin_only = require_role("admin")
reviewer_or_admin = require_role("admin", "reviewer")


@router.get("/projects/{project_id}/dashboard")
async def project_dashboard(
    project_id: int,
    _: User = Depends(reviewer_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """Per-user labeling/review stats for a project."""
    # Labeled counts per user
    labeled_stmt = (
        select(ImageRecord.labeled_by, func.count(ImageRecord.id))
        .where(ImageRecord.project_id == project_id, ImageRecord.labeled_by.isnot(None))
        .group_by(ImageRecord.labeled_by)
    )
    labeled_result = await db.execute(labeled_stmt)
    labeled_counts = {uid: cnt for uid, cnt in labeled_result.all()}

    # Reviewed counts per user
    reviewed_stmt = (
        select(ImageRecord.reviewed_by, func.count(ImageRecord.id))
        .where(ImageRecord.project_id == project_id, ImageRecord.reviewed_by.isnot(None))
        .group_by(ImageRecord.reviewed_by)
    )
    reviewed_result = await db.execute(reviewed_stmt)
    reviewed_counts = {uid: cnt for uid, cnt in reviewed_result.all()}

    # Approved/rejected counts
    approved_stmt = (
        select(func.count(ImageRecord.id))
        .where(ImageRecord.project_id == project_id, ImageRecord.review_status == "approved")
    )
    rejected_stmt = (
        select(func.count(ImageRecord.id))
        .where(ImageRecord.project_id == project_id, ImageRecord.review_status == "rejected")
    )
    approved = (await db.execute(approved_stmt)).scalar() or 0
    rejected = (await db.execute(rejected_stmt)).scalar() or 0

    # Total images
    total_stmt = select(func.count(ImageRecord.id)).where(ImageRecord.project_id == project_id)
    total = (await db.execute(total_stmt)).scalar() or 0

    # Get usernames
    user_ids = set(labeled_counts.keys()) | set(reviewed_counts.keys())
    users = {}
    if user_ids:
        user_stmt = select(User).where(User.id.in_(user_ids))
        user_result = await db.execute(user_stmt)
        for u in user_result.scalars():
            users[u.id] = u.username

    per_user = []
    for uid in user_ids:
        per_user.append({
            "user_id": uid,
            "username": users.get(uid, "unknown"),
            "labeled": labeled_counts.get(uid, 0),
            "reviewed": reviewed_counts.get(uid, 0),
        })

    return {
        "total_images": total,
        "approved": approved,
        "rejected": rejected,
        "per_user": per_user,
    }


@router.get("/users/me/progress")
async def my_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Current user's labeling/review stats across all projects."""
    labeled_stmt = (
        select(func.count(ImageRecord.id))
        .where(ImageRecord.labeled_by == current_user.id)
    )
    reviewed_stmt = (
        select(func.count(ImageRecord.id))
        .where(ImageRecord.reviewed_by == current_user.id)
    )
    assigned_stmt = (
        select(func.count(ImageAssignment.id))
        .where(ImageAssignment.user_id == current_user.id)
    )
    labeled = (await db.execute(labeled_stmt)).scalar() or 0
    reviewed = (await db.execute(reviewed_stmt)).scalar() or 0
    assigned = (await db.execute(assigned_stmt)).scalar() or 0

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "labeled": labeled,
        "reviewed": reviewed,
        "assigned": assigned,
    }


@router.get("/audit-log")
async def get_audit_log(
    _: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
    user_id: int | None = Query(None),
    action: str | None = Query(None),
    entity_type: str | None = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
):
    return await audit_repo.get_log(
        db, user_id=user_id, action=action,
        entity_type=entity_type, limit=limit, offset=offset,
    )
