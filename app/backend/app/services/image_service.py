import hashlib
from pathlib import Path

from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..repositories import image_repo

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def compute_file_hash(filepath: Path) -> str:
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_image_dimensions(filepath: Path) -> tuple[int, int]:
    with Image.open(filepath) as img:
        return img.size  # (width, height)


async def import_images_from_folder(
    db: AsyncSession, project_id: int, folder_path: str
) -> dict:
    folder = settings.resolve_image_path(folder_path)
    if not folder.is_dir():
        return {"imported": 0, "skipped": 0, "errors": [f"Not a directory: {folder} (from '{folder_path}')"]}

    imported = 0
    skipped = 0
    errors: list[str] = []

    for fp in sorted(folder.iterdir()):
        if fp.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        try:
            file_hash = compute_file_hash(fp)
            existing = await image_repo.get_by_hash(db, project_id, file_hash)
            if existing:
                skipped += 1
                continue

            width, height = get_image_dimensions(fp)
            await image_repo.create(
                db,
                project_id=project_id,
                filename=fp.name,
                filepath=str(fp.resolve()),
                width=width,
                height=height,
                hash=file_hash,
            )
            imported += 1
        except Exception as e:
            errors.append(f"{fp.name}: {e}")

    await image_repo.bulk_flush(db)
    return {"imported": imported, "skipped": skipped, "errors": errors}
