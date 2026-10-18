import json
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from datetime import UTC, datetime, timedelta
from time import monotonic

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import Principal
from app.persistence.models import Approval, ToolExecution
from app.security.audit import record_audit
from app.security.policy import PolicyEngine
from app.tools.contracts import ToolCall, ToolResult
from app.tools.mcp import LocalMCPServer
from app.tools.registry import ToolRegistry


class ToolExecutionService:
    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry
        self.mcp = LocalMCPServer(registry)
        self._calls: dict[tuple[str, str], list[float]] = {}
        self.policy = PolicyEngine()

    def execute(
        self, db: Session, principal: Principal, call: ToolCall, run_id: str | None = None
    ) -> ToolResult:
        existing = db.scalar(
            select(ToolExecution).where(ToolExecution.idempotency_key == call.idempotency_key)
        )
        if existing is not None:
            return ToolResult(
                tool_id=existing.tool_id,
                status="replayed",
                result=json.loads(existing.result_json),
                provider_reference=existing.provider_reference,
                error_code=existing.error_code,
                verified=existing.status == "completed",
            )
        tool = self.registry.authorize(call.tool_id, principal.workspace, principal.role)
        self.mcp.validate_call(call, principal.workspace, principal.role)
        decision = self.policy.evaluate(
            tool_id=call.tool_id,
            role=principal.role,
            workspace=principal.workspace,
            mode=call.mode,
        )
        if not decision.allowed:
            raise PermissionError(decision.reason)
        if decision.requires_approval and call.mode == "execute":
            approval = db.get(Approval, call.approval_id) if call.approval_id else None
            if approval is None:
                approval = Approval(
                    organization_id=principal.organization_id,
                    requested_by=principal.user_id,
                    status="pending",
                    action_type=call.tool_id,
                    payload=json.dumps(call.arguments),
                    expires_at=datetime.now(UTC) + timedelta(minutes=30),
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
                    details={"risk": decision.risk.value},
                )
                return ToolResult(
                    tool_id=call.tool_id, status="pending_approval", approval_id=approval.id
                )
            if (
                approval.organization_id != principal.organization_id
                or approval.action_type != call.tool_id
                or json.loads(approval.payload) != call.arguments
                or not self.policy.approval_is_valid(
                    approval.status, approval.expires_at, datetime.now(UTC)
                )
            ):
                raise PermissionError("Approval is invalid, expired, or does not match the action.")
        now = monotonic()
        rate_key = (principal.user_id, call.tool_id)
        recent = [timestamp for timestamp in self._calls.get(rate_key, []) if now - timestamp < 60]
        if len(recent) >= tool.rate_limit_per_minute:
            raise PermissionError("Tool rate limit exceeded.")
        recent.append(now)
        self._calls[rate_key] = recent
        record = ToolExecution(
            organization_id=principal.organization_id,
            requester_id=principal.user_id,
            run_id=run_id,
            tool_id=call.tool_id,
            idempotency_key=call.idempotency_key,
            status="draft" if call.mode == "draft" else "started",
            request_json=json.dumps(call.arguments),
        )
        db.add(record)
        db.flush()
        try:
            if call.mode == "draft":
                result = self._invoke(
                    tool.adapter.draft, call.arguments, call.timeout_seconds, tool.max_retries
                )
                record.result_json = json.dumps(result)
                record.completed_at = datetime.now(UTC)
                db.flush()
                return ToolResult(
                    tool_id=call.tool_id, status="draft", result=result, verified=False
                )
            result = self._invoke(
                tool.adapter.execute, call.arguments, call.timeout_seconds, tool.max_retries
            )
            verified = tool.adapter.verify(result)
            if not verified:
                raise RuntimeError("provider_result_unverified")
            record.status = "completed"
            record.result_json = json.dumps(result)
            record.provider_reference = str(result.get("ticket_id", "")) or None
            record.completed_at = datetime.now(UTC)
            db.flush()
            return ToolResult(
                tool_id=call.tool_id,
                status="completed",
                result=result,
                provider_reference=record.provider_reference,
                verified=True,
            )
        except ValueError as error:
            record.status = "failed"
            record.error_code = "invalid_arguments"
            record.result_json = json.dumps({"message": str(error)})
            record.completed_at = datetime.now(UTC)
            db.flush()
            return ToolResult(tool_id=call.tool_id, status="failed", error_code=record.error_code)
        except FutureTimeoutError:
            record.status = "failed"
            record.error_code = "tool_timeout"
            record.completed_at = datetime.now(UTC)
            db.flush()
            return ToolResult(tool_id=call.tool_id, status="failed", error_code=record.error_code)
        except Exception:
            record.status = "failed"
            record.error_code = "provider_error"
            record.completed_at = datetime.now(UTC)
            db.flush()
            return ToolResult(tool_id=call.tool_id, status="failed", error_code=record.error_code)

    @staticmethod
    def _invoke(adapter, arguments: dict[str, object], timeout: float, max_retries: int):
        last_error = None
        for _ in range(min(max_retries, 2) + 1):
            executor = ThreadPoolExecutor(max_workers=1)
            future = executor.submit(adapter, arguments)
            try:
                return future.result(timeout=timeout)
            except FutureTimeoutError:
                future.cancel()
                executor.shutdown(wait=False, cancel_futures=True)
                raise
            except Exception as error:
                last_error = error
                executor.shutdown(wait=True, cancel_futures=True)
        raise last_error or RuntimeError("tool_execution_failed")
