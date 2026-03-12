from sqlalchemy.ext.asyncio import AsyncSession

from ..repositories import annotation_repo, image_repo
from ..schemas.annotation import AnnotationCreate


def compute_normalized(
    x_min: float, y_min: float, x_max: float, y_max: float,
    img_width: int, img_height: int,
) -> dict:
    w = x_max - x_min
    h = y_max - y_min
    x_center = x_min + w / 2
    y_center = y_min + h / 2
    return {
        "normalized_x_center": x_center / img_width,
        "normalized_y_center": y_center / img_height,
        "normalized_width": w / img_width,
        "normalized_height": h / img_height,
    }


async def save_annotations(
    db: AsyncSession, image_id: int, annotations: list[AnnotationCreate]
) -> list[dict]:
    image = await image_repo.get_by_id(db, image_id)
    if not image:
        raise ValueError(f"Image {image_id} not found")

    ann_dicts = []
    for ann in annotations:
        normalized = compute_normalized(
            ann.x_min, ann.y_min, ann.x_max, ann.y_max,
            image.width, image.height,
        )
        ann_dicts.append({
            "label": ann.label,
            "x_min": ann.x_min,
            "y_min": ann.y_min,
            "x_max": ann.x_max,
            "y_max": ann.y_max,
            "source": ann.source,
            "confidence": ann.confidence,
            **normalized,
        })

    saved = await annotation_repo.replace_all(db, image_id, ann_dicts)

    # Update image status
    if saved:
        image.status = "labeled" if image.status == "new" else image.status
    await db.commit()

    return saved
