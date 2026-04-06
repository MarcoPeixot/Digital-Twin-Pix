import logging
from collections import deque
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from models import Alert, ComponentState, RiskLevel, SystemState

logger = logging.getLogger(__name__)


class MitigationAction(str, Enum):
    THROTTLE_INPUT = "THROTTLE_INPUT"
    SCALE_WORKERS = "SCALE_WORKERS"
    ISOLATE_COMPONENT = "ISOLATE_COMPONENT"


class MitigationMode(str, Enum):
    ADVISORY = "ADVISORY"
    AUTOMATIC = "AUTOMATIC"


@dataclass
class Recommendation:
    action: MitigationAction
    target_component: str
    reason: str
    trigger_risk: RiskLevel
    mode: MitigationMode = MitigationMode.ADVISORY
    executed: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "action": self.action.value,
            "target_component": self.target_component,
            "reason": self.reason,
            "trigger_risk": self.trigger_risk.value,
            "mode": self.mode.value,
            "executed": self.executed,
            "timestamp": self.timestamp.isoformat(),
        }


MAX_RECOMMENDATIONS = 500


class RecommendationStore:
    def __init__(self, max_size: int = MAX_RECOMMENDATIONS):
        self._items: deque[Recommendation] = deque(maxlen=max_size)

    def add(self, rec: Recommendation) -> None:
        self._items.append(rec)

    def add_many(self, recs: list[Recommendation]) -> None:
        for r in recs:
            self._items.append(r)

    def get_recent(self, n: int = 50) -> list[Recommendation]:
        items = list(self._items)
        return items[-n:]

    def count(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()


# Thresholds — reuse from health_engine for consistency
from health_engine import (
    ERROR_RATE_CRITICAL,
    ERROR_RATE_WARNING,
    LATENCY_P95_CRITICAL_MS,
    LATENCY_P95_WARNING_MS,
)


class MitigationEngine:
    """Rule-based mitigation recommender.

    Maps risk conditions detected in component state to concrete
    mitigation actions. Operates in advisory mode by default —
    recommendations are logged but not executed.

    Rules are explicit, simple, and academically explainable:
    - CRITICAL error rate or latency -> THROTTLE_INPUT
    - Component unavailable -> ISOLATE_COMPONENT
    - WARNING error rate + WARNING latency combined -> SCALE_WORKERS
    """

    def __init__(self, mode: MitigationMode = MitigationMode.ADVISORY):
        self.mode = mode
        # Dedup: track active recommendations per (component, action) to avoid
        # recommending the same action every poll cycle
        self._active: dict[tuple[str, MitigationAction], RiskLevel] = {}

    def evaluate(
        self, state: SystemState, alerts: list[Alert]
    ) -> list[Recommendation]:
        if state.overall_risk == RiskLevel.NORMAL:
            self._active.clear()
            return []

        recommendations: list[Recommendation] = []
        new_active: dict[tuple[str, MitigationAction], RiskLevel] = {}

        for comp in state.components.values():
            comp_recs = self._apply_rules(comp)
            for rec in comp_recs:
                key = (rec.target_component, rec.action)
                new_active[key] = rec.trigger_risk
                # Only emit if new condition
                if key not in self._active:
                    recommendations.append(rec)

        self._active = new_active
        return recommendations

    def _apply_rules(self, comp: ComponentState) -> list[Recommendation]:
        # Rule 1: Component unavailable (or functionally unavailable) -> ISOLATE
        # Health engine already sets available=False for functional unavailability.
        if not comp.available:
            return [Recommendation(
                action=MitigationAction.ISOLATE_COMPONENT,
                target_component=comp.name,
                reason="component_unavailable — isolate to prevent cascading failure",
                trigger_risk=RiskLevel.CRITICAL,
                mode=self.mode,
            )]

        recs: list[Recommendation] = []
        has_critical = False

        # Rules 2+3: CRITICAL error rate or latency -> single THROTTLE_INPUT
        # Merged into one recommendation to avoid duplicates within the same cycle.
        throttle_reasons: list[str] = []

        if comp.error_rate >= ERROR_RATE_CRITICAL:
            has_critical = True
            throttle_reasons.append(
                f"error_rate={comp.error_rate:.2%} >= {ERROR_RATE_CRITICAL:.0%}"
            )

        if comp.latency_p95_ms >= LATENCY_P95_CRITICAL_MS:
            has_critical = True
            throttle_reasons.append(
                f"latency_p95={comp.latency_p95_ms:.0f}ms >= {LATENCY_P95_CRITICAL_MS}ms"
            )

        if throttle_reasons:
            recs.append(Recommendation(
                action=MitigationAction.THROTTLE_INPUT,
                target_component=comp.name,
                reason=" + ".join(throttle_reasons) + " — reduce input load",
                trigger_risk=RiskLevel.CRITICAL,
                mode=self.mode,
            ))

        # Rule 4: WARNING error rate + WARNING latency combined -> SCALE_WORKERS
        # Only when NO critical conditions exist — scaling workers cannot
        # resolve severe failures or dependency outages.
        if (
            not has_critical
            and comp.error_rate >= ERROR_RATE_WARNING
            and comp.latency_p95_ms >= LATENCY_P95_WARNING_MS
        ):
            recs.append(Recommendation(
                action=MitigationAction.SCALE_WORKERS,
                target_component=comp.name,
                reason=(
                    f"error_rate={comp.error_rate:.2%} and latency_p95={comp.latency_p95_ms:.0f}ms "
                    f"both at WARNING — scale workers to absorb load"
                ),
                trigger_risk=RiskLevel.WARNING,
                mode=self.mode,
            ))

        return recs
