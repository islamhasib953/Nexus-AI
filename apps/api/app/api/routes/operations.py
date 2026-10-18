from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_principal
from app.operations.service import OperationsService

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])


def get_db(request: Request):
    yield from request.app.state.database.sessions()


def require_operations_access(principal: Principal = Depends(require_principal)) -> Principal:
    if principal.workspace != "internal" or principal.role not in {"internal_member", "admin"}:
        raise HTTPException(status_code=403, detail="Operations metrics require an internal role.")
    return principal


@router.get("/overview")
def overview(
    request: Request,
    principal: Principal = Depends(require_operations_access),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if not request.app.state.settings.observability_enabled:
        raise HTTPException(
            status_code=404, detail="Observability is disabled for this environment."
        )
    service = OperationsService(request.app.state.settings, request.app.state.model_router)
    return service.overview(db, principal.organization_id)


@router.get("/alerts")
def alerts(
    request: Request,
    principal: Principal = Depends(require_operations_access),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    if not request.app.state.settings.observability_enabled:
        raise HTTPException(
            status_code=404, detail="Observability is disabled for this environment."
        )
    service = OperationsService(request.app.state.settings, request.app.state.model_router)
    snapshot = service.overview(db, principal.organization_id)
    return {"generated_at": snapshot["generated_at"], "items": service.alerts(snapshot)}
