import logging
from collections import deque
from datetime import datetime, timezone

from models import Alert, ComponentState, RiskLevel, SystemState

logger = logging.getLogger(__name__)

# Thresholds — explicit and simple per docs requirement
ERROR_RATE_WARNING = 0.05       # 5%
ERROR_RATE_CRITICAL = 0.15      # 15%
LATENCY_P95_WARNING_MS = 500    # 500ms
LATENCY_P95_CRITICAL_MS = 2000  # 2s

# Functional unavailability: if error rate exceeds this threshold the
# component is considered effectively down even if it still emits metrics
# (e.g. processing-core responding but DB unreachable).
FUNCTIONAL_UNAVAIL_THRESHOLD = 0.50  # 50%

# Only components with direct infrastructure dependencies qualify for
# functional unavailability.  api-gateway is excluded because its errors
# typically propagate from downstream — isolating it would mask the root
# cause instead of addressing it.
FUNCTIONAL_UNAVAIL_COMPONENTS = frozenset({"processing-core", "directory"})

# Warmup: ignore first N evaluation cycles to let Prometheus populate
WARMUP_CYCLES = 6  # 6 * 5s = 30s

# Cooldown: after elevated risk, require N consecutive NORMAL evaluations
# before downgrading risk level
COOLDOWN_CYCLES = 3


class HealthEngine:
    def __init__(self):
        self._cycle_count = 0
        # Components currently in active failure.
        # Value = "root_cause" (available=False) or "degraded" (threshold breach).
        self._elevated: dict[str, str] = {}
        # Components in recovery phase: cooldown starts only when metrics
        # normalise, not during the critical condition itself.
        self._cooldown: dict[str, int] = {}
        # Audit log of cooldown events (bounded, newest last)
        self._cooldown_log: deque[dict] = deque(maxlen=50)
        # Track last active alert per (component, reason) for dedup
        self._active_alerts: dict[tuple[str, str], RiskLevel] = {}

    @property
    def warming_up(self) -> bool:
        return self._cycle_count < WARMUP_CYCLES

    def evaluate(self, components: dict[str, ComponentState]) -> tuple[SystemState, list[Alert]]:
        self._cycle_count += 1
        now = datetime.now(timezone.utc)

        if self.warming_up:
            logger.info(
                "Warmup cycle %d/%d — skipping risk evaluation",
                self._cycle_count, WARMUP_CYCLES,
            )
            for comp in components.values():
                comp.risk = RiskLevel.NORMAL
            state = SystemState(
                overall_risk=RiskLevel.NORMAL,
                components=components,
                last_updated=now,
            )
            return state, []

        alerts: list[Alert] = []
        new_active: dict[tuple[str, str], RiskLevel] = {}

        for comp in components.values():
            comp.risk = RiskLevel.NORMAL
            component_alerts = self._check_rules(comp)

            for a in component_alerts:
                key = (a.component, a.reason)
                new_active[key] = a.risk_level
                # Dedup: only emit if this is a new condition
                if key not in self._active_alerts:
                    alerts.append(a)

            # Cooldown logic — two distinct phases:
            #   elevated: component is actively failing (rules_risk != NORMAL)
            #   cooldown: metrics normalised, twin monitors recovery
            rules_risk = comp.risk  # risk set by threshold rules above

            if rules_risk != RiskLevel.NORMAL:
                # Active failure — classify and cancel any recovery cooldown
                category = "root_cause" if not comp.available else "degraded"
                self._elevated[comp.name] = category
                self._cooldown.pop(comp.name, None)
            elif comp.name in self._elevated:
                # Transition: was elevated, now rules say NORMAL → start recovery cooldown
                del self._elevated[comp.name]
                self._cooldown[comp.name] = COOLDOWN_CYCLES
                comp.risk = RiskLevel.WARNING
                self._cooldown_log.append({
                    "component": comp.name,
                    "event": "cooldown_started",
                    "cycles": COOLDOWN_CYCLES,
                    "timestamp": now.isoformat(),
                })
                logger.info(
                    "Cooldown started for %s: %d cycles",
                    comp.name, COOLDOWN_CYCLES,
                )
            elif comp.name in self._cooldown:
                # Already in recovery cooldown — decrement
                remaining = self._cooldown[comp.name]
                if remaining > 1:
                    comp.risk = RiskLevel.WARNING
                    self._cooldown[comp.name] = remaining - 1
                    logger.info(
                        "Cooldown for %s: %d cycles remaining",
                        comp.name, remaining - 1,
                    )
                else:
                    del self._cooldown[comp.name]
                    self._cooldown_log.append({
                        "component": comp.name,
                        "event": "cooldown_ended",
                        "timestamp": now.isoformat(),
                    })
                    logger.info("Cooldown ended for %s", comp.name)

        # Update active alerts tracking
        self._active_alerts = new_active

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

    @property
    def cooldown_status(self) -> dict[str, int]:
        """Remaining cooldown cycles per component (recovery phase only)."""
        return dict(self._cooldown)

    @property
    def cooldown_log(self) -> list[dict]:
        """Recent cooldown events (start/end) for audit."""
        return list(self._cooldown_log)

    @property
    def elevated_components(self) -> dict[str, str]:
        """Components in active failure: name -> 'root_cause' | 'degraded'."""
        return dict(self._elevated)

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

        # Functional unavailability: component responds but most requests
        # fail, indicating a severe dependency issue (e.g. DB down).
        # Only applied to components with direct infrastructure dependencies.
        if (
            comp.name in FUNCTIONAL_UNAVAIL_COMPONENTS
            and comp.error_rate >= FUNCTIONAL_UNAVAIL_THRESHOLD
        ):
            comp.available = False
            comp.risk = RiskLevel.CRITICAL
            alerts.append(Alert(
                component=comp.name,
                risk_level=RiskLevel.CRITICAL,
                reason="functional_unavailability",
                metric_value=comp.error_rate,
                threshold=FUNCTIONAL_UNAVAIL_THRESHOLD,
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
