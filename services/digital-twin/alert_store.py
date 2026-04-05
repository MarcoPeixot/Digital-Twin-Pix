from collections import deque

from models import Alert

MAX_ALERTS = 500


class AlertStore:
    def __init__(self, max_size: int = MAX_ALERTS):
        self._alerts: deque[Alert] = deque(maxlen=max_size)

    def add(self, alert: Alert) -> None:
        self._alerts.append(alert)

    def add_many(self, alerts: list[Alert]) -> None:
        for a in alerts:
            self._alerts.append(a)

    def get_all(self) -> list[Alert]:
        return list(self._alerts)

    def get_recent(self, n: int = 50) -> list[Alert]:
        items = list(self._alerts)
        return items[-n:]

    def count(self) -> int:
        return len(self._alerts)

    def clear(self) -> None:
        self._alerts.clear()
