"""Append decisions to a JSONL file for post-session review."""

import logging
import threading

from ..config import settings
from ..models.decision import Decision

logger = logging.getLogger(__name__)

_lock = threading.Lock()


def log_decision(decision: Decision):
    """Append a decision as a JSON line to the log file."""
    if not settings.log_decisions_to_file:
        return
    try:
        line = decision.model_dump_json()
        with _lock:
            with open(settings.decision_log_path, "a") as f:
                f.write(line + "\n")
    except Exception as e:
        logger.warning(f"Failed to log decision: {e}")
