from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.entities import Alert, DeviceInfo, SensorReading

router = APIRouter(prefix='/dashboard', tags=['dashboard'])

@router.get("/overview")
async def get_dashboard_overview(window: str = "24h", db: AsyncSession = Depends(get_db)):
    latest = await db.scalar(select(SensorReading).order_by(desc(SensorReading.recorded_at)).limit(1))
    recent_alerts = (
        await db.scalars(select(Alert).order_by(desc(Alert.created_at)).limit(3))
    ).all()
    device = await db.scalar(select(DeviceInfo).where(DeviceInfo.device_id == 'DEV-001').limit(1))

    trend_rows = (
        await db.scalars(
            select(SensorReading)
            .order_by(desc(SensorReading.recorded_at))
            .limit(24)
        )
    ).all()

    return {
        "code": 200,
        "data": {
            "realTimeData": {
                "vocs": round(latest.vocs, 2) if latest else 0,
                "temperature": round(latest.temperature, 2) if latest else 0,
                "humidity": round(latest.humidity, 2) if latest else 0,
                "pressure": round(latest.pressure, 2) if latest else 0,
                "timestamp": latest.recorded_at.strftime('%Y-%m-%d %H:%M') if latest else '-',
            },
            "recentAlerts": [
                {
                    "id": item.id,
                    "title": item.title,
                    "time": item.created_at.strftime('%Y-%m-%d %H:%M'),
                    "level": item.level,
                    "status": item.status,
                }
                for item in recent_alerts
            ],
            "systemStatus": {
                "deviceOnline": device.status if device else '离线',
                "dataCollection": '正常' if latest else '异常',
                "network": '正常',
                "version": 'v1.0.0',
            },
            "actual_series": [
                {
                    "time": row.recorded_at.strftime('%Y-%m-%d %H:%M'),
                    "vocs": round(row.vocs, 2),
                }
                for row in reversed(trend_rows)
            ],
        }
    }