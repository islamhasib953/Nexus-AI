from app.tools.integrations import SupportTicketAdapter
from app.tools.registry import ToolDefinition, ToolRegistry


def build_tool_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            tool_id="support.create_ticket",
            description="Create a support ticket in the approved support system.",
            input_schema={"type": "object", "required": ["title", "description"]},
            allowed_workspaces=frozenset({"internal"}),
            allowed_roles=frozenset({"internal_member"}),
            mutating=True,
            adapter=SupportTicketAdapter(),
        )
    )
    return registry
