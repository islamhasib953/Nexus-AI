import uuid
from typing import Any


class SupportTicketAdapter:
    """Deterministic local business adapter; replaceable by Jira/Linear/CRM later."""

    def draft(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self._validate(arguments)
        return {
            "operation": "create_ticket",
            "title": arguments["title"],
            "description": arguments["description"],
            "mode": "draft",
        }

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        self._validate(arguments)
        ticket_id = f"TCK-{uuid.uuid4().hex[:10].upper()}"
        return {
            "ticket_id": ticket_id,
            "title": arguments["title"],
            "description": arguments["description"],
            "status": "created",
        }

    def verify(self, result: dict[str, Any]) -> bool:
        return result.get("status") == "created" and bool(result.get("ticket_id"))

    @staticmethod
    def _validate(arguments: dict[str, Any]) -> None:
        if not isinstance(arguments.get("title"), str) or not arguments["title"].strip():
            raise ValueError("title is required")
        if (
            not isinstance(arguments.get("description"), str)
            or not arguments["description"].strip()
        ):
            raise ValueError("description is required")
