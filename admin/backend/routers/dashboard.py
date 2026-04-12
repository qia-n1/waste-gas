from __future__ import annotations

from fastapi import APIRouter, Depends

from routers.auth import get_current_user
from services.vocs_proxy import get_anomaly_heatmap, get_dashboard_overview, get_equipment_status


router = APIRouter(
    prefix="/api/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/overview")
async def overview() -> dict:
    return await get_dashboard_overview()


@router.get("/equipment-status")
async def equipment_status() -> dict:
    return await get_equipment_status()


@router.get("/anomaly-heatmap")
async def anomaly_heatmap(days: int = 7) -> dict:
    return await get_anomaly_heatmap(days=days)
