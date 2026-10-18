import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RouteDecision:
    kind: str
    cacheable: bool
    bypass_reason: str | None
    use_conversation_context: bool
    requires_retrieval: bool
    requires_tools: bool


class RequestClassifier:
    CURRENT_DATA = re.compile(r"\b(now|today|latest|current|live|آخر|اليوم|حالي|الآن)\b", re.I)
    ACTION = re.compile(r"\b(send|delete|create|update|book|شراء|احذف|أنشئ|أرسل)\b", re.I)
    RETRIEVAL = re.compile(r"\b(document|policy|file|knowledge|contract|مستند|سياسة|ملف)\b", re.I)

    def classify(self, prompt: str) -> RouteDecision:
        if self.CURRENT_DATA.search(prompt):
            return RouteDecision("current_data", False, "time_sensitive", True, False, False)
        if self.ACTION.search(prompt):
            return RouteDecision("action", False, "mutating_or_tool_request", True, False, True)
        if self.RETRIEVAL.search(prompt):
            # Retrieval answers must not be served from a stale response cache after
            # a document update or deletion; source-aware caching can be added later.
            return RouteDecision(
                "retrieval", False, "authorized_source_freshness", True, True, False
            )
        return RouteDecision("direct_model", True, None, False, False, False)
