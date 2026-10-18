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
    confidence: float
    explanation: str


class RequestClassifier:
    CURRENT_DATA = re.compile(r"\b(now|today|latest|current|live|آخر|اليوم|حالي|الآن)\b", re.I)
    ACTION = re.compile(r"\b(send|delete|create|update|book|شراء|احذف|أنشئ|أرسل)\b", re.I)
    RETRIEVAL = re.compile(r"\b(document|policy|file|knowledge|contract|مستند|سياسة|ملف)\b", re.I)

    def classify(self, prompt: str) -> RouteDecision:
        normalized = prompt.strip()
        current = bool(self.CURRENT_DATA.search(normalized))
        action = bool(self.ACTION.search(normalized))
        retrieval = bool(self.RETRIEVAL.search(normalized))
        if action:
            confidence = 0.74 if current or retrieval else 0.96
            signals = [
                name
                for name, present in (("current-data", current), ("retrieval", retrieval))
                if present
            ]
            suffix = f"; ambiguous signals: {', '.join(signals)}" if signals else ""
            return RouteDecision(
                "action",
                False,
                "mutating_or_tool_request",
                True,
                False,
                True,
                confidence,
                f"Action intent matched an allowlisted action signal{suffix}.",
            )
        if current:
            return RouteDecision(
                "current_data",
                False,
                "time_sensitive",
                True,
                False,
                False,
                0.98,
                "Current-data signal requires a fresh, non-cacheable path.",
            )
        if retrieval:
            # Retrieval answers must not be served from a stale response cache after
            # a document update or deletion; source-aware caching can be added later.
            return RouteDecision(
                "retrieval",
                False,
                "authorized_source_freshness",
                True,
                True,
                False,
                0.91,
                "Knowledge-source signal requires authorized retrieval.",
            )
        return RouteDecision(
            "direct_model",
            True,
            None,
            False,
            False,
            False,
            0.70 if normalized else 0.20,
            "No specialized signal matched; direct model path is the bounded fallback.",
        )
