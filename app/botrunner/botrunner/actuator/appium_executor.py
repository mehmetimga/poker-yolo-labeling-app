"""Appium executor — pointer actions for Rive/Flutter button compatibility."""

import asyncio
import logging

from ..config import settings
from .base import ClickExecutor

logger = logging.getLogger(__name__)

try:
    from appium import webdriver as appium_webdriver
    from appium.webdriver.common.appiumby import AppiumBy
    from selenium.webdriver.common.action_chains import ActionChains
    _APPIUM_AVAILABLE = True
except ImportError:
    _APPIUM_AVAILABLE = False


class AppiumExecutor(ClickExecutor):
    name = "appium"

    def __init__(self):
        self._driver = None

    def _get_driver(self):
        """Lazy-init Appium driver connection."""
        if self._driver is not None:
            return self._driver

        if not _APPIUM_AVAILABLE:
            raise RuntimeError("Appium-Python-Client not installed")

        caps = {}
        if settings.appium_platform == "android":
            caps = {
                "platformName": "Android",
                "automationName": "UiAutomator2",
                "noReset": True,
            }
            if settings.adb_device:
                caps["udid"] = settings.adb_device
        elif settings.appium_platform == "ios":
            caps = {
                "platformName": "iOS",
                "automationName": "XCUITest",
                "noReset": True,
            }

        self._driver = appium_webdriver.Remote(
            command_executor=settings.appium_url,
            desired_capabilities=caps,
        )
        logger.info(f"Appium connected ({settings.appium_platform}) at {settings.appium_url}")
        return self._driver

    async def tap(self, x: int, y: int) -> bool:
        """Pointer action: move → down → pause → up (Rive compatible)."""
        try:
            driver = await asyncio.to_thread(self._get_driver)
            pause_sec = settings.appium_tap_pause_ms / 1000.0

            def _tap():
                actions = ActionChains(driver)
                actions.w3c_actions.pointer_action.move_to_location(x, y)
                actions.w3c_actions.pointer_action.pointer_down()
                actions.w3c_actions.pointer_action.pause(pause_sec)
                actions.w3c_actions.pointer_action.pointer_up()
                actions.perform()

            await asyncio.to_thread(_tap)
            logger.info(f"appium tap at ({x}, {y}) pause={settings.appium_tap_pause_ms}ms")
            return True
        except Exception as e:
            logger.error(f"appium tap failed: {e}")
            self._driver = None  # Reset connection on failure
            return False

    async def drag(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> bool:
        """Pointer action: move → down → move(target) → up."""
        try:
            driver = await asyncio.to_thread(self._get_driver)

            def _drag():
                actions = ActionChains(driver)
                actions.w3c_actions.pointer_action.move_to_location(x1, y1)
                actions.w3c_actions.pointer_action.pointer_down()
                actions.w3c_actions.pointer_action.pause(0.05)
                actions.w3c_actions.pointer_action.move_to_location(x2, y2)
                actions.w3c_actions.pointer_action.pause(0.05)
                actions.w3c_actions.pointer_action.pointer_up()
                actions.perform()

            await asyncio.to_thread(_drag)
            logger.info(f"appium drag ({x1},{y1}) → ({x2},{y2})")
            return True
        except Exception as e:
            logger.error(f"appium drag failed: {e}")
            self._driver = None
            return False

    async def health_check(self) -> bool:
        if not _APPIUM_AVAILABLE:
            return False
        try:
            driver = await asyncio.to_thread(self._get_driver)
            return driver is not None
        except Exception:
            return False
