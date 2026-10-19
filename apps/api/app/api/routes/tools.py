from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_principal
from app.security.audit import record_audit
from app.tools.contracts import ToolCall
from app.tools.service import ToolExecutionService

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


def get_db(request: Request):
    yield from request.app.state.database.sessions()


@router.get("")
def list_tools(request: Request, principal: Principal = Depends(require_principal)):
    service: ToolExecutionService = request.app.state.tools
    return {"items": service.mcp.list_tools(principal.workspace, principal.role)}


@router.post("/execute")
def execute_tool(
    call: ToolCall,
    request: Request,
    principal: Principal = Depends(require_principal),
    db: Session = Depends(get_db),
):
    service: ToolExecutionService = request.app.state.tools
    try:
        result = service.execute(db, principal, call)
        record_audit(
            db,
            principal,
            action="tool.execute",
            resource_type="tool",
            resource_id=call.tool_id,
            outcome="success",
            details={"status": result.status},
        )
    except PermissionError as error:
        record_audit(
            db,
            principal,
            action="tool.execute",
            resource_type="tool",
            resource_id=call.tool_id,
            outcome="denied",
            details={"error": str(error)},
        )
        db.commit()
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        record_audit(
            db,
            principal,
            action="tool.execute",
            resource_type="tool",
            resource_id=call.tool_id,
            outcome="invalid",
            details={"error": str(error)},
        )
        db.commit()
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return result.model_dump()
