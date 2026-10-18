from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from statistics import mean

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.llm.router import ModelRouter
from app.persistence.models import (
    AgentExecutionMetric,
    DocumentChunk,
    ModelUsage,
    RoutingDecisionLog,
    Run,
    ToolExecution,
)


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _cost(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation:
        return Decimal("0")


class OperationsService:
    """Produces a tenant-scoped snapshot from durable records; it does not emit secrets."""

    def __init__(self, settings: Settings, model_router: ModelRouter) -> None:
        self.settings = settings
        self.model_router = model_router

    def overview(self, db: Session, organization_id: str) -> dict[str, object]:
        now = datetime.now(UTC)
        since = now - timedelta(hours=self.settings.metrics_window_hours)
        runs = db.scalars(
            select(Run).where(Run.organization_id == organization_id, Run.created_at >= since)
        ).all()
        usages = db.scalars(
            select(ModelUsage).where(
                ModelUsage.organization_id == organization_id, ModelUsage.created_at >= since
            )
        ).all()
        tools = db.scalars(
            select(ToolExecution).where(
                ToolExecution.organization_id == organization_id,
                ToolExecution.created_at >= since,
            )
        ).all()
        routes = db.scalars(
            select(RoutingDecisionLog).where(
                RoutingDecisionLog.organization_id == organization_id,
                RoutingDecisionLog.created_at >= since,
            )
        ).all()
        agents = db.scalars(
            select(AgentExecutionMetric).where(
                AgentExecutionMetric.organization_id == organization_id,
                AgentExecutionMetric.created_at >= since,
            )
        ).all()

        costs_by_provider: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        costs_by_model: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        run_to_agent = {record.run_id: record.agent_id for record in agents}
        run_to_task = {record.run_id: record.route_kind for record in routes if record.run_id}
        costs_by_agent: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        costs_by_task: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        total_cost = Decimal("0")
        for usage in usages:
            amount = _cost(usage.estimated_cost_usd)
            total_cost += amount
            costs_by_provider[usage.provider] += amount
            costs_by_model[usage.model_id] += amount
            if usage.run_id and usage.run_id in run_to_agent:
                costs_by_agent[run_to_agent[usage.run_id]] += amount
            if usage.run_id and usage.run_id in run_to_task:
                costs_by_task[run_to_task[usage.run_id]] += amount

        completed_durations = [
            (_utc(run.completed_at) - _utc(run.started_at)).total_seconds() * 1000
            for run in runs
            if run.started_at and run.completed_at
        ]
        queued = [run for run in runs if run.status == "queued"]
        queue_ages = [(now - _utc(run.created_at)).total_seconds() for run in queued]
        failed_runs = sum(run.status == "failed" for run in runs)
        failed_tools = sum(tool.status == "failed" for tool in tools)
        cache_hits = sum(route.cache_status == "hit" for route in routes)
        providers = {item.provider for item in usages} | {
            model.provider for model in self.model_router.registry.all()
        }
        summary = {
            "runs_total": len(runs),
            "runs_failed": failed_runs,
            "run_error_rate": _rate(failed_runs, len(runs)),
            "queue_depth": len(queued),
            "queue_oldest_seconds": round(max(queue_ages), 2) if queue_ages else 0.0,
            "run_duration_avg_ms": round(mean(completed_durations), 2)
            if completed_durations
            else 0.0,
            "tool_calls_total": len(tools),
            "tool_failure_rate": _rate(failed_tools, len(tools)),
            "cache_hit_rate": _rate(cache_hits, len(routes)),
            "routing_latency_avg_ms": round(mean([route.latency_ms for route in routes]), 2)
            if routes
            else 0.0,
            "documents_indexed_chunks": db.scalar(
                select(func.count(DocumentChunk.id)).where(
                    DocumentChunk.organization_id == organization_id
                )
            )
            or 0,
        }
        return {
            "generated_at": now.isoformat(),
            "window_hours": self.settings.metrics_window_hours,
            "organization_id": organization_id,
            "summary": summary,
            "cost": {
                "estimated_usd": f"{total_cost:.8f}",
                "by_provider": self._currency_map(costs_by_provider),
                "by_model": self._currency_map(costs_by_model),
                "by_agent": self._currency_map(costs_by_agent),
                "by_task": self._currency_map(costs_by_task),
            },
            "agents": self._agent_breakdown(agents),
            "providers": self.model_router.health.snapshot(providers),
        }

    def alerts(self, overview: dict[str, object]) -> list[dict[str, object]]:
        summary = overview["summary"]
        assert isinstance(summary, dict)
        alerts: list[dict[str, object]] = []
        if summary["queue_depth"] >= self.settings.ops_queue_warning_threshold:
            alerts.append(
                self._alert("queue_depth", "warning", "Queued runs exceed the warning threshold.")
            )
        if summary["run_error_rate"] > self.settings.ops_error_rate_critical_threshold:
            alerts.append(
                self._alert("run_error_rate", "critical", "Run error rate breaches the SLO.")
            )
        if summary["tool_failure_rate"] > self.settings.ops_tool_failure_critical_threshold:
            alerts.append(
                self._alert("tool_failure_rate", "critical", "Tool failure rate breaches the SLO.")
            )
        for provider in overview["providers"]:
            assert isinstance(provider, dict)
            if not provider["available"]:
                alerts.append(
                    self._alert(
                        f"provider:{provider['provider']}",
                        "warning",
                        "Provider circuit is open; fallback policy is active.",
                    )
                )
        return alerts

    @staticmethod
    def _currency_map(values: dict[str, Decimal]) -> dict[str, str]:
        return {key: f"{value:.8f}" for key, value in sorted(values.items())}

    @staticmethod
    def _agent_breakdown(records: list[AgentExecutionMetric]) -> list[dict[str, object]]:
        grouped: dict[str, list[AgentExecutionMetric]] = defaultdict(list)
        for record in records:
            grouped[record.agent_id].append(record)
        return [
            {
                "agent_id": agent_id,
                "runs": len(items),
                "failed": sum(item.status == "failed" for item in items),
                "average_duration_ms": round(mean([item.duration_ms for item in items]), 2),
                "input_tokens": sum(item.input_tokens for item in items),
                "output_tokens": sum(item.output_tokens for item in items),
            }
            for agent_id, items in sorted(grouped.items())
        ]

    @staticmethod
    def _alert(rule_id: str, severity: str, message: str) -> dict[str, object]:
        return {"rule_id": rule_id, "severity": severity, "message": message}
