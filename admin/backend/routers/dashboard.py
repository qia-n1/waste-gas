from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException

from config import settings
from routers.auth import get_current_user
from services.vocs_proxy import (
    call_ensemble_predict,
    get_anomaly_heatmap,
    get_dashboard_overview,
    get_emitter_history,
    get_equipment_status,
)


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


@router.get("/emitter-history/{emitter_id}")
async def emitter_history(emitter_id: str, limit: int = 48) -> dict:
    """Return recent history points for a single emitter, used by the
    FactoryScene popup that opens when a building label is clicked."""
    result = await get_emitter_history(emitter_id, limit=limit)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unknown emitter: {emitter_id}")
    return result


@router.post("/predict")
async def ensemble_predict() -> dict:
    result = await call_ensemble_predict()
    if result is None:
        return {"status": "error", "message": "集成模型服务不可用或历史数据不足96步"}
    return result


@router.get("/ensemble-health")
async def ensemble_health() -> dict:
    try:
        async with httpx.AsyncClient(
            base_url=settings.ensemble_base_url,
            timeout=3,
        ) as client:
            response = await client.get("/health")
            response.raise_for_status()
            return {"connected": True, **response.json()}
    except httpx.HTTPError:
        return {"connected": False, "status": "unreachable"}
