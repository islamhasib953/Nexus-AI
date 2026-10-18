from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import Principal, require_principal
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
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    db.commit()
    return result.model_dump()
