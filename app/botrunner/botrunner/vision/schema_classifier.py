from collections import Counter

from ..config import load_schemas, load_regions
from ..models.pipeline_models import Detection


def _point_in_region(x: float, y: float, region_name: str, region_map: dict) -> bool:
    region = region_map.get(region_name)
    if not region:
        return False
    return (
        region["x_min"] <= x <= region["x_max"]
        and region["y_min"] <= y <= region["y_max"]
    )


# Scoring weights (same as backend)
W_REQUIRED_PRESENT = 3.0
W_REQUIRED_REGION = 1.0
W_REQUIRED_COUNT = 1.0
W_OPTIONAL_PRESENT = 1.0
W_FORBIDDEN_PRESENT = -5.0
W_MISSING_REQUIRED = -4.0


def _score_schema(
    schema_def: dict,
    label_counts: Counter,
    label_positions: dict[str, list[tuple[float, float]]],
    region_map: dict,
) -> dict:
    score = 0.0
    missing = []
    conflicts = []

    for rule in schema_def.get("required", []):
        label = rule["label"]
        count = label_counts.get(label, 0)
        expected_count = rule.get("count")
        count_min = rule.get("count_min", expected_count or 1)
        count_max = rule.get("count_max", expected_count or count_min)

        if count == 0:
            score += W_MISSING_REQUIRED
            missing.append(label)
            continue

        score += W_REQUIRED_PRESENT
        if count_min and count_max and count_min <= count <= count_max:
            score += W_REQUIRED_COUNT
        elif expected_count and count == expected_count:
            score += W_REQUIRED_COUNT

        region = rule.get("region")
        if region and label in label_positions:
            in_region = any(
                _point_in_region(x, y, region, region_map)
                for x, y in label_positions[label]
            )
            if in_region:
                score += W_REQUIRED_REGION

    for rule in schema_def.get("optional", []):
        label = rule["label"]
        if label_counts.get(label, 0) > 0:
            score += W_OPTIONAL_PRESENT

    for rule in schema_def.get("forbidden", []):
        label = rule["label"]
        if label_counts.get(label, 0) > 0:
            score += W_FORBIDDEN_PRESENT
            conflicts.append(label)

    return {"score": score, "missing": missing, "conflicts": conflicts}


def classify_schema(
    detections: list[Detection], img_width: int, img_height: int
) -> tuple[str, float]:
    """Classify detections against all schemas. Returns (schema_name, normalized_score)."""
    label_counts: Counter = Counter()
    label_positions: dict[str, list[tuple[float, float]]] = {}

    for det in detections:
        label_counts[det.label] += 1
        nx = det.center_x / img_width
        ny = det.center_y / img_height
        label_positions.setdefault(det.label, []).append((nx, ny))

    schemas_config = load_schemas()
    region_map = load_regions()

    results = []
    for schema_def in schemas_config["schemas"]:
        result = _score_schema(schema_def, label_counts, label_positions, region_map)
        results.append({"schema": schema_def["name"], **result})

    if not results:
        return "unknown", 0.0

    max_score = max(r["score"] for r in results)
    min_score = min(r["score"] for r in results)
    spread = max_score - min_score if max_score != min_score else 1.0

    for r in results:
        r["normalized"] = max(0.0, min(1.0, (r["score"] - min_score) / spread))

    results.sort(key=lambda x: x["normalized"], reverse=True)
    best = results[0]
    return best["schema"], round(best["normalized"], 3)
