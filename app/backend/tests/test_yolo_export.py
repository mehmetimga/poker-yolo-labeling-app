import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models.project import Project
from app.models.image import ImageRecord
from app.models.annotation import Annotation
from app.services.export_service import export_yolo, export_metadata


@pytest_asyncio.fixture
async def db_with_data():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as db:
        project = Project(
            id=1, name="test", description="", image_root_path="/tmp/images"
        )
        db.add(project)

        image = ImageRecord(
            id=1,
            project_id=1,
            filename="test.png",
            filepath="/tmp/images/test.png",
            width=1080,
            height=1920,
            hash="abc123",
        )
        db.add(image)

        ann = Annotation(
            image_id=1,
            label="hero_card",
            x_min=400.0,
            y_min=1500.0,
            x_max=500.0,
            y_max=1700.0,
            normalized_x_center=round((400 + 50) / 1080, 6),
            normalized_y_center=round((1500 + 100) / 1920, 6),
            normalized_width=round(100 / 1080, 6),
            normalized_height=round(200 / 1920, 6),
            source="manual",
        )
        db.add(ann)
        await db.commit()
        yield db

    await engine.dispose()


@pytest.mark.asyncio
async def test_yolo_export_format(db_with_data):
    with tempfile.TemporaryDirectory() as tmpdir:
        result = await export_yolo(db_with_data, 1, tmpdir)
        assert result["exported_images"] == 1

        txt_path = Path(tmpdir) / "test.txt"
        assert txt_path.exists()

        content = txt_path.read_text().strip()
        parts = content.split()
        assert len(parts) == 5

        class_id = int(parts[0])
        x_center = float(parts[1])
        y_center = float(parts[2])
        width = float(parts[3])
        height = float(parts[4])

        # All values should be in [0, 1]
        assert 0 <= x_center <= 1
        assert 0 <= y_center <= 1
        assert 0 < width <= 1
        assert 0 < height <= 1

        # classes.txt should exist
        classes_path = Path(tmpdir) / "classes.txt"
        assert classes_path.exists()


@pytest.mark.asyncio
async def test_metadata_export_format(db_with_data):
    import json

    with tempfile.TemporaryDirectory() as tmpdir:
        result = await export_metadata(db_with_data, 1, tmpdir)
        assert result["exported_images"] == 1

        json_path = Path(tmpdir) / "test.json"
        assert json_path.exists()

        data = json.loads(json_path.read_text())
        assert data["image"] == "test.png"
        assert data["project"] == "test"
        assert len(data["annotations"]) == 1

        ann = data["annotations"][0]
        assert ann["label"] == "hero_card"
        assert len(ann["bbox_xyxy"]) == 4
        assert len(ann["bbox_yolo"]) == 4
        assert ann["source"] == "manual"
