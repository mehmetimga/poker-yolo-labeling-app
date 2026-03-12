import json
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/poker_labeling.db"
    shared_dir: Path = Path(__file__).resolve().parent.parent.parent / "shared"
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    images_dir: Path = Path(__file__).resolve().parent.parent.parent / "datasets"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    yolo_model_path: str | None = None
    yolo_confidence_threshold: float = 0.25

    model_config = {"env_prefix": "LABELING_"}

    def resolve_image_path(self, image_root_path: str) -> Path:
        """Resolve image_root_path: if relative, resolve against images_dir."""
        p = Path(image_root_path)
        if p.is_absolute():
            return p
        return self.images_dir / image_root_path


settings = Settings()


def load_taxonomy() -> dict:
    with open(settings.shared_dir / "taxonomy.json") as f:
        return json.load(f)


def load_schemas() -> dict:
    with open(settings.shared_dir / "schemas.json") as f:
        return json.load(f)


def load_regions() -> dict:
    with open(settings.shared_dir / "regions.json") as f:
        return json.load(f)
