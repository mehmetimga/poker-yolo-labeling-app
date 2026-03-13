"""HTTP client to send decisions to the botrunner actuator."""

import logging

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=5.0)
    return _client


async def send_to_actuator(action: str, amount: float | None = None) -> dict | None:
    """POST a decision to the botrunner actuator endpoint.

    Returns the ClickResult dict on success, None on failure.
    """
    if not settings.actuator_enabled:
        return None

    url = f"http://{settings.botrunner_host}:{settings.botrunner_port}/actuator/execute"
    payload: dict = {"action": action}
    if amount is not None:
        payload["amount"] = amount

    try:
        client = _get_client()
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        result = resp.json()
        logger.info(
            "Actuator response: %s for %s at (%s, %s)",
            result.get("status"), action,
            result.get("screen_x"), result.get("screen_y"),
        )
        return result
    except httpx.HTTPStatusError as e:
        logger.error("Actuator HTTP error: %s", e.response.status_code)
        return None
    except Exception as e:
        logger.error("Actuator request failed: %s", e)
        return None


async def close_client():
    global _client
    if _client:
        await _client.aclose()
        _client = None
