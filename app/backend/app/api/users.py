from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import require_role, hash_password
from ..database import get_db
from ..models.user import User
from ..models.image import ImageRecord
from ..models.auth_models import ReviewComment
from ..repositories import user_repo
from ..schemas.user import UserCreate, UserOut, UserUpdate

router = APIRouter()

admin_only = require_role("admin")


@router.get("/users")
async def list_users(
    _: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    users = await user_repo.get_all(db)
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in users
    ]


@router.post("/users", response_model=UserOut)
async def create_user(
    body: UserCreate,
    _: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    if body.role not in ("admin", "reviewer", "labeler"):
        raise HTTPException(status_code=400, detail="Invalid role")
    existing = await user_repo.get_by_username(db, body.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    existing_email = await user_repo.get_by_email(db, body.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    user = await user_repo.create(
        db,
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    _: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    body: UserUpdate,
    _: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    updates = body.model_dump(exclude_unset=True)
    if "role" in updates and updates["role"] not in ("admin", "reviewer", "labeler"):
        raise HTTPException(status_code=400, detail="Invalid role")
    await user_repo.update(db, user, **updates)
    return {"message": "User updated"}


@router.get("/users/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    _: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    user = await user_repo.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Count labeled images (images where labeled_by = user_id)
    labeled_stmt = select(func.count(ImageRecord.id)).where(ImageRecord.labeled_by == user_id)
    labeled_result = await db.execute(labeled_stmt)
    labeled_count = labeled_result.scalar_one()

    # Count reviews
    review_stmt = select(ReviewComment.decision, func.count(ReviewComment.id)).where(
        ReviewComment.reviewer_id == user_id
    ).group_by(ReviewComment.decision)
    review_result = await db.execute(review_stmt)
    review_counts = {row[0]: row[1] for row in review_result.all()}

    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "labeled_count": labeled_count,
        "approved_count": review_counts.get("approved", 0),
        "rejected_count": review_counts.get("rejected", 0),
        "needs_work_count": review_counts.get("needs_work", 0),
    }
