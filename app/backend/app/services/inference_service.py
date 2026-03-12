from pathlib import Path

try:
    from ultralytics import YOLO

    _ULTRALYTICS_AVAILABLE = True
except ImportError:
    _ULTRALYTICS_AVAILABLE = False

_model = None
_model_path = None


def load_model(model_path: str):
    global _model, _model_path
    if _model is not None and _model_path == model_path:
        return _model
    if not _ULTRALYTICS_AVAILABLE:
        raise RuntimeError("ultralytics is not installed")
    if not Path(model_path).is_file():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    _model = YOLO(model_path)
    _model_path = model_path
    return _model


def run_inference(
    image_path: str, model_path: str, confidence: float = 0.25
) -> list[dict]:
    model = load_model(model_path)
    results = model.predict(image_path, conf=confidence, verbose=False)
    detections = []
    if results and len(results) > 0:
        for box in results[0].boxes:
            xyxy = box.xyxy[0].tolist()
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            label = model.names.get(cls_id, f"class_{cls_id}")
            detections.append(
                {
                    "label": label,
                    "x_min": xyxy[0],
                    "y_min": xyxy[1],
                    "x_max": xyxy[2],
                    "y_max": xyxy[3],
                    "source": "model",
                    "confidence": conf,
                }
            )
    return detections
