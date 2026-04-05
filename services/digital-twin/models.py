from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class RiskLevel(str, Enum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class ComponentState:
    name: str
    throughput: float = 0.0          # req/s
    error_rate: float = 0.0          # 0.0 - 1.0
    latency_p95_ms: float = 0.0      # milliseconds
    success_count: float = 0.0
    error_count: float = 0.0
    risk: RiskLevel = RiskLevel.NORMAL
    available: bool = True
    last_updated: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "throughput": round(self.throughput, 2),
            "error_rate": round(self.error_rate, 4),
            "latency_p95_ms": round(self.latency_p95_ms, 2),
            "success_count": round(self.success_count, 2),
            "error_count": round(self.error_count, 2),
            "risk": self.risk.value,
            "available": self.available,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


@dataclass
class SystemState:
    overall_risk: RiskLevel = RiskLevel.NORMAL
    components: dict[str, ComponentState] = field(default_factory=dict)
    last_updated: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "overall_risk": self.overall_risk.value,
            "components": {k: v.to_dict() for k, v in self.components.items()},
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


@dataclass
class Alert:
    component: str
    risk_level: RiskLevel
    reason: str
    metric_value: float
    threshold: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "component": self.component,
            "risk_level": self.risk_level.value,
            "reason": self.reason,
            "metric_value": round(self.metric_value, 4),
            "threshold": round(self.threshold, 4),
            "timestamp": self.timestamp.isoformat(),
        }
