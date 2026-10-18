from typing import Any

import httpx

from app.tools.contracts import ToolCall, ToolResult
from app.tools.registry import ToolRegistry


class LocalMCPServer:
    """MCP-shaped local boundary: schema and authorization are enforced server-side."""

    def __init__(self, registry: ToolRegistry) -> None:
        self.registry = registry

    def list_tools(self, workspace: str, role: str) -> list[dict[str, Any]]:
        return [
            {
                "name": tool.tool_id,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            for tool in self.registry.all()
            if workspace in tool.allowed_workspaces and role in tool.allowed_roles
        ]

    def validate_call(self, call: ToolCall, workspace: str, role: str) -> None:
        tool = self.registry.authorize(call.tool_id, workspace, role)
        required = tool.input_schema.get("required", [])
        missing = [field for field in required if field not in call.arguments]
        if missing:
            raise ValueError(f"Missing required tool arguments: {', '.join(missing)}")


class RemoteMCPError(RuntimeError):
    """A remote MCP request failed validation or transport."""


class RemoteMCPClient:
    """Minimal JSON-RPC transport for a remote MCP ``tools/call`` endpoint.

    The client is opt-in and dependency-injected in tests. The application does not
    call a remote server unless a URL is explicitly configured, and a remote result
    is never marked verified by this transport alone.
    """

    def __init__(
        self,
        base_url: str = "",
        *,
        timeout_seconds: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._client = client

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def call(self, call: ToolCall) -> ToolResult:
        if not self.enabled:
            raise RemoteMCPError("Remote MCP transport is not configured for this environment.")
        payload = {
            "jsonrpc": "2.0",
            "id": call.idempotency_key,
            "method": "tools/call",
            "params": {"name": call.tool_id, "arguments": call.arguments},
        }
        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=self.timeout_seconds)
        try:
            response = client.post(self.base_url, json=payload)
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise RemoteMCPError("Remote MCP request failed.") from error
        finally:
            if owns_client:
                client.close()
        if not isinstance(body, dict):
            raise RemoteMCPError("Remote MCP response must be a JSON object.")
        if body.get("jsonrpc") != "2.0" or body.get("id") != call.idempotency_key:
            raise RemoteMCPError("Remote MCP response has an invalid JSON-RPC envelope.")
        if "error" in body:
            error = body["error"]
            message = (
                error.get("message", "Remote MCP tool failed.")
                if isinstance(error, dict)
                else str(error)
            )
            return ToolResult(tool_id=call.tool_id, status="failed", error_code=f"remote:{message}")
        result = body.get("result")
        if not isinstance(result, dict):
            raise RemoteMCPError("Remote MCP response is missing a result object.")
        if result.get("isError") is True:
            return ToolResult(tool_id=call.tool_id, status="failed", error_code="remote_tool_error")
        content = result.get("structuredContent", result.get("content", []))
        return ToolResult(
            tool_id=call.tool_id,
            status="completed",
            result={"content": content},
            verified=False,
        )
