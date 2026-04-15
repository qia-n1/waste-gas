from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.entities import Alert, AlertRecord

router = APIRouter(prefix='/alerts', tags=['alerts'])

@router.get('')
async def list_alerts(
    status: str | None = None,
    level: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> dict:
    query = select(Alert)
    if status and status != 'all':
        query = query.where(Alert.status == status)
    if level and level != 'all':
        query = query.where(Alert.level == level)

    rows = (await db.scalars(query.order_by(desc(Alert.created_at)).limit(limit))).all()
    return {
        'code': 200,
        'data': [
            {
                'id': item.id,
                'title': item.title,
                'time': item.created_at.strftime('%Y-%m-%d %H:%M'),
                'description': item.description,
                'level': item.level,
                'status': item.status,
            }
            for item in rows
        ],
    }

@router.get('/{alert_id}')
async def get_alert_detail(alert_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    alert = await db.scalar(select(Alert).where(Alert.id == alert_id).limit(1))
    if alert is None:
        raise HTTPException(status_code=404, detail='告警不存在')

    records = (
        await db.scalars(
            select(AlertRecord)
            .where(AlertRecord.alert_id == alert.id)
            .order_by(AlertRecord.time.asc())
        )
    ).all()

    return {
        'code': 200,
        'data': {
            'id': alert.id,
            'title': alert.title,
            'time': alert.created_at.strftime('%Y-%m-%d %H:%M'),
            'description': alert.description,
            'level': alert.level,
            'status': alert.status,
            'deviceId': alert.device_id,
            'location': alert.location,
            'type': alert.alert_type,
            'data': [
                {
                    'label': alert.metric_label,
                    'value': f'{round(alert.current_value, 2)}',
                    'unit': alert.unit,
                    'threshold': f'{round(alert.threshold_value, 2)} {alert.unit}',
                }
            ],
            'processingRecords': [
                {
                    'time': rec.time.strftime('%Y-%m-%d %H:%M'),
                    'content': rec.content,
                    'operator': rec.operator,
                }
                for rec in records
            ],
        },
    }


@router.post('/{alert_id}/resolve')
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    alert = await db.scalar(select(Alert).where(Alert.id == alert_id).limit(1))
    if alert is None:
        raise HTTPException(status_code=404, detail='告警不存在')

    alert.status = 'resolved'
    alert.resolved_at = datetime.now().replace(microsecond=0)
    db.add(
        AlertRecord(
            alert_id=alert.id,
            time=alert.resolved_at,
            content='告警已处理',
            operator='当前用户',
        )
    )
    await db.commit()
    return {'code': 200, 'message': '告警已标记为已处理'}


@router.post('/{alert_id}/ignore')
async def ignore_alert(alert_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    alert = await db.scalar(select(Alert).where(Alert.id == alert_id).limit(1))
    if alert is None:
        raise HTTPException(status_code=404, detail='告警不存在')

    now = datetime.now().replace(microsecond=0)
    db.add(AlertRecord(alert_id=alert.id, time=now, content='告警已忽略', operator='当前用户'))
    await db.commit()
    return {'code': 200, 'message': '告警已忽略'}