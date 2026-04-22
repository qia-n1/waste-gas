"""Device data watchdog.

Polls the upstream VOCs service for the latest sensor payload. If no fresh
sensor data has been observed for `DEVICE_TIMEOUT_SECONDS`, an alert is
generated and broadcast to in-process listeners (used by the admin SSE
endpoint) and stored in an in-memory deque so it appears in the next
`/api/alerts` response consumed by `AlarmCenter.vue`.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)

DEVICE_TIMEOUT_SECONDS = 90
CHECK_INTERVAL_SECONDS = 10
ALERT_BUFFER = 50


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone().isoformat(timespec="seconds")


class DeviceWatchdog:
    """Tracks sensor heartbeat freshness; emits offline / recovery alerts."""

    def __init__(self) -> None:
        self._last_seen: Optional[datetime] = None
        self._is_online: bool = True
        self._alerts: Deque[Dict[str, Any]] = deque(maxlen=ALERT_BUFFER)
        self._listeners: List[asyncio.Queue[Dict[str, Any]]] = []
        self._task: Optional[asyncio.Task] = None
        self._stopping = False

    # ------------------------------------------------------------------ heartbeat
    def heartbeat(self, when: Optional[datetime] = None) -> None:
        ts = when or _now()
        was_offline = not self._is_online
        self._last_seen = ts
        self._is_online = True
        if was_offline:
            self._emit_alert(
                level="info",
                message="设备数据通信已恢复，传感器重新上报。",
                recovered=True,
            )

    # ------------------------------------------------------------------ alerts
    def _emit_alert(self, *, level: str, message: str, recovered: bool = False) -> None:
        alert: Dict[str, Any] = {
            "alert_id": f"WATCHDOG-{int(_now().timestamp() * 1000)}",
            "timestamp": _iso(_now()),
            "level": level,
            "message": message,
            "value": 0.0,
            "threshold": float(DEVICE_TIMEOUT_SECONDS),
            "acknowledged": False,
            "location": "传感器网关",
            "status": "已恢复" if recovered else "处理中",
            "source": "device_watchdog",
        }
        self._alerts.appendleft(alert)
        for queue in list(self._listeners):
            try:
                queue.put_nowait(alert)
            except asyncio.QueueFull:
                logger.warning("device_watchdog listener queue full, dropping alert")

    def list_alerts(self) -> List[Dict[str, Any]]:
        return list(self._alerts)

    def status(self) -> Dict[str, Any]:
        elapsed: Optional[float] = None
        if self._last_seen is not None:
            elapsed = (_now() - self._last_seen).total_seconds()
        return {
            "online": self._is_online,
            "lastSeen": _iso(self._last_seen) if self._last_seen else None,
            "elapsedSeconds": round(elapsed, 1) if elapsed is not None else None,
            "timeoutThreshold": DEVICE_TIMEOUT_SECONDS,
            "checkInterval": CHECK_INTERVAL_SECONDS,
            "bufferedAlerts": len(self._alerts),
        }

    # ------------------------------------------------------------------ pubsub
    def subscribe(self) -> asyncio.Queue[Dict[str, Any]]:
        queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=64)
        self._listeners.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[Dict[str, Any]]) -> None:
        try:
            self._listeners.remove(queue)
        except ValueError:
            pass

    # ------------------------------------------------------------------ loop
    async def _poll_once(self) -> None:
        # Imported lazily to avoid circular import (vocs_proxy may import settings only)
        from services import vocs_proxy

        try:
            sensor = await vocs_proxy.fetch_latest_sensor()
        except Exception as exc:  # noqa: BLE001
            logger.debug("watchdog poll failed: %s", exc)
            sensor = None

        if sensor and sensor.get("timestamp"):
            self.heartbeat()
            return

        # No fresh data this tick — check whether we crossed the timeout
        reference = self._last_seen
        if reference is None:
            # Treat startup as the reference so the first alert fires after
            # DEVICE_TIMEOUT_SECONDS of continued silence.
            self._last_seen = _now()
            return

        elapsed = (_now() - reference).total_seconds()
        if elapsed > DEVICE_TIMEOUT_SECONDS and self._is_online:
            self._is_online = False
            self._emit_alert(
                level="critical",
                message=(
                    f"设备数据采集已中断 {int(elapsed)} 秒，超过 {DEVICE_TIMEOUT_SECONDS}s 阈值，"
                    "请立即检查传感器与上行网关。"
                ),
            )

    async def _loop(self) -> None:
        logger.info(
            "device_watchdog started: timeout=%ss interval=%ss",
            DEVICE_TIMEOUT_SECONDS,
            CHECK_INTERVAL_SECONDS,
        )
        while not self._stopping:
            try:
                await self._poll_once()
            except asyncio.CancelledError:
                break
            except Exception as exc:  # noqa: BLE001
                logger.exception("device_watchdog tick error: %s", exc)
            try:
                await asyncio.sleep(CHECK_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                break
        logger.info("device_watchdog stopped")

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._stopping = False
            self._task = asyncio.create_task(self._loop(), name="device_watchdog")

    async def stop(self) -> None:
        self._stopping = True
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


# Module-level singleton
watchdog = DeviceWatchdog()
