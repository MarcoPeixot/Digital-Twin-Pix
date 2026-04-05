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
current_state = SystemState()

# Own metrics
twin_alerts_total = Counter(
    "twin_alerts_total", "Alerts emitted by digital twin", ["risk_level"]
)
twin_evaluation_duration = Histogram(
    "twin_evaluation_duration_seconds", "Time to evaluate system state"
)


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

            logger.info(
                "State updated: overall_risk=%s components=%d alerts=%d",
                state.overall_risk.value,
                len(state.components),
                len(alerts),
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


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(), media_type="text/plain; version=0.0.4")
