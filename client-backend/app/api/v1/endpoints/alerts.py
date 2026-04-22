from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_username
from app.db.session import get_db
import json
from app.models.entities import Alert, AlertRecord, DisposalRecord, RagPlan

router = APIRouter(prefix='/alerts', tags=['alerts'])

TRACKING_HOURS_BEFORE_RESOLVE = 48


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

    # 从 rag_plans 表获取 AI 处理方案
    rag_plan = await db.scalar(
        select(RagPlan)
        .where(RagPlan.alert_id == alert.id)
        .order_by(RagPlan.created_at.desc())
        .limit(1)
    )

    if rag_plan:
        try:
            steps = json.loads(rag_plan.steps)
        except json.JSONDecodeError:
            steps = []
        ai_plan = {
            'title': rag_plan.title,
            'summary': rag_plan.summary,
            'steps': steps,
            'qaHint': rag_plan.qa_hint,
        }
    else:
        # 默认可用方案（管理端未下发时使用）
        ai_plan = {
            'title': '现场处置方案（默认）',
            'summary': '按“先控制风险—再定位原因—复测确认—留痕闭环”的顺序执行，必要时升级班长/仪控/工艺联动。',
            'steps': [
                '确认告警点位、阈值与近 30 分钟趋势；对比相邻排口是否同步抬升',
                '现场检查关键设备（风机/阀门/压差/温度/电流），记录异常参数与照片',
                '若为压差升高：优先排查取压管堵塞/积水，再检查过滤器与转轮通道结焦/堵塞',
                '执行临时控制措施：降负荷、切换备机/旁路、增加洗涤/喷淋强度（如适用）',
                '处置后 10/30/60 分钟复测，趋势恢复稳定后提交处置并进入 48h 跟踪',
            ],
            'qaHint': '在本方案下可继续追问：例如“压差升高怎么判断是取压管问题？”“需要哪些现场证据？”',
        }

    now = datetime.now().replace(microsecond=0)
    resolve_earliest: datetime | None = None
    can_resolve = False
    if alert.status == 'tracking' and alert.handled_at is not None:
        resolve_earliest = alert.handled_at + timedelta(hours=TRACKING_HOURS_BEFORE_RESOLVE)
        can_resolve = now >= resolve_earliest

    return {
        'code': 200,
        'data': {
            'id': alert.id,
            'title': alert.title,
            'time': alert.created_at.strftime('%Y-%m-%d %H:%M'),
            'description': alert.description,
            'level': alert.level,
            'status': alert.status,
            'handledAt': alert.handled_at.strftime('%Y-%m-%d %H:%M') if alert.handled_at else None,
            'resolveEarliestAt': resolve_earliest.strftime('%Y-%m-%d %H:%M') if resolve_earliest else None,
            'canResolve': can_resolve,
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
            'aiPlan': ai_plan,
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


@router.post('/{alert_id}/accept')
async def accept_alert(
    alert_id: int,
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    alert = await db.scalar(select(Alert).where(Alert.id == alert_id).limit(1))
    if alert is None:
        raise HTTPException(status_code=404, detail='告警不存在')
    if alert.status != 'unresolved':
        raise HTTPException(status_code=400, detail='仅待接单状态的告警可以接单')

    now = datetime.now().replace(microsecond=0)
    alert.status = 'accepted'
    db.add(AlertRecord(alert_id=alert.id, time=now, content='现场已接单，开始处置', operator=username))
    await db.commit()
    return {'code': 200, 'message': '接单成功'}


@router.post('/{alert_id}/resolve')
async def resolve_alert(
    alert_id: int,
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    alert = await db.scalar(select(Alert).where(Alert.id == alert_id).limit(1))
    if alert is None:
        raise HTTPException(status_code=404, detail='告警不存在')
    if alert.status != 'tracking':
        raise HTTPException(status_code=400, detail='仅「持续跟踪」中的告警可结案，请先提交处置并等待跟踪期满')
    if alert.handled_at is None:
        raise HTTPException(status_code=400, detail='缺少处置起算时间，无法结案')

    now = datetime.now().replace(microsecond=0)
    earliest = alert.handled_at + timedelta(hours=TRACKING_HOURS_BEFORE_RESOLVE)
    if now < earliest:
        raise HTTPException(
            status_code=400,
            detail=f'已处置告警须持续跟踪满 {TRACKING_HOURS_BEFORE_RESOLVE} 小时方可结案，最早 {earliest.strftime("%Y-%m-%d %H:%M")} 后可操作',
        )

    alert.status = 'resolved'
    alert.resolved_at = now
    db.add(
        AlertRecord(
            alert_id=alert.id,
            time=now,
            content='跟踪期满，告警已结案',
            operator=username,
        )
    )
    await db.commit()
    return {'code': 200, 'message': '告警已结案'}


@router.post('/{alert_id}/ignore')
async def ignore_alert(alert_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    alert = await db.scalar(select(Alert).where(Alert.id == alert_id).limit(1))
    if alert is None:
        raise HTTPException(status_code=404, detail='告警不存在')
    if alert.status not in ('unresolved', 'accepted'):
        raise HTTPException(status_code=400, detail='当前状态不可忽略')

    now = datetime.now().replace(microsecond=0)
    alert.status = 'resolved'
    alert.resolved_at = now
    db.add(AlertRecord(alert_id=alert.id, time=now, content='告警已忽略', operator='当前用户'))
    await db.commit()
    return {'code': 200, 'message': '告警已忽略'}


@router.post('/{alert_id}/misreport')
async def misreport_alert(alert_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    alert = await db.scalar(select(Alert).where(Alert.id == alert_id).limit(1))
    if alert is None:
        raise HTTPException(status_code=404, detail='告警不存在')
    if alert.status not in ('unresolved', 'accepted'):
        raise HTTPException(status_code=400, detail='当前状态不可标记误报')

    now = datetime.now().replace(microsecond=0)
    alert.status = 'resolved'
    alert.resolved_at = now
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
    if alert.status not in ('unresolved', 'accepted'):
        raise HTTPException(status_code=400, detail='当前状态不可提交处置')

    now = datetime.now().replace(microsecond=0)
    alert.status = 'tracking'
    alert.handled_at = now
    db.add(
        DisposalRecord(
            alert_id=alert.id,
            username=username,
            result=payload.result[:64],
            notes=payload.notes,
            photo_url=payload.photoUrl,
            status='已提交',
            action_type='处置闭环',
            created_at=now,
        )
    )
    _tail = f'，进入 {TRACKING_HOURS_BEFORE_RESOLVE} 小时持续跟踪后方可结案'
    _rec = f'提交处置结果：{payload.result}{_tail}'[:256]
    db.add(AlertRecord(alert_id=alert.id, time=now, content=_rec, operator=username))
    await db.commit()
    return {'code': 200, 'message': f'处置已记录，需持续跟踪满 {TRACKING_HOURS_BEFORE_RESOLVE} 小时方可结案'}


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
