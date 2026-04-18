from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from routers.auth import get_current_user
from services.vocs_proxy import acknowledge_alert, get_alert_diagnosis, get_alerts


router = APIRouter(
    prefix="/api/alerts",
    tags=["alerts"],
    dependencies=[Depends(get_current_user)],
)


@router.get("")
async def alerts(
    limit: int = Query(default=30, ge=1, le=100),
    search: str = "",
    level: str = "",
) -> dict:
    return await get_alerts(limit=limit, search=search, level=level)


@router.post("/{alert_id}/acknowledge")
async def acknowledge(alert_id: str) -> dict:
    return await acknowledge_alert(alert_id)


@router.get("/{alert_id}/diagnosis")
async def diagnosis(alert_id: str) -> dict:
    return await get_alert_diagnosis(alert_id)
