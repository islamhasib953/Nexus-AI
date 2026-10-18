from typing import Any

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


class RemoteMCPClient:
    """Transport seam for a future remote MCP server; no remote call is made by default."""

    def __init__(self, base_url: str = "") -> None:
        self.base_url = base_url.rstrip("/")

    @property
    def enabled(self) -> bool:
        return bool(self.base_url)

    def call(self, call: ToolCall) -> ToolResult:
        raise RuntimeError("Remote MCP transport is not configured for this environment.")
