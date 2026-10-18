import json

from sqlalchemy.orm import Session

from app.core.auth import Principal
from app.persistence.models import AuditLog


def record_audit(
    db: Session,
    principal: Principal,
    *,
    action: str,
    resource_type: str,
    resource_id: str | None,
    outcome: str,
    details: dict[str, object] | None = None,
) -> None:
    db.add(
        AuditLog(
            organization_id=principal.organization_id,
            actor_id=principal.user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            details_json=json.dumps(details or {}),
        )
    )
