from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_username
from app.db.session import get_db
from app.models.entities import Alert, AlertRecord, DisposalRecord

router = APIRouter(prefix='/alerts', tags=['alerts'])


class AlertHandleRequest(BaseModel):
    result: str = Field(min_length=1, max_length=128)
    notes: str = ''
    photoUrl: str = ''


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

    ai_diagnosis = {
        'reason': '结合近 24 小时趋势，疑似风机效率下降与吸附饱和共同导致。',
        'suggestion': '优先检查风机负压、活性炭状态，并复核相邻排口是否同步波动。',
        'similarCases': ['2026-03-18 A 区风机停转', '2026-02-26 活性炭饱和导致浓度升高'],
        'sop': ['关闭异常支路', '检查风机电流与转速', '采样复测并记录处置结果'],
    }

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
            'predictionCurve': [
                {'label': '10:00', 'value': round(alert.current_value * 0.78, 2)},
                {'label': '10:10', 'value': round(alert.current_value * 0.86, 2)},
                {'label': '10:20', 'value': round(alert.current_value * 0.93, 2)},
                {'label': '当前', 'value': round(alert.current_value, 2)},
            ],
            'aiDiagnosis': ai_diagnosis,
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
    alert.status = 'resolved'
    db.add(AlertRecord(alert_id=alert.id, time=now, content='告警已忽略', operator='当前用户'))
    await db.commit()
    return {'code': 200, 'message': '告警已忽略'}


@router.post('/{alert_id}/misreport')
async def misreport_alert(alert_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    alert = await db.scalar(select(Alert).where(Alert.id == alert_id).limit(1))
    if alert is None:
        raise HTTPException(status_code=404, detail='告警不存在')

    now = datetime.now().replace(microsecond=0)
    alert.status = 'resolved'
    db.add(AlertRecord(alert_id=alert.id, time=now, content='已标记为误报', operator='当前用户'))
    await db.commit()
    return {'code': 200, 'message': '已标记为误报'}


@router.post('/{alert_id}/handle')
async def handle_alert(
    alert_id: int,
    payload: AlertHandleRequest,
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    alert = await db.scalar(select(Alert).where(Alert.id == alert_id).limit(1))
    if alert is None:
        raise HTTPException(status_code=404, detail='告警不存在')

    now = datetime.now().replace(microsecond=0)
    alert.status = 'resolved'
    alert.resolved_at = now
    db.add(
        DisposalRecord(
            alert_id=alert.id,
            username=username,
            result=payload.result,
            notes=payload.notes,
            photo_url=payload.photoUrl,
            status='已提交',
            action_type='处置闭环',
            created_at=now,
        )
    )
    db.add(
        AlertRecord(
            alert_id=alert.id,
            time=now,
            content=f'提交处置结果：{payload.result}',
            operator=username,
        )
    )
    await db.commit()
    return {'code': 200, 'message': '处置记录已提交'}


@router.get('/exports/disposals')
async def export_disposals(
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    rows = (await db.scalars(select(DisposalRecord).where(DisposalRecord.username == username).order_by(DisposalRecord.created_at.desc()))).all()
    lines = ['告警ID,结果,状态,时间']
    for row in rows:
        lines.append(f'{row.alert_id},{row.result},{row.status},{row.created_at.strftime("%Y-%m-%d %H:%M")}')
    return {'code': 200, 'data': {'filename': 'disposals.csv', 'content': '\n'.join(lines)}}
