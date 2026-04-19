"""Admin-side Server-Sent Events.

Currently exposes a single stream pushing watchdog-generated device alerts
in real time so the frontend AlarmCenter doesn't have to wait for the next
30s polling tick.
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from services.device_watchdog import watchdog

router = APIRouter(prefix="/api/events", tags=["events"])


def _format_event(event: str, data: dict | str) -> str:
    payload = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


@router.get("/device-alerts")
async def device_alerts_stream(request: Request) -> StreamingResponse:
    """SSE stream that emits a `device_alert` event each time the watchdog
    raises a new device-offline / recovery alert."""

    async def generator() -> AsyncIterator[str]:
        queue = watchdog.subscribe()
        try:
            # Initial hello so the client transitions to "connected".
            yield _format_event("connected", watchdog.status())

            while True:
                if await request.is_disconnected():
                    break
                try:
                    alert = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield _format_event("device_alert", alert)
                except asyncio.TimeoutError:
                    # Heartbeat keeps proxies and EventSource happy.
                    yield ": ping\n\n"
        finally:
            watchdog.unsubscribe(queue)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/device-status")
async def device_status() -> dict:
    """Snapshot of the watchdog state — useful for diagnostics / health checks."""
    return watchdog.status()
