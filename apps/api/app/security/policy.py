from dataclasses import dataclass
from datetime import UTC
from enum import StrEnum


class RiskCategory(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    risk: RiskCategory
    requires_approval: bool
    reason: str


class PolicyEngine:
    def evaluate(self, *, tool_id: str, role: str, workspace: str, mode: str) -> PolicyDecision:
        if workspace == "customer":
            if tool_id.startswith("support.") or ".delete" in tool_id:
                return PolicyDecision(
                    False, RiskCategory.high, True, "customer_actions_are_restricted"
                )
            return PolicyDecision(False, RiskCategory.critical, False, "insufficient_role")
        if role not in {"internal_member", "admin"}:
            return PolicyDecision(False, RiskCategory.critical, False, "insufficient_role")
        if ".delete" in tool_id or tool_id.startswith("admin."):
            return PolicyDecision(True, RiskCategory.critical, True, "high_impact_action")
        if mode == "execute" and tool_id.startswith("support."):
            return PolicyDecision(True, RiskCategory.medium, False, "approved_support_operation")
        return PolicyDecision(True, RiskCategory.low, False, "read_or_draft_operation")

    @staticmethod
    def approval_is_valid(status: str, expires_at, now) -> bool:
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        return status == "approved" and expires_at > now
