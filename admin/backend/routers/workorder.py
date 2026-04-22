"""代维工单全流程管理相关接口。

第一期返回 mock 数据，后续可接入云数据库（沿用 services.db 连接池）。
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from routers.auth import get_current_user


router = APIRouter(
    prefix="/api/work-orders",
    tags=["work-orders"],
    dependencies=[Depends(get_current_user)],
)


def _seeded_random(seed: int) -> random.Random:
    """Create a deterministic RNG so the mock page doesn't flicker on refresh."""
    return random.Random(seed)


@router.get("/overview")
async def overview() -> dict:
    rng = _seeded_random(20260421)
    total_this_month = 128
    total_last_month = 142
    return {
        "month": datetime.now().strftime("%Y-%m"),
        "totalThisMonth": total_this_month,
        "totalLastMonth": total_last_month,
        "momChangePct": round((total_this_month - total_last_month) / total_last_month * 100, 1),
        "firstFixRate": 0.782,
        "avgResponseHours": 1.24,
        "avgResolutionHours": 4.8,
        "pendingCount": 17,
        "overdueCount": 3,
        "photoCount": 1286,
        "updatedAt": datetime.now().isoformat(),
        "kpiNotes": [
            "本月新增工单较上月下降 9.9%",
            "一次性修复率较上月提升 3.2pp",
            "严重程度 P1/P2 工单平均响应 0.8 小时",
        ],
        "reportFeatures": [
            "工单处理数量",
            "工单类型分布",
            "一次性修复率（按故障类型）",
            "反复报修厂区 Top",
            "平均响应/处理时长",
            "设备服役年限分布",
            "维修日历热力图",
            "故障根因 Top",
            "现场照片收集数量",
        ],
    }


@router.get("/trend")
async def trend(days: int = 30) -> dict:
    """Daily work-order count trend."""
    rng = _seeded_random(1001 + days)
    today = datetime.now().date()
    points = []
    for offset in range(days - 1, -1, -1):
        date = today - timedelta(days=offset)
        base = 4 + rng.randint(0, 6)
        if date.weekday() in (5, 6):
            base += rng.randint(0, 2)
        points.append({"date": date.isoformat(), "count": base})
    return {"points": points}


@router.get("/type-distribution")
async def type_distribution() -> dict:
    items = [
        {"name": "设备故障", "value": 42, "color": "#53d1ff"},
        {"name": "超标预警", "value": 28, "color": "#ff5b61"},
        {"name": "定期巡检", "value": 35, "color": "#ffb347"},
        {"name": "传感器异常", "value": 15, "color": "#a78bfa"},
        {"name": "其他", "value": 8, "color": "#7dd3fc"},
    ]
    return {"items": items, "total": sum(item["value"] for item in items)}


@router.get("/first-fix-rate")
async def first_fix_rate() -> dict:
    items = [
        {"category": "RTO 炉体", "rate": 0.86, "total": 22, "color": "#53d1ff"},
        {"category": "转轮系统", "rate": 0.72, "total": 18, "color": "#ffb347"},
        {"category": "风机", "rate": 0.81, "total": 15, "color": "#a78bfa"},
        {"category": "传感器", "rate": 0.64, "total": 11, "color": "#ff5b61"},
        {"category": "管路阀门", "rate": 0.78, "total": 14, "color": "#7dd3fc"},
    ]
    overall = round(sum(x["rate"] * x["total"] for x in items) / sum(x["total"] for x in items), 3)
    return {"items": items, "overall": overall}


@router.get("/repeated-sites")
async def repeated_sites(limit: int = 8) -> dict:
    items = [
        {"site": "A2 涂装车间", "count": 12, "lastAt": "2026-04-18 14:20"},
        {"site": "B1 烘房入口", "count": 9, "lastAt": "2026-04-19 09:45"},
        {"site": "C3 排放总管", "count": 7, "lastAt": "2026-04-20 16:10"},
        {"site": "A3 喷漆房 #2", "count": 6, "lastAt": "2026-04-17 11:05"},
        {"site": "RTO 出口", "count": 5, "lastAt": "2026-04-19 22:30"},
        {"site": "B2 烘房出口", "count": 4, "lastAt": "2026-04-16 08:15"},
        {"site": "活性炭箱 #1", "count": 4, "lastAt": "2026-04-15 13:50"},
        {"site": "脱附区", "count": 3, "lastAt": "2026-04-14 17:40"},
    ]
    return {"items": items[:limit]}


@router.get("/duration-stats")
async def duration_stats() -> dict:
    items = [
        {"month": "2025-11", "avgHours": 5.6},
        {"month": "2025-12", "avgHours": 5.2},
        {"month": "2026-01", "avgHours": 4.9},
        {"month": "2026-02", "avgHours": 5.1},
        {"month": "2026-03", "avgHours": 4.6},
        {"month": "2026-04", "avgHours": 4.2},
    ]
    return {"items": items, "currentAvg": items[-1]["avgHours"]}


@router.get("/device-age")
async def device_age() -> dict:
    buckets = [
        {"range": "0-1年", "count": 18},
        {"range": "1-3年", "count": 42},
        {"range": "3-5年", "count": 31},
        {"range": "5-8年", "count": 22},
        {"range": "8年以上", "count": 9},
    ]
    return {"buckets": buckets}


@router.get("/repair-heatmap")
async def repair_heatmap(weeks: int = 14) -> dict:
    rng = _seeded_random(42)
    today = datetime.now().date()
    start = today - timedelta(days=weeks * 7 - 1)
    cells = []
    for offset in range((today - start).days + 1):
        d = start + timedelta(days=offset)
        intensity = rng.randint(0, 4)
        if d.weekday() in (5, 6):
            intensity = max(0, intensity - 1)
        cells.append({"date": d.isoformat(), "value": intensity})
    return {"cells": cells, "start": start.isoformat(), "end": today.isoformat()}


@router.get("/root-causes")
async def root_causes() -> dict:
    items = [
        {"cause": "燃烧温度不稳", "count": 23, "color": "#ff5b61"},
        {"cause": "传感器漂移", "count": 19, "color": "#ffb347"},
        {"cause": "风机异响", "count": 14, "color": "#53d1ff"},
        {"cause": "管路泄漏", "count": 11, "color": "#a78bfa"},
        {"cause": "转轮堵塞", "count": 9, "color": "#7dd3fc"},
        {"cause": "其他", "count": 14, "color": "#94a3b8"},
    ]
    return {"items": items, "total": sum(item["count"] for item in items)}


@router.get("/attachments-trend")
async def attachments_trend(days: int = 30) -> dict:
    rng = _seeded_random(7777)
    today = datetime.now().date()
    points = []
    for offset in range(days - 1, -1, -1):
        date = today - timedelta(days=offset)
        points.append({"date": date.isoformat(), "count": 20 + rng.randint(0, 40)})
    return {"points": points, "total": sum(p["count"] for p in points)}
