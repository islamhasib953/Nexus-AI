from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/api/v1", tags=["contract"])


@router.get("/contract")
async def contract_summary() -> dict[str, object]:
    settings = get_settings()
    return {
        "api_version": "v1",
        "service": settings.app_name,
        "phase": 2,
        "status": "foundation",
        "streaming": "SSE",
        "model_provider": settings.model_provider,
        "routes": [
            "/api/v1/health/live",
            "/api/v1/health/ready",
            "/api/v1/contract",
        ],
    }
