from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import get_current_user
from ..models.user import User
from ..services.batch_inference_service import get_task

router = APIRouter()


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str, _: User = Depends(get_current_user)):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
