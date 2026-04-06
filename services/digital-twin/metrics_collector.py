import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from models import ComponentState

logger = logging.getLogger(__name__)

# Mapping: component name -> (metric prefix, success tag value, error tag value)
COMPONENT_METRICS = {
    "api-gateway": {
        "counter": "twinpix_transactions_total",
        "timer": "twinpix_transaction_duration_seconds",
        "success_status": "success",
        "error_status": "error",
    },
    "directory": {
        "counter": "twinpix_key_lookups_total",
        "timer": "twinpix_key_lookup_duration_seconds",
        "success_status": "success",
        "error_status": "error",
    },
    "processing-core": {
        "counter": "twinpix_processing_total",
        "timer": "twinpix_processing_duration_seconds",
        "success_status": "success",
        "error_status": "error",
    },
}


class MetricsCollector:
    def __init__(self, prometheus_url: str):
        self.prometheus_url = prometheus_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=5.0)

    async def _query(self, promql: str) -> Optional[float]:
        try:
            resp = await self.client.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": promql},
            )
            data = resp.json()
            if data["status"] == "success" and data["data"]["result"]:
                return float(data["data"]["result"][0]["value"][1])
        except Exception as e:
            logger.warning("Prometheus query failed for '%s': %s", promql, e)
        return None

    async def collect_component(self, component: str) -> ComponentState:
        cfg = COMPONENT_METRICS[component]
        now = datetime.now(timezone.utc)

        # Rate of success over last 1 minute
        success_rate = await self._query(
            f'rate({cfg["counter"]}{{status="{cfg["success_status"]}"}}[1m])'
        )
        # Rate of errors over last 1 minute
        error_rate_val = await self._query(
            f'rate({cfg["counter"]}{{status="{cfg["error_status"]}"}}[1m])'
        )
        # Absolute counters
        success_count = await self._query(
            f'{cfg["counter"]}{{status="{cfg["success_status"]}"}}'
        )
        error_count = await self._query(
            f'{cfg["counter"]}{{status="{cfg["error_status"]}"}}'
        )
        # p95 latency — Micrometer publishPercentiles() exports pre-computed
        # gauge with quantile tag, NOT histogram buckets.
        latency_p95 = await self._query(
            f'{cfg["timer"]}{{quantile="0.95"}}'
        )

        throughput = (success_rate or 0.0) + (error_rate_val or 0.0)
        total_rate = throughput if throughput > 0 else 0.0
        error_ratio = (error_rate_val or 0.0) / total_rate if total_rate > 0 else 0.0

        available = success_rate is not None or error_rate_val is not None

        return ComponentState(
            name=component,
            throughput=throughput,
            error_rate=error_ratio,
            latency_p95_ms=(latency_p95 or 0.0) * 1000,  # seconds -> ms
            success_count=success_count or 0.0,
            error_count=error_count or 0.0,
            available=available,
            last_updated=now,
        )

    async def collect_all(self) -> dict[str, ComponentState]:
        states = {}
        for component in COMPONENT_METRICS:
            states[component] = await self.collect_component(component)
        return states

    async def close(self):
        await self.client.aclose()
