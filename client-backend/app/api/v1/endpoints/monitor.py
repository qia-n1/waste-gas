from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_username
from app.db.session import get_db
from app.models.entities import AreaSourcePoint, AreaZone, DeviceInfo, SensorReading

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
    recent_rows = (await db.scalars(select(SensorReading).order_by(desc(SensorReading.recorded_at)).limit(60))).all()

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
async def get_map_points(
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    zones = (await db.scalars(select(AreaZone).order_by(AreaZone.id.asc()))).all()
    own_area_names = {item.name for item in zones if item.manager_username == username}
    area_names = list(own_area_names)
    points: list[AreaSourcePoint] = []
    if area_names:
        points = (
            await db.scalars(
                select(AreaSourcePoint)
                .where(AreaSourcePoint.area_name.in_(area_names))
                .order_by(AreaSourcePoint.id.asc())
            )
        ).all()

    # 俯视布局：块区分离、少重叠，便于客户端点击厂房与标点（百分比相对地图画布）
    # 俯视布局与 admin FactoryScene 厂区顺序一致（百分比相对地图画布）
    region_layout: dict[str, dict[str, int]] = {
        '喷涂生产厂房': {'x': 14, 'y': 38, 'w': 20, 'h': 28},
        '排口烟囱区': {'x': 3, 'y': 22, 'w': 12, 'h': 26},
        '转轮吸附厂房': {'x': 33, 'y': 38, 'w': 18, 'h': 28},
        'RTO 主处理厂房': {'x': 50, 'y': 34, 'w': 24, 'h': 34},
        '公辅燃烧区': {'x': 75, 'y': 38, 'w': 16, 'h': 28},
        '监测附属区': {'x': 70, 'y': 66, 'w': 24, 'h': 18},
        # 旧种子数据兼容
        'A区处理车间': {'x': 9, 'y': 30, 'w': 50, 'h': 52},
        'B区吸附站': {'x': 62, 'y': 30, 'w': 28, 'h': 56},
    }
    base_layouts = [
        {'x': 8, 'y': 10, 'w': 38, 'h': 34},
        {'x': 54, 'y': 10, 'w': 38, 'h': 34},
        {'x': 8, 'y': 52, 'w': 38, 'h': 34},
        {'x': 54, 'y': 52, 'w': 38, 'h': 34},
        {'x': 30, 'y': 31, 'w': 40, 'h': 38},
    ]

    areas = []
    for idx, zone in enumerate(zones):
        layout = region_layout.get(zone.name) or base_layouts[idx % len(base_layouts)]
        level = 'low'
        if zone.alert_count >= 2:
            level = 'high'
        elif zone.alert_count >= 1 or zone.avg_vocs >= 25:
            level = 'medium'

        areas.append(
            {
                'id': zone.id,
                'name': zone.name,
                'x': layout['x'],
                'y': layout['y'],
                'w': layout['w'],
                'h': layout['h'],
                'deviceCount': zone.device_count,
                'onlineRate': round(zone.online_rate, 1),
                'alertCount': zone.alert_count,
                'avgVocs': round(zone.avg_vocs, 2),
                'level': level,
                'canView': zone.manager_username == username,
            }
        )

    response_points = [
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
    ]

    if not response_points:
        for area in areas:
            if not area['canView']:
                continue
            response_points.append(
                {
                    'id': f"area-{area['id']}",
                    'name': area['name'],
                    'x': round(area['x'] + area['w'] / 2, 2),
                    'y': round(area['y'] + area['h'] / 2, 2),
                    'concentration': area['avgVocs'],
                    'status': '告警' if area['level'] == 'high' else ('预警' if area['level'] == 'medium' else '正常'),
                    'level': area['level'],
                    'trend': 'stable',
                    'deviceId': '-',
                    'areaName': area['name'],
                }
            )

    nearest_alert = next((point for point in response_points if point['level'] == 'high'), response_points[0] if response_points else None)
    return {
        'code': 200,
        'data': {
            'areas': areas,
            'points': response_points,
            'nearestAlertId': nearest_alert['id'] if nearest_alert else None,
            'ownedAreaNames': area_names,
        },
    }


@router.post('/control/start')
async def start_monitoring() -> dict:
    return {'code': 200, 'message': '监控已开始'}


@router.post('/control/stop')
async def stop_monitoring() -> dict:
    return {'code': 200, 'message': '监控已停止'}
