"""Models for the actuator module."""

from pydantic import BaseModel


class ButtonLocation(BaseModel):
    action: str           # "fold","call","check","raise","bet","all_in"
    label: str            # original YOLO label ("fold_button")
    amount: float | None = None
    center_x: float       # capture-space pixels
    center_y: float
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    confidence: float


class SliderLocation(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    center_y: float


class DetectionMap(BaseModel):
    frame_id: str
    timestamp: float
    window_left: int
    window_top: int
    window_width: int
    window_height: int
    retina_scale: float       # mss_width / logical_width (1.0 or 2.0)
    buttons: list[ButtonLocation] = []
    slider: SliderLocation | None = None


class ClickRequest(BaseModel):
    action: str
    amount: float | None = None
    method: str | None = None   # override config method


class ClickResult(BaseModel):
    status: str           # "clicked","not_found","safety_blocked","dry_run"
    action: str
    screen_x: int | None = None
    screen_y: int | None = None
    detail: str = ""
