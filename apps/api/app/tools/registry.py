from dataclasses import dataclass
from typing import Any, Protocol


class ToolAdapter(Protocol):
    def draft(self, arguments: dict[str, Any]) -> dict[str, Any]: ...

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]: ...

    def verify(self, result: dict[str, Any]) -> bool: ...


@dataclass(frozen=True)
class ToolDefinition:
    tool_id: str
    description: str
    input_schema: dict[str, Any]
    allowed_workspaces: frozenset[str]
    allowed_roles: frozenset[str]
    mutating: bool
    adapter: ToolAdapter
    max_retries: int = 1
    rate_limit_per_minute: int = 30


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        if definition.tool_id in self._tools:
            raise ValueError(f"Tool already registered: {definition.tool_id}")
        self._tools[definition.tool_id] = definition

    def get(self, tool_id: str) -> ToolDefinition:
        try:
            return self._tools[tool_id]
        except KeyError as error:
            raise PermissionError("Tool is not approved.") from error

    def authorize(self, tool_id: str, workspace: str, role: str) -> ToolDefinition:
        tool = self.get(tool_id)
        if workspace not in tool.allowed_workspaces or role not in tool.allowed_roles:
            raise PermissionError("Tool is not authorized for this principal.")
        return tool

    def all(self) -> list[ToolDefinition]:
        return list(self._tools.values())
