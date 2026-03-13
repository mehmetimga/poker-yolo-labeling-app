import json
from pathlib import Path

from pydantic_settings import BaseSettings


class BotSettings(BaseSettings):
    # Capture
    capture_interval_ms: int = 500
    window_title: str = "BetRivers"
    capture_region: str | None = None  # "x,y,w,h" override

    # Dedup
    phash_threshold: int = 8

    # Model
    yolo_model_path: str = ""
    yolo_confidence: float = 0.25

    # OCR
    ocr_gpu: bool = False
    ocr_languages: str = "en"

    # Game state
    confidence_gate: float = 0.4

    # Shared config
    shared_dir: str = str(Path(__file__).resolve().parent.parent.parent / "shared")

    # API
    api_port: int = 8100

    model_config = {"env_prefix": "BOT_"}


settings = BotSettings()


def load_taxonomy() -> dict:
    path = Path(settings.shared_dir) / "taxonomy.json"
    with open(path) as f:
        return json.load(f)


def load_schemas() -> dict:
    path = Path(settings.shared_dir) / "schemas.json"
    with open(path) as f:
        return json.load(f)


def load_regions() -> dict:
    path = Path(settings.shared_dir) / "regions.json"
    with open(path) as f:
        return json.load(f)
