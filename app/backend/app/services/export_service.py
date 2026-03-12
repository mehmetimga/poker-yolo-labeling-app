import json
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.project import Project
from ..models.image import ImageRecord
from ..models.annotation import Annotation
from ..repositories import project_repo
from ..services.schema_service import get_taxonomy_label_id_map


async def export_yolo(db: AsyncSession, project_id: int, output_dir: str) -> dict:
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    label_id_map = get_taxonomy_label_id_map()
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Write classes.txt
    sorted_labels = sorted(label_id_map.items(), key=lambda x: x[1])
    classes_file = out_path / "classes.txt"
    classes_file.write_text("\n".join(name for name, _ in sorted_labels) + "\n")

    stmt = select(ImageRecord).where(ImageRecord.project_id == project_id)
    result = await db.execute(stmt)
    images = result.scalars().all()

    exported = 0
    for image in images:
        ann_stmt = select(Annotation).where(Annotation.image_id == image.id)
        ann_result = await db.execute(ann_stmt)
        annotations = ann_result.scalars().all()

        if not annotations:
            continue

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

        (out_path / txt_name).write_text("\n".join(lines) + "\n")
        exported += 1

    return {"exported_images": exported, "output_dir": str(out_path)}


async def export_metadata(db: AsyncSession, project_id: int, output_dir: str) -> dict:
    project = await project_repo.get_by_id(db, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    stmt = select(ImageRecord).where(ImageRecord.project_id == project_id)
    result = await db.execute(stmt)
    images = result.scalars().all()

    exported = 0
    for image in images:
        ann_stmt = select(Annotation).where(Annotation.image_id == image.id)
        ann_result = await db.execute(ann_stmt)
        annotations = ann_result.scalars().all()

        if not annotations:
            continue

        metadata = {
            "image": image.filename,
            "project": project.name,
            "assigned_schema": image.assigned_schema,
            "suggested_schema": image.suggested_schema,
            "schema_confidence": image.schema_confidence,
            "review_status": image.review_status,
            "annotations": [
                {
                    "label": ann.label,
                    "bbox_xyxy": [ann.x_min, ann.y_min, ann.x_max, ann.y_max],
                    "bbox_yolo": [
                        round(ann.normalized_x_center, 6),
                        round(ann.normalized_y_center, 6),
                        round(ann.normalized_width, 6),
                        round(ann.normalized_height, 6),
                    ],
                    "source": ann.source,
                    "confidence": ann.confidence,
                }
                for ann in annotations
            ],
        }

        json_name = Path(image.filename).stem + ".json"
        (out_path / json_name).write_text(json.dumps(metadata, indent=2) + "\n")
        exported += 1

    return {"exported_images": exported, "output_dir": str(out_path)}
