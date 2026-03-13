import asyncio
import json
import logging
import random
import shutil
from collections import defaultdict
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import async_session
from ..models.image import ImageRecord
from ..models.annotation import Annotation
from ..models.training import TrainingRun, DatasetSplit
from ..repositories import training_repo, image_repo, annotation_repo
from ..services.schema_service import get_taxonomy_label_id_map
from ..services import inference_service

logger = logging.getLogger(__name__)

# In-memory training task tracking (same pattern as batch_inference_service)
_training_tasks: dict[int, dict] = {}  # run_id -> status info


def get_training_status(run_id: int) -> dict | None:
    return _training_tasks.get(run_id)


async def create_stratified_split(
    db: AsyncSession,
    project_id: int,
    run_id: int,
    train_ratio: float = 0.7,
    val_ratio: float = 0.2,
    test_ratio: float = 0.1,
) -> dict[str, int]:
    """Split labeled images into train/val/test sets, stratified by assigned_schema."""
    # Get all labeled images (status in labeled, reviewed, approved, pre_annotated)
    stmt = (
        select(ImageRecord)
        .where(
            ImageRecord.project_id == project_id,
            ImageRecord.status.in_(["labeled", "reviewed", "approved", "pre_annotated"]),
        )
    )
    result = await db.execute(stmt)
    images = list(result.scalars().all())

    if not images:
        return {"train": 0, "val": 0, "test": 0}

    # Group by assigned_schema for stratification
    schema_groups: dict[str, list[int]] = defaultdict(list)
    for img in images:
        key = img.assigned_schema or "_unassigned"
        schema_groups[key].append(img.id)

    splits: list[dict] = []
    counts = {"train": 0, "val": 0, "test": 0}

    for _schema, img_ids in schema_groups.items():
        random.shuffle(img_ids)
        n = len(img_ids)
        n_train = max(1, int(n * train_ratio))
        n_val = max(0, int(n * val_ratio))
        # rest goes to test
        train_ids = img_ids[:n_train]
        val_ids = img_ids[n_train:n_train + n_val]
        test_ids = img_ids[n_train + n_val:]

        for iid in train_ids:
            splits.append({"image_id": iid, "split": "train"})
            counts["train"] += 1
        for iid in val_ids:
            splits.append({"image_id": iid, "split": "val"})
            counts["val"] += 1
        for iid in test_ids:
            splits.append({"image_id": iid, "split": "test"})
            counts["test"] += 1

    await training_repo.create_splits(db, run_id, splits)
    return counts


async def prepare_yolo_dataset(db: AsyncSession, run_id: int) -> Path:
    """Create YOLO-format dataset directory from split assignments."""
    label_id_map = get_taxonomy_label_id_map()
    run = await training_repo.get_by_id(db, run_id)
    if not run:
        raise ValueError(f"Training run {run_id} not found")

    base_dir = settings.data_dir / "training" / f"run_{run_id}"
    if base_dir.exists():
        shutil.rmtree(base_dir)

    for split_name in ("train", "val", "test"):
        (base_dir / split_name / "images").mkdir(parents=True, exist_ok=True)
        (base_dir / split_name / "labels").mkdir(parents=True, exist_ok=True)

    # Get all splits
    splits = await training_repo.get_splits(db, run_id)

    for ds in splits:
        image = await image_repo.get_by_id(db, ds.image_id)
        if not image:
            continue

        annotations = await annotation_repo.get_by_image(db, ds.image_id)
        if not annotations:
            continue

        # Resolve image path
        src_path = Path(image.filepath)
        if not src_path.is_file():
            src_path = settings.images_dir / image.filepath
        if not src_path.is_file():
            continue

        # Symlink image
        dest_img = base_dir / ds.split / "images" / image.filename
        if not dest_img.exists():
            dest_img.symlink_to(src_path.resolve())

        # Write YOLO label file
        txt_name = Path(image.filename).stem + ".txt"
        lines = []
        for ann in annotations:
            class_id = label_id_map.get(ann.label)
            if class_id is None:
                continue
            lines.append(
                f"{class_id} {ann.normalized_x_center:.6f} {ann.normalized_y_center:.6f} "
                f"{ann.normalized_width:.6f} {ann.normalized_height:.6f}"
            )
        (base_dir / ds.split / "labels" / txt_name).write_text("\n".join(lines) + "\n")

    # Write data.yaml
    sorted_labels = sorted(label_id_map.items(), key=lambda x: x[1])
    names_list = [name for name, _ in sorted_labels]
    data_yaml = {
        "path": str(base_dir.resolve()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": len(names_list),
        "names": names_list,
    }
    import yaml
    (base_dir / "data.yaml").write_text(yaml.dump(data_yaml, default_flow_style=False))

    return base_dir


def _run_yolo_training(data_yaml: str, run: TrainingRun) -> dict:
    """Synchronous YOLO training (runs in thread). Returns metrics dict."""
    from ultralytics import YOLO

    model = YOLO(run.base_model)
    results = model.train(
        data=data_yaml,
        epochs=run.epochs,
        batch=run.batch_size,
        imgsz=run.img_size,
        lr0=run.learning_rate,
        project=str(Path(data_yaml).parent / "output"),
        name="train",
        exist_ok=True,
        verbose=True,
    )

    # Extract metrics from results
    metrics = {}
    if results and hasattr(results, "results_dict"):
        metrics = {k: float(v) for k, v in results.results_dict.items()}

    # Find best model path
    output_dir = Path(data_yaml).parent / "output" / "train"
    best_pt = output_dir / "weights" / "best.pt"
    if not best_pt.exists():
        best_pt = output_dir / "weights" / "last.pt"

    metrics["model_path"] = str(best_pt) if best_pt.exists() else None
    return metrics


def _run_yolo_evaluation(model_path: str, data_yaml: str, split: str = "test") -> dict:
    """Run model validation on a specific split. Returns per-class metrics."""
    from ultralytics import YOLO

    model = YOLO(model_path)
    results = model.val(data=data_yaml, split=split, verbose=False)

    eval_data = {
        "mAP50": float(results.box.map50) if hasattr(results.box, "map50") else None,
        "mAP50_95": float(results.box.map) if hasattr(results.box, "map") else None,
        "precision": float(results.box.mp) if hasattr(results.box, "mp") else None,
        "recall": float(results.box.mr) if hasattr(results.box, "mr") else None,
        "per_class": {},
    }

    # Per-class AP
    if hasattr(results.box, "ap50") and results.names:
        for i, (cls_id, name) in enumerate(results.names.items()):
            if i < len(results.box.ap50):
                eval_data["per_class"][name] = {
                    "ap50": float(results.box.ap50[i]),
                    "ap50_95": float(results.box.ap[i]) if i < len(results.box.ap) else None,
                }

    return eval_data


async def _run_error_mining(db: AsyncSession, run_id: int, model_path: str) -> list[dict]:
    """Compare model predictions vs ground truth on val/test images. Return top divergences."""
    splits = await training_repo.get_splits(db, run_id)
    val_test_splits = [s for s in splits if s.split in ("val", "test")]

    errors = []
    for ds in val_test_splits:
        image = await image_repo.get_by_id(db, ds.image_id)
        if not image:
            continue

        # Get ground truth
        gt_annotations = await annotation_repo.get_by_image(db, ds.image_id)
        gt_labels = defaultdict(int)
        for ann in gt_annotations:
            gt_labels[ann.label] += 1

        # Run model inference
        filepath = Path(image.filepath)
        if not filepath.is_file():
            filepath = settings.images_dir / image.filepath
        if not filepath.is_file():
            continue

        try:
            detections = await asyncio.to_thread(
                inference_service.run_inference,
                str(filepath),
                model_path,
                0.25,
            )
        except Exception:
            continue

        pred_labels = defaultdict(int)
        for d in detections:
            pred_labels[d["label"]] += 1

        # Compute divergence: labels that differ between GT and pred
        all_labels = set(gt_labels.keys()) | set(pred_labels.keys())
        divergence = 0
        missing = []
        extra = []
        for label in all_labels:
            gt_count = gt_labels.get(label, 0)
            pred_count = pred_labels.get(label, 0)
            diff = abs(gt_count - pred_count)
            divergence += diff
            if gt_count > pred_count:
                missing.append({"label": label, "gt": gt_count, "pred": pred_count})
            elif pred_count > gt_count:
                extra.append({"label": label, "gt": gt_count, "pred": pred_count})

        if divergence > 0:
            errors.append({
                "image_id": image.id,
                "filename": image.filename,
                "split": ds.split,
                "divergence": divergence,
                "gt_count": len(gt_annotations),
                "pred_count": len(detections),
                "missing": missing,
                "extra": extra,
            })

    # Sort by divergence descending
    errors.sort(key=lambda x: x["divergence"], reverse=True)
    return errors[:50]  # Top 50 worst


async def run_training_pipeline(run_id: int):
    """Full training pipeline: prepare dataset -> train -> evaluate -> error mine."""
    _training_tasks[run_id] = {"status": "preparing", "progress": "Preparing dataset..."}

    try:
        async with async_session() as db:
            run = await training_repo.get_by_id(db, run_id)
            if not run:
                raise ValueError(f"Run {run_id} not found")

            await training_repo.update(db, run, status="preparing")

            # 1. Prepare dataset
            dataset_dir = await prepare_yolo_dataset(db, run_id)
            data_yaml = str(dataset_dir / "data.yaml")

        # 2. Train (CPU/GPU-bound, run in thread)
        _training_tasks[run_id] = {"status": "training", "progress": "Training model..."}
        async with async_session() as db:
            run = await training_repo.get_by_id(db, run_id)
            await training_repo.update(db, run, status="training")

        metrics = await asyncio.to_thread(_run_yolo_training, data_yaml, run)
        model_path = metrics.pop("model_path", None)

        async with async_session() as db:
            run = await training_repo.get_by_id(db, run_id)
            await training_repo.update(
                db, run,
                metrics_json=json.dumps(metrics),
                model_path=model_path,
                status="evaluating",
            )

        # 3. Evaluate on val/test set
        _training_tasks[run_id] = {"status": "evaluating", "progress": "Evaluating model..."}
        if model_path and Path(model_path).exists():
            eval_results = await asyncio.to_thread(
                _run_yolo_evaluation, model_path, data_yaml, "val"
            )

            # 4. Error mining
            _training_tasks[run_id] = {"status": "mining", "progress": "Mining errors..."}
            async with async_session() as db:
                error_data = await _run_error_mining(db, run_id, model_path)
                eval_results["error_mining"] = error_data

            async with async_session() as db:
                run = await training_repo.get_by_id(db, run_id)
                await training_repo.update(
                    db, run,
                    eval_json=json.dumps(eval_results),
                    status="done",
                )
        else:
            async with async_session() as db:
                run = await training_repo.get_by_id(db, run_id)
                await training_repo.update(db, run, status="done")

        _training_tasks[run_id] = {"status": "done", "progress": "Complete"}

    except Exception as e:
        logger.error(f"Training pipeline failed for run {run_id}: {e}")
        _training_tasks[run_id] = {"status": "failed", "progress": str(e)}
        try:
            async with async_session() as db:
                run = await training_repo.get_by_id(db, run_id)
                if run:
                    await training_repo.update(db, run, status="failed", error_message=str(e))
        except Exception:
            pass
