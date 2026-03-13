from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.dependencies import require_role, get_current_user
from ..database import get_db
from ..models.user import User
from ..repositories import assignment_repo, audit_repo, image_repo
from ..schemas.review import AssignmentCreate

router = APIRouter()

admin_only = require_role("admin")


@router.post("/projects/{project_id}/assignments")
async def assign_images(
    project_id: int,
    body: AssignmentCreate,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    """Assign a batch of images to a labeler."""
    count = await assignment_repo.assign_batch(
        db,
        image_ids=body.image_ids,
        user_id=body.user_id,
        assigned_by=current_user.id,
    )
    await audit_repo.log_action(
        db, current_user.id, "assign", "image", body.user_id,
        f'{{"image_count":{count},"project_id":{project_id}}}'
    )
    return {"assigned": count}


@router.get("/projects/{project_id}/assignments")
async def list_project_assignments(
    project_id: int,
    _: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    return await assignment_repo.get_by_project(db, project_id)


@router.get("/users/me/assignments")
async def my_assignments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await assignment_repo.get_by_user(db, current_user.id)


@router.delete("/images/{image_id}/assignments/{user_id}")
async def unassign_image(
    image_id: int,
    user_id: int,
    current_user: User = Depends(admin_only),
    db: AsyncSession = Depends(get_db),
):
    deleted = await assignment_repo.unassign(db, image_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"deleted": True}
