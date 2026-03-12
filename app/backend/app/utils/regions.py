from ..config import load_regions


def get_region_map() -> dict[str, dict]:
    data = load_regions()
    return data["regions"]


def point_in_region(
    x_center_norm: float, y_center_norm: float, region_name: str, region_map: dict
) -> bool:
    region = region_map.get(region_name)
    if not region:
        return True  # Unknown region = no constraint
    return (
        region["x_min"] <= x_center_norm <= region["x_max"]
        and region["y_min"] <= y_center_norm <= region["y_max"]
    )
