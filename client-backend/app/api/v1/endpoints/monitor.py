from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.entities import AreaSourcePoint, DeviceInfo, SensorReading

router = APIRouter(prefix='/monitor', tags=['monitor'])


def _status(value: float, warning_low: float, warning_high: float, err_low: float, err_high: float) -> str:
    if value < err_low or value > err_high:
        return 'error'
    if value < warning_low or value > warning_high:
        return 'warning'
    return 'normal'


@router.get('/realtime')
async def get_realtime_data(db: AsyncSession = Depends(get_db)) -> dict:
    latest = await db.scalar(select(SensorReading).order_by(desc(SensorReading.recorded_at)).limit(1))
    device = await db.scalar(select(DeviceInfo).where(DeviceInfo.device_id == 'DEV-001').limit(1))
    recent_rows = (await db.scalars(select(SensorReading).order_by(desc(SensorReading.recorded_at)).limit(24))).all()

    trend = [
        {
            'time': row.recorded_at.strftime('%Y-%m-%d %H:%M'),
            'vocs': round(row.vocs, 2),
            'temperature': round(row.temperature, 2),
            'humidity': round(row.humidity, 2),
            'pressure': round(row.pressure, 2),
        }
        for row in reversed(recent_rows)
    ]

    if latest is None:
        return {'code': 200, 'data': {'real_time_data': None, 'device_info': None, 'trend': []}}

    return {
        'code': 200,
        'data': {
            'real_time_data': {
                'vocs': round(latest.vocs, 2),
                'temperature': round(latest.temperature, 2),
                'humidity': round(latest.humidity, 2),
                'pressure': round(latest.pressure, 2),
                'timestamp': latest.recorded_at.strftime('%Y-%m-%d %H:%M'),
                'status': {
                    'vocs': _status(latest.vocs, 20, 50, 0, 80),
                    'temperature': _status(latest.temperature, 5, 35, 0, 40),
                    'humidity': _status(latest.humidity, 30, 80, 20, 90),
                    'pressure': _status(latest.pressure, 95, 105, 90, 110),
                },
            },
            'device_info': {
                'deviceId': device.device_id if device else 'DEV-001',
                'deviceName': device.device_name if device else '未知设备',
                'status': device.status if device else '离线',
                'lastOnline': (device.last_online.strftime('%Y-%m-%d %H:%M') if device else '-'),
                'ipAddress': device.ip_address if device else '-',
                'firmwareVersion': device.firmware_version if device else '-',
                'location': device.location if device else '-',
            },
            'trend': trend,
        },
    }


@router.get('/map')
async def get_map_points(db: AsyncSession = Depends(get_db)) -> dict:
    points = (await db.scalars(select(AreaSourcePoint).order_by(AreaSourcePoint.id.asc()))).all()
    nearest_alert = next((point for point in points if point.level == 'high'), points[0] if points else None)
    return {
        'code': 200,
        'data': {
            'points': [
                {
                    'id': point.id,
                    'name': point.source_name,
                    'x': point.x,
                    'y': point.y,
                    'concentration': round(point.concentration, 2),
                    'status': point.status,
                    'level': point.level,
                    'trend': point.trend,
                    'deviceId': point.device_id,
                    'areaName': point.area_name,
                }
                for point in points
            ],
            'nearestAlertId': nearest_alert.id if nearest_alert else None,
        },
    }


@router.post('/control/start')
async def start_monitoring() -> dict:
    return {'code': 200, 'message': '监控已开始'}


@router.post('/control/stop')
async def stop_monitoring() -> dict:
    return {'code': 200, 'message': '监控已停止'}
