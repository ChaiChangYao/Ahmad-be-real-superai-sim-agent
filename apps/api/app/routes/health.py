from datetime import datetime, UTC
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
def root() -> dict:
    return {
        "service": "buildables-sim-sandbox-api",
        "status": "ok",
        "message": "API is running. Use /health or open the web UI at http://localhost:3000",
        "docs": "/docs",
        "health": "/health",
    }


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "buildables-sim-sandbox-api", "timestamp": datetime.now(UTC).isoformat()}
