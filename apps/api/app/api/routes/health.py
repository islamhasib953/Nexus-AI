from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    settings = get_settings()
    return {"status": "ok", "service": settings.app_name, "version": settings.app_version}


@router.get("/ready")
async def readiness() -> dict[str, object]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "checks": {"configuration": "ok", "external_dependencies": "not_configured"},
    }
