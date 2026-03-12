from app.services.annotation_service import compute_normalized


def test_compute_normalized_center():
    result = compute_normalized(
        x_min=100, y_min=200, x_max=300, y_max=400,
        img_width=1000, img_height=1000,
    )
    assert result["normalized_x_center"] == 0.2  # (100 + 100) / 1000
    assert result["normalized_y_center"] == 0.3  # (200 + 100) / 1000
    assert result["normalized_width"] == 0.2  # 200 / 1000
    assert result["normalized_height"] == 0.2  # 200 / 1000


def test_compute_normalized_full_image():
    result = compute_normalized(
        x_min=0, y_min=0, x_max=1080, y_max=1920,
        img_width=1080, img_height=1920,
    )
    assert result["normalized_x_center"] == 0.5
    assert result["normalized_y_center"] == 0.5
    assert result["normalized_width"] == 1.0
    assert result["normalized_height"] == 1.0


def test_compute_normalized_small_box():
    result = compute_normalized(
        x_min=540, y_min=960, x_max=541, y_max=961,
        img_width=1080, img_height=1920,
    )
    assert abs(result["normalized_x_center"] - 540.5 / 1080) < 1e-6
    assert abs(result["normalized_width"] - 1 / 1080) < 1e-6
