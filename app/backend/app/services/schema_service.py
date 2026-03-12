from collections import Counter

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import load_schemas, load_taxonomy
from ..repositories import annotation_repo, image_repo
from ..utils.regions import get_region_map, point_in_region


# Scoring weights
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

    # Score required labels
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

        # Check count
        if count_min and count_max and count_min <= count <= count_max:
            score += W_REQUIRED_COUNT
        elif expected_count and count == expected_count:
            score += W_REQUIRED_COUNT

        # Check region
        region = rule.get("region")
        if region and label in label_positions:
            in_region = any(
                point_in_region(x, y, region, region_map)
                for x, y in label_positions[label]
            )
            if in_region:
                score += W_REQUIRED_REGION

    # Score optional labels
    for rule in schema_def.get("optional", []):
        label = rule["label"]
        if label_counts.get(label, 0) > 0:
            score += W_OPTIONAL_PRESENT

    # Score forbidden labels
    for rule in schema_def.get("forbidden", []):
        label = rule["label"]
        if label_counts.get(label, 0) > 0:
            score += W_FORBIDDEN_PRESENT
            conflicts.append(label)

    return {
        "score": score,
        "missing": missing,
        "conflicts": conflicts,
    }


def _normalize_scores(results: list[dict]) -> list[dict]:
    if not results:
        return results
    max_score = max(r["score"] for r in results)
    min_score = min(r["score"] for r in results)
    spread = max_score - min_score if max_score != min_score else 1.0
    for r in results:
        r["normalized_score"] = max(0.0, min(1.0, (r["score"] - min_score) / spread))
    return results


async def score_schemas(db: AsyncSession, image_id: int) -> list[dict]:
    image = await image_repo.get_by_id(db, image_id)
    if not image:
        raise ValueError(f"Image {image_id} not found")

    annotations = await annotation_repo.get_by_image(db, image_id)
    if not annotations:
        return []

    label_counts: Counter = Counter()
    label_positions: dict[str, list[tuple[float, float]]] = {}

    for ann in annotations:
        label_counts[ann.label] += 1
        label_positions.setdefault(ann.label, []).append(
            (ann.normalized_x_center, ann.normalized_y_center)
        )

    schemas_config = load_schemas()
    region_map = get_region_map()

    results = []
    for schema_def in schemas_config["schemas"]:
        result = _score_schema(schema_def, label_counts, label_positions, region_map)
        results.append({
            "schema": schema_def["name"],
            "score": result["normalized_score"] if "normalized_score" in result else result["score"],
            "missing": result["missing"],
            "conflicts": result["conflicts"],
        })

    # Normalize
    results = _normalize_scores(results)
    for r in results:
        r["score"] = round(r.get("normalized_score", r["score"]), 3)
        r.pop("normalized_score", None)

    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def get_taxonomy_label_id_map() -> dict[str, int]:
    taxonomy = load_taxonomy()
    return {label["name"]: label["id"] for label in taxonomy["labels"]}
