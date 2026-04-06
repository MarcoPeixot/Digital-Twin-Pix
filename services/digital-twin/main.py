import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import PlainTextResponse

from alert_store import AlertStore
from health_engine import HealthEngine
from metrics_collector import MetricsCollector
from mitigation import MitigationEngine, MitigationAction, RecommendationStore
from models import RiskLevel, SystemState

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
POLL_INTERVAL = int(os.getenv("TWIN_POLL_INTERVAL_SECONDS", "5"))

collector = MetricsCollector(PROMETHEUS_URL)
engine = HealthEngine()
store = AlertStore()
mitigation_engine = MitigationEngine()
recommendation_store = RecommendationStore()
current_state = SystemState()

# Own metrics
twin_alerts_total = Counter(
    "twin_alerts_total", "Alerts emitted by digital twin", ["risk_level"]
)
twin_recommendations_total = Counter(
    "twin_recommendations_total",
    "Mitigation recommendations emitted by digital twin",
    ["action"],
)
twin_evaluation_duration = Histogram(
    "twin_evaluation_duration_seconds", "Time to evaluate system state"
)

# Pre-register all labeled series so baseline runs expose explicit zeros.
for risk_level in RiskLevel:
    twin_alerts_total.labels(risk_level=risk_level.value).inc(0)

for action in MitigationAction:
    twin_recommendations_total.labels(action=action.value).inc(0)


async def poll_loop():
    while True:
        try:
            with twin_evaluation_duration.time():
                components = await collector.collect_all()
                state, alerts = engine.evaluate(components)

            global current_state
            current_state = state

            if alerts:
                store.add_many(alerts)
                for a in alerts:
                    twin_alerts_total.labels(risk_level=a.risk_level.value).inc()
                    logger.warning(
                        "ALERT [%s] %s: %s (value=%.4f, threshold=%.4f)",
                        a.risk_level.value,
                        a.component,
                        a.reason,
                        a.metric_value,
                        a.threshold,
                    )

            # Mitigation: evaluate recommendations based on current state
            recommendations = mitigation_engine.evaluate(state, alerts)
            if recommendations:
                recommendation_store.add_many(recommendations)
                for rec in recommendations:
                    twin_recommendations_total.labels(action=rec.action.value).inc()
                    logger.warning(
                        "RECOMMENDATION [%s] %s -> %s: %s (mode=%s)",
                        rec.trigger_risk.value,
                        rec.target_component,
                        rec.action.value,
                        rec.reason,
                        rec.mode.value,
                    )

            logger.info(
                "State updated: overall_risk=%s components=%d alerts=%d recommendations=%d",
                state.overall_risk.value,
                len(state.components),
                len(alerts),
                len(recommendations),
            )
        except Exception:
            logger.exception("Poll loop error")

        await asyncio.sleep(POLL_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(poll_loop())
    yield
    task.cancel()
    await collector.close()


app = FastAPI(title="digital-twin", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "up", "service": "digital-twin"}


@app.get("/state")
def get_state():
    return current_state.to_dict()


@app.get("/alerts")
def get_alerts(
    limit: int = Query(50, ge=1, le=500),
    risk_level: RiskLevel | None = Query(None),
):
    alerts = store.get_recent(limit)
    if risk_level:
        alerts = [a for a in alerts if a.risk_level == risk_level]
    return {
        "total_stored": store.count(),
        "returned": len(alerts),
        "alerts": [a.to_dict() for a in alerts],
    }


@app.get("/recommendations")
def get_recommendations(
    limit: int = Query(50, ge=1, le=500),
    action: MitigationAction | None = Query(None),
):
    recs = recommendation_store.get_recent(limit)
    if action:
        recs = [r for r in recs if r.action == action]
    return {
        "total_stored": recommendation_store.count(),
        "returned": len(recs),
        "recommendations": [r.to_dict() for r in recs],
    }


@app.get("/mitigation/status")
def mitigation_status():
    cooldown = engine.cooldown_status
    elevated = engine.elevated_components
    return {
        "mode": mitigation_engine.mode.value,
        "active_recommendations": len(mitigation_engine._active),
        "total_recommendations": recommendation_store.count(),
        "active_details": [
            {"component": comp, "action": action.value, "risk": risk.value}
            for (comp, action), risk in mitigation_engine._active.items()
        ],
        # Elevated — split by role:
        #   root_cause: component itself is down (isolate target)
        #   degraded:   threshold breach, likely propagation from root cause
        "elevated": {
            name: {"category": category}
            for name, category in elevated.items()
        },
        # Cooldown: components whose metrics normalised; twin keeps risk at
        # WARNING for a few cycles to confirm stable recovery.
        "cooldown_recovery": {
            name: {"remaining_cycles": remaining}
            for name, remaining in cooldown.items()
        },
        # Persistent log of recent cooldown transitions — survives the
        # short active window so it's observable even with slow polling.
        "cooldown_log": engine.cooldown_log,
    }


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(), media_type="text/plain; version=0.0.4")
