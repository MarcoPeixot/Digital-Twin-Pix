import logging
from datetime import datetime, timezone

from models import Alert, ComponentState, RiskLevel, SystemState

logger = logging.getLogger(__name__)

# Thresholds — explicit and simple per docs requirement
ERROR_RATE_WARNING = 0.05       # 5%
ERROR_RATE_CRITICAL = 0.15      # 15%
LATENCY_P95_WARNING_MS = 500    # 500ms
LATENCY_P95_CRITICAL_MS = 2000  # 2s


class HealthEngine:
    def evaluate(self, components: dict[str, ComponentState]) -> tuple[SystemState, list[Alert]]:
        alerts: list[Alert] = []
        now = datetime.now(timezone.utc)

        for comp in components.values():
            comp.risk = RiskLevel.NORMAL
            component_alerts = self._check_rules(comp)
            if component_alerts:
                alerts.extend(component_alerts)

        # Overall risk = worst component risk
        worst = RiskLevel.NORMAL
        for comp in components.values():
            if comp.risk == RiskLevel.CRITICAL:
                worst = RiskLevel.CRITICAL
                break
            if comp.risk == RiskLevel.WARNING:
                worst = RiskLevel.WARNING

        state = SystemState(
            overall_risk=worst,
            components=components,
            last_updated=now,
        )
        return state, alerts

    def _check_rules(self, comp: ComponentState) -> list[Alert]:
        alerts: list[Alert] = []

        if not comp.available:
            comp.risk = RiskLevel.CRITICAL
            alerts.append(Alert(
                component=comp.name,
                risk_level=RiskLevel.CRITICAL,
                reason="component_unavailable",
                metric_value=0.0,
                threshold=0.0,
            ))
            return alerts

        # Error rate rules
        if comp.error_rate >= ERROR_RATE_CRITICAL:
            comp.risk = RiskLevel.CRITICAL
            alerts.append(Alert(
                component=comp.name,
                risk_level=RiskLevel.CRITICAL,
                reason="error_rate_critical",
                metric_value=comp.error_rate,
                threshold=ERROR_RATE_CRITICAL,
            ))
        elif comp.error_rate >= ERROR_RATE_WARNING:
            comp.risk = max(comp.risk, RiskLevel.WARNING, key=_risk_order)
            alerts.append(Alert(
                component=comp.name,
                risk_level=RiskLevel.WARNING,
                reason="error_rate_warning",
                metric_value=comp.error_rate,
                threshold=ERROR_RATE_WARNING,
            ))

        # Latency p95 rules
        if comp.latency_p95_ms >= LATENCY_P95_CRITICAL_MS:
            comp.risk = max(comp.risk, RiskLevel.CRITICAL, key=_risk_order)
            alerts.append(Alert(
                component=comp.name,
                risk_level=RiskLevel.CRITICAL,
                reason="latency_p95_critical",
                metric_value=comp.latency_p95_ms,
                threshold=LATENCY_P95_CRITICAL_MS,
            ))
        elif comp.latency_p95_ms >= LATENCY_P95_WARNING_MS:
            comp.risk = max(comp.risk, RiskLevel.WARNING, key=_risk_order)
            alerts.append(Alert(
                component=comp.name,
                risk_level=RiskLevel.WARNING,
                reason="latency_p95_warning",
                metric_value=comp.latency_p95_ms,
                threshold=LATENCY_P95_WARNING_MS,
            ))

        return alerts


def _risk_order(level: RiskLevel) -> int:
    return {RiskLevel.NORMAL: 0, RiskLevel.WARNING: 1, RiskLevel.CRITICAL: 2}[level]
