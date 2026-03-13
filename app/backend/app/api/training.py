import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..repositories import training_repo
from ..services import training_service

router = APIRouter()


# ─── Request / Response schemas ────────────────────────────────────


class CreateRunRequest(BaseModel):
    name: str
    base_model: str = "yolov8n.pt"
    epochs: int = 100
    batch_size: int = 16
    img_size: int = 640
    learning_rate: float = 0.01
    train_ratio: float = 0.7
    val_ratio: float = 0.2
    test_ratio: float = 0.1


class TrainingRunResponse(BaseModel):
    id: int
    project_id: int
    name: str
    status: str
    model_path: str | None
    base_model: str
    epochs: int
    batch_size: int
    img_size: int
    learning_rate: float
    train_count: int
    val_count: int
    test_count: int
    split_ratio: str
    metrics: dict | None = None
    evaluation: dict | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


def _run_to_response(run) -> dict:
    metrics = None
    if run.metrics_json:
        try:
            metrics = json.loads(run.metrics_json)
        except json.JSONDecodeError:
            pass

    evaluation = None
    if run.eval_json:
        try:
            evaluation = json.loads(run.eval_json)
        except json.JSONDecodeError:
            pass

    return {
        "id": run.id,
        "project_id": run.project_id,
        "name": run.name,
        "status": run.status,
        "model_path": run.model_path,
        "base_model": run.base_model,
        "epochs": run.epochs,
        "batch_size": run.batch_size,
        "img_size": run.img_size,
        "learning_rate": run.learning_rate,
        "train_count": run.train_count,
        "val_count": run.val_count,
        "test_count": run.test_count,
        "split_ratio": run.split_ratio,
        "metrics": metrics,
        "evaluation": evaluation,
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
    }


# ─── Endpoints ─────────────────────────────────────────────────────


@router.get("/projects/{project_id}/training-runs")
async def list_runs(project_id: int, db: AsyncSession = Depends(get_db)):
    runs = await training_repo.get_all(db, project_id)
    return [_run_to_response(r) for r in runs]


@router.get("/training-runs/{run_id}")
async def get_run(run_id: int, db: AsyncSession = Depends(get_db)):
    run = await training_repo.get_by_id(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")
    return _run_to_response(run)


@router.get("/training-runs/{run_id}/status")
async def get_run_live_status(run_id: int, db: AsyncSession = Depends(get_db)):
    """Get live training status (in-memory, more granular than DB status)."""
    live = training_service.get_training_status(run_id)
    run = await training_repo.get_by_id(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")
    return {
        "run_id": run_id,
        "db_status": run.status,
        "live_status": live["status"] if live else run.status,
        "progress": live["progress"] if live else None,
    }


@router.post("/projects/{project_id}/training-runs")
async def create_run(
    project_id: int,
    body: CreateRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a training run, split the dataset, and kick off training."""
    split_ratio = f"{int(body.train_ratio*100)}/{int(body.val_ratio*100)}/{int(body.test_ratio*100)}"

    run = await training_repo.create(
        db,
        project_id=project_id,
        name=body.name,
        base_model=body.base_model,
        epochs=body.epochs,
        batch_size=body.batch_size,
        img_size=body.img_size,
        learning_rate=body.learning_rate,
        split_ratio=split_ratio,
        status="pending",
    )

    # Create stratified dataset split
    counts = await training_service.create_stratified_split(
        db, project_id, run.id,
        train_ratio=body.train_ratio,
        val_ratio=body.val_ratio,
        test_ratio=body.test_ratio,
    )

    await training_repo.update(
        db, run,
        train_count=counts["train"],
        val_count=counts["val"],
        test_count=counts["test"],
    )

    total = counts["train"] + counts["val"] + counts["test"]
    if total == 0:
        await training_repo.update(db, run, status="failed", error_message="No labeled images to train on")
        raise HTTPException(status_code=400, detail="No labeled images found. Label some images first.")

    # Launch training pipeline in background
    asyncio.create_task(training_service.run_training_pipeline(run.id))

    return _run_to_response(run)


@router.get("/training-runs/{run_id}/splits")
async def get_splits(run_id: int, db: AsyncSession = Depends(get_db)):
    """Get split summary and per-image split assignments."""
    run = await training_repo.get_by_id(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")

    summary = await training_repo.get_split_summary(db, run_id)
    splits = await training_repo.get_splits(db, run_id)

    return {
        "summary": summary,
        "images": [{"image_id": s.image_id, "split": s.split} for s in splits],
    }


@router.get("/training-runs/{run_id}/errors")
async def get_error_mining(run_id: int, db: AsyncSession = Depends(get_db)):
    """Get error mining results (images where model diverges from ground truth)."""
    run = await training_repo.get_by_id(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")

    if not run.eval_json:
        return {"errors": [], "message": "No evaluation data yet"}

    eval_data = json.loads(run.eval_json)
    return {
        "errors": eval_data.get("error_mining", []),
        "total_evaluated": run.val_count + run.test_count,
    }


@router.get("/training-runs/{run_id}/compare/{other_run_id}")
async def compare_runs(
    run_id: int,
    other_run_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Compare metrics between two training runs."""
    run_a = await training_repo.get_by_id(db, run_id)
    run_b = await training_repo.get_by_id(db, other_run_id)
    if not run_a or not run_b:
        raise HTTPException(status_code=404, detail="Training run not found")

    def parse_metrics(run):
        m = {}
        if run.metrics_json:
            try:
                m["training"] = json.loads(run.metrics_json)
            except json.JSONDecodeError:
                pass
        if run.eval_json:
            try:
                m["evaluation"] = json.loads(run.eval_json)
            except json.JSONDecodeError:
                pass
        return m

    return {
        "run_a": {"id": run_a.id, "name": run_a.name, **parse_metrics(run_a)},
        "run_b": {"id": run_b.id, "name": run_b.name, **parse_metrics(run_b)},
    }


@router.post("/training-runs/{run_id}/activate")
async def activate_model(run_id: int, db: AsyncSession = Depends(get_db)):
    """Set the trained model as the active inference model."""
    run = await training_repo.get_by_id(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")
    if not run.model_path:
        raise HTTPException(status_code=400, detail="No trained model available")

    from ..config import settings
    settings.yolo_model_path = run.model_path

    # Clear cached model so next inference loads the new one
    from ..services import inference_service
    inference_service._model = None
    inference_service._model_path = None

    return {"message": f"Activated model from run '{run.name}'", "model_path": run.model_path}
