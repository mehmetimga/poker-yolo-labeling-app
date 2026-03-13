#!/usr/bin/env python3
"""Entry point for the botrunner service."""

import uvicorn

from botrunner.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "botrunner.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=False,
        log_level="info",
    )
