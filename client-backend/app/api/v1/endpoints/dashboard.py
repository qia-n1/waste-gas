from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.entities import Alert, AreaSourcePoint, AreaZone, DeviceInfo, SensorReading

router = APIRouter(prefix='/dashboard', tags=['dashboard'])


@router.get('/overview')
async def get_dashboard_overview(window: str = '24h', db: AsyncSession = Depends(get_db)) -> dict:
    latest = await db.scalar(select(SensorReading).order_by(desc(SensorReading.recorded_at)).limit(1))
    recent_alerts = (await db.scalars(select(Alert).order_by(desc(Alert.created_at)).limit(3))).all()
    device = await db.scalar(select(DeviceInfo).where(DeviceInfo.device_id == 'DEV-001').limit(1))
    trend_rows = (await db.scalars(select(SensorReading).order_by(desc(SensorReading.recorded_at)).limit(24))).all()
    map_points = (await db.scalars(select(AreaSourcePoint).order_by(AreaSourcePoint.id.asc()))).all()

    return {
        'code': 200,
        'data': {
            'realTimeData': {
                'vocs': round(latest.vocs, 2) if latest else 0,
                'temperature': round(latest.temperature, 2) if latest else 0,
                'humidity': round(latest.humidity, 2) if latest else 0,
                'pressure': round(latest.pressure, 2) if latest else 0,
                'timestamp': latest.recorded_at.strftime('%Y-%m-%d %H:%M') if latest else '-',
            },
            'recentAlerts': [
                {
                    'id': item.id,
                    'title': item.title,
                    'time': item.created_at.strftime('%Y-%m-%d %H:%M'),
                    'level': item.level,
                    'status': item.status,
                }
                for item in recent_alerts
            ],
            'systemStatus': {
                'deviceOnline': device.status if device else '离线',
                'dataCollection': '正常' if latest else '异常',
                'network': '正常',
                'version': 'v1.0.0',
            },
            'actual_series': [
                {'time': row.recorded_at.strftime('%Y-%m-%d %H:%M'), 'vocs': round(row.vocs, 2)}
                for row in reversed(trend_rows)
            ],
            'mapPoints': [
                {
                    'id': point.id,
                    'name': point.source_name,
                    'x': point.x,
                    'y': point.y,
                    'value': round(point.concentration, 2),
                    'level': point.level,
                    'status': point.status,
                    'trend': point.trend,
                }
                for point in map_points
            ],
        }
    }


@router.get('/my-area')
async def get_my_area(username: str = 'admin', db: AsyncSession = Depends(get_db)) -> dict:
    zones = (await db.scalars(select(AreaZone).where(AreaZone.manager_username == username))).all()
    sources = (await db.scalars(select(AreaSourcePoint).order_by(AreaSourcePoint.id.asc()))).all()
    devices = (await db.scalars(select(DeviceInfo).order_by(DeviceInfo.id.asc()))).all()
    trend_rows = (await db.scalars(select(SensorReading).order_by(desc(SensorReading.recorded_at)).limit(8))).all()

    return {
        'code': 200,
        'data': {
            'overview': {
                'deviceCount': sum(item.device_count for item in zones),
                'onlineRate': round(sum(item.online_rate for item in zones) / len(zones), 1) if zones else 0,
                'alertCount': sum(item.alert_count for item in zones),
            },
            'areas': [
                {
                    'name': item.name,
                    'deviceCount': item.device_count,
                    'onlineRate': item.online_rate,
                    'alertCount': item.alert_count,
                    'avgVocs': item.avg_vocs,
                }
                for item in zones
            ],
            'sources': [
                {
                    'id': item.id,
                    'name': item.source_name,
                    'areaName': item.area_name,
                    'concentration': item.concentration,
                    'status': item.status,
                    'level': item.level,
                }
                for item in sources
            ],
            'deviceStatus': [
                {
                    'deviceId': item.device_id,
                    'deviceName': item.device_name,
                    'status': item.status,
                    'location': item.location,
                }
                for item in devices
            ],
            'trend': [
                {
                    'time': row.recorded_at.strftime('%H:%M'),
                    'vocs': round(row.vocs, 2),
                }
                for row in reversed(trend_rows)
            ],
        },
    }
