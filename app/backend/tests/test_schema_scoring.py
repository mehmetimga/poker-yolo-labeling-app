import pytest
from collections import Counter
from app.services.schema_service import _score_schema
from app.utils.regions import get_region_map


@pytest.fixture
def region_map():
    return get_region_map()


@pytest.fixture
def preflop_my_turn_schema():
    return {
        "name": "table_preflop_my_turn",
        "required": [
            {"label": "hero_card", "count": 2, "region": "bottom_center"},
            {"label": "fold_button", "count": 1, "region": "bottom"},
            {"label": "call_button", "count": 1, "region": "bottom"},
            {"label": "raise_button", "count": 1, "region": "bottom"},
        ],
        "optional": [
            {"label": "pot_amount", "count": 1, "region": "center"},
            {"label": "dealer_button", "count": 1},
        ],
        "forbidden": [
            {"label": "winner_banner"},
            {"label": "buyin_popup"},
            {"label": "board_card"},
        ],
    }


def test_perfect_match(preflop_my_turn_schema, region_map):
    label_counts = Counter({
        "hero_card": 2,
        "fold_button": 1,
        "call_button": 1,
        "raise_button": 1,
        "pot_amount": 1,
    })
    label_positions = {
        "hero_card": [(0.5, 0.9), (0.5, 0.9)],
        "fold_button": [(0.2, 0.85)],
        "call_button": [(0.5, 0.85)],
        "raise_button": [(0.8, 0.85)],
        "pot_amount": [(0.5, 0.5)],
    }

    result = _score_schema(preflop_my_turn_schema, label_counts, label_positions, region_map)
    assert result["score"] > 0
    assert result["missing"] == []
    assert result["conflicts"] == []


def test_missing_required(preflop_my_turn_schema, region_map):
    label_counts = Counter({"hero_card": 2})
    label_positions = {"hero_card": [(0.5, 0.9), (0.5, 0.9)]}

    result = _score_schema(preflop_my_turn_schema, label_counts, label_positions, region_map)
    assert "fold_button" in result["missing"]
    assert "call_button" in result["missing"]
    assert "raise_button" in result["missing"]


def test_forbidden_label_penalizes(preflop_my_turn_schema, region_map):
    label_counts = Counter({
        "hero_card": 2,
        "fold_button": 1,
        "call_button": 1,
        "raise_button": 1,
        "winner_banner": 1,  # forbidden
    })
    label_positions = {
        "hero_card": [(0.5, 0.9), (0.5, 0.9)],
        "fold_button": [(0.2, 0.85)],
        "call_button": [(0.5, 0.85)],
        "raise_button": [(0.8, 0.85)],
        "winner_banner": [(0.5, 0.5)],
    }

    result = _score_schema(preflop_my_turn_schema, label_counts, label_positions, region_map)
    assert "winner_banner" in result["conflicts"]


def test_empty_annotations(preflop_my_turn_schema, region_map):
    label_counts = Counter()
    label_positions = {}

    result = _score_schema(preflop_my_turn_schema, label_counts, label_positions, region_map)
    assert result["score"] < 0
    assert len(result["missing"]) == 4  # all required labels missing
