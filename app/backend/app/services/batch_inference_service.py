import asyncio
import logging
import uuid
from pathlib import Path

from ..config import settings
from ..database import async_session
from ..repositories import annotation_repo, image_repo
from ..services import inference_service, annotation_service
from ..schemas.annotation import AnnotationCreate

logger = logging.getLogger(__name__)

# In-memory task tracking
_tasks: dict[str, dict] = {}


def create_task(project_id: int, total: int) -> str:
    task_id = str(uuid.uuid4())
    _tasks[task_id] = {
        "task_id": task_id,
        "project_id": project_id,
        "status": "running",
        "total": total,
        "completed": 0,
        "errors": 0,
    }
    return task_id


def get_task(task_id: str) -> dict | None:
    return _tasks.get(task_id)


async def run_batch_inference(
    task_id: str,
    image_ids: list[int],
    model_path: str,
    confidence: float,
):
    """Run YOLO inference on a batch of images sequentially."""
    task = _tasks[task_id]

    for image_id in image_ids:
        try:
            async with async_session() as db:
                # Skip images that already have annotations
                existing = await annotation_repo.get_by_image(db, image_id)
                if existing:
                    task["completed"] += 1
                    continue

                image = await image_repo.get_by_id(db, image_id)
                if not image:
                    task["errors"] += 1
                    task["completed"] += 1
                    continue

                # Resolve filepath
                filepath = Path(image.filepath)
                if not filepath.is_file():
                    filepath = settings.images_dir / image.filepath
                if not filepath.is_file():
                    task["errors"] += 1
                    task["completed"] += 1
                    continue

                # Run inference in thread (CPU-bound)
                detections = await asyncio.to_thread(
                    inference_service.run_inference,
                    str(filepath),
                    model_path,
                    confidence,
                )

                if detections:
                    # Convert to AnnotationCreate objects
                    ann_creates = [
                        AnnotationCreate(**d) for d in detections
                    ]
                    await annotation_service.save_annotations(db, image_id, ann_creates)

                    # Update image status and avg confidence
                    avg_conf = sum(d["confidence"] for d in detections) / len(detections)
                    image.status = "pre_annotated"
                    image.schema_confidence = round(avg_conf, 4)
                    await db.commit()

                task["completed"] += 1

        except Exception as e:
            logger.error(f"Batch inference error on image {image_id}: {e}")
            task["errors"] += 1
            task["completed"] += 1

    task["status"] = "done"
