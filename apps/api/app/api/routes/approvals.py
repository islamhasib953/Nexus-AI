import json
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_principal
from app.persistence.models import Approval
from app.security.audit import record_audit
from app.security.policy import PolicyEngine

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


class ApprovalRequest(BaseModel):
    action_type: str = Field(min_length=1, max_length=100)
    payload: dict[str, object] = Field(default_factory=dict)
    run_id: str | None = None
    ttl_minutes: int = Field(default=30, ge=1, le=1440)


def get_db(request: Request):
    yield from request.app.state.database.sessions()


def own_approval(db: Session, approval_id: str, principal: Principal) -> Approval:
    approval = db.get(Approval, approval_id)
    if approval is None or approval.organization_id != principal.organization_id:
        raise HTTPException(status_code=404, detail="Approval not found.")
    return approval


def expires_at_utc(approval: Approval) -> datetime:
    value = approval.expires_at
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


@router.get("")
def list_approvals(
    principal: Principal = Depends(require_principal), db: Session = Depends(get_db)
):
    rows = db.scalars(
        select(Approval)
        .where(Approval.organization_id == principal.organization_id)
        .order_by(Approval.created_at.desc())
    ).all()
    return {
        "items": [
            {
                "id": row.id,
                "action_type": row.action_type,
                "status": row.status,
                "expires_at": row.expires_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.post("", status_code=201)
def request_approval(
    body: ApprovalRequest,
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
):
    decision = PolicyEngine().evaluate(
        tool_id=body.action_type, role=principal.role, workspace=principal.workspace, mode="execute"
    )
    if not decision.allowed and not decision.requires_approval:
        raise HTTPException(status_code=403, detail=decision.reason)
    now = datetime.now(UTC)
    approval = Approval(
        run_id=body.run_id,
        organization_id=principal.organization_id,
        requested_by=principal.user_id,
        status="pending",
        action_type=body.action_type,
        payload=json.dumps(body.payload),
        expires_at=now + timedelta(minutes=body.ttl_minutes),
    )
    db.add(approval)
    db.flush()
    record_audit(
        db,
        principal,
        action="approval.requested",
        resource_type="approval",
        resource_id=approval.id,
        outcome="pending",
        details={"action_type": body.action_type},
    )
    db.commit()
    return {
        "id": approval.id,
        "status": approval.status,
        "expires_at": approval.expires_at.isoformat(),
    }


@router.post("/{approval_id}/approve")
def approve(
    approval_id: str,
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
):
    approval = own_approval(db, approval_id, principal)
    if approval.status != "pending" or expires_at_utc(approval) <= datetime.now(UTC):
        raise HTTPException(status_code=409, detail="Approval is expired or not pending.")
    if principal.role not in {"internal_member", "admin"}:
        raise HTTPException(
            status_code=403, detail="Only an internal approver can approve actions."
        )
    approval.status = "approved"
    approval.decided_by = principal.user_id
    approval.decided_at = datetime.now(UTC)
    record_audit(
        db,
        principal,
        action="approval.approved",
        resource_type="approval",
        resource_id=approval.id,
        outcome="approved",
    )
    db.commit()
    return {"id": approval.id, "status": approval.status}


@router.post("/{approval_id}/cancel")
def cancel(
    approval_id: str,
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
):
    approval = own_approval(db, approval_id, principal)
    if approval.status != "pending":
        raise HTTPException(status_code=409, detail="Approval is not pending.")
    approval.status = "cancelled"
    approval.cancelled_at = datetime.now(UTC)
    record_audit(
        db,
        principal,
        action="approval.cancelled",
        resource_type="approval",
        resource_id=approval.id,
        outcome="cancelled",
    )
    db.commit()
    return {"id": approval.id, "status": approval.status}
