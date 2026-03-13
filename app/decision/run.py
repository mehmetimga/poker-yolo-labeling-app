#!/usr/bin/env python3
"""Entry point for the decision engine service."""

import uvicorn

from decision.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "decision.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=False,
        log_level="info",
    )
