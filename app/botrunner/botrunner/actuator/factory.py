"""Executor factory — create the right ClickExecutor for the configured method."""

from ..config import settings
from .base import ClickExecutor


def create_executor(method: str | None = None) -> ClickExecutor:
    """Create a ClickExecutor based on method name.
    Falls back to config if method is None."""
    m = method or settings.actuator_method

    match m:
        case "pyautogui":
            from .pyautogui_executor import PyAutoGUIExecutor
            return PyAutoGUIExecutor()
        case "cliclick":
            from .cliclick_executor import CliClickExecutor
            return CliClickExecutor()
        case "adb":
            from .adb_executor import ADBExecutor
            return ADBExecutor()
        case "appium":
            from .appium_executor import AppiumExecutor
            return AppiumExecutor()
        case "applescript":
            from .applescript_executor import AppleScriptExecutor
            return AppleScriptExecutor()
        case _:
            raise ValueError(f"Unknown actuator method: {m}")
