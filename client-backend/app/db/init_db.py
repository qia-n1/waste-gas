from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import engine
from app.models.entities import (
    AiConversation,
    Alert,
    AlertRecord,
    AreaSourcePoint,
    AreaZone,
    Base,
    DeviceInfo,
    DisposalRecord,
    InspectionRecord,
    NotificationMessage,
    SensorReading,
    SystemSetting,
    UserProfile,
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_if_empty(session: AsyncSession) -> None:
    profile_exists = await session.scalar(select(UserProfile.id).limit(1))
    if profile_exists:
        return

    now = datetime.now().replace(second=0, microsecond=0)

    session.add(
        UserProfile(
            username='admin',
            password_hash=hash_password('password'),
            role='管理员',
            name='张三',
            email='admin@example.com',
            phone='13800138000',
            department='技术部',
            join_date=date(2026, 1, 1),
        )
    )

    session.add(
        SystemSetting(
            alert_notify=True,
            system_notify=True,
            offline_notify=True,
            dark_mode=False,
            language='简体中文',
        )
    )

    session.add(
        DeviceInfo(
            device_id='DEV-001',
            device_name='废气监测设备 1',
            status='在线',
            last_online=now,
            ip_address='192.168.1.100',
            firmware_version='v1.0.0',
            location='废气处理车间 A',
        )
    )

    readings: list[SensorReading] = []
    for i in range(24):
        ts = now - timedelta(hours=23 - i)
        readings.append(
            SensorReading(
                device_id='DEV-001',
                recorded_at=ts,
                vocs=12.5 + (i % 5) * 4.3,
                temperature=24.0 + (i % 4) * 1.5,
                humidity=42 + (i % 6) * 3,
                pressure=100.5 + (i % 5) * 0.6,
            )
        )
    session.add_all(readings)

    alert_1 = Alert(
        title='VOCs 浓度超标',
        description='VOCs 浓度达到 65.2 mg/m3，超过阈值 50 mg/m3，持续时间超过 5 分钟',
        level='high',
        status='unresolved',
        created_at=now - timedelta(hours=2),
        resolved_at=None,
        device_id='DEV-001',
        location='废气处理车间 A',
        alert_type='浓度超标',
        metric_label='VOCs 浓度',
        current_value=65.2,
        unit='mg/m3',
        threshold_value=50,
    )
    alert_1.records = [
        AlertRecord(time=now - timedelta(hours=2), content='系统自动检测到告警', operator='系统')
    ]

    alert_2 = Alert(
        title='温度异常',
        description='温度达到 42.5 C，超过阈值 40 C',
        level='medium',
        status='resolved',
        created_at=now - timedelta(hours=4),
        resolved_at=now - timedelta(hours=3, minutes=30),
        device_id='DEV-001',
        location='废气处理车间 A',
        alert_type='温度异常',
        metric_label='温度',
        current_value=42.5,
        unit='C',
        threshold_value=40,
    )
    alert_2.records = [
        AlertRecord(time=now - timedelta(hours=4), content='系统自动检测到告警', operator='系统'),
        AlertRecord(time=now - timedelta(hours=3, minutes=30), content='现场巡检并完成处置', operator='管理员'),
    ]

    session.add_all([alert_1, alert_2])

    session.add_all([
        AreaZone(name='A区处理车间', manager_username='admin', device_count=8, online_rate=98.5, alert_count=2, avg_vocs=23.6),
        AreaZone(name='B区吸附站', manager_username='admin', device_count=5, online_rate=100.0, alert_count=1, avg_vocs=18.4),
    ])

    session.add_all([
        AreaSourcePoint(area_name='A区处理车间', source_name='排口 A-01', x=18, y=32, concentration=18.5, status='正常', level='low', trend='stable', device_id='DEV-001'),
        AreaSourcePoint(area_name='A区处理车间', source_name='排口 A-02', x=42, y=26, concentration=36.2, status='预警', level='medium', trend='up', device_id='DEV-002'),
        AreaSourcePoint(area_name='A区处理车间', source_name='排口 A-03', x=64, y=58, concentration=65.2, status='告警', level='high', trend='up', device_id='DEV-003'),
        AreaSourcePoint(area_name='B区吸附站', source_name='排口 B-01', x=30, y=72, concentration=12.1, status='正常', level='low', trend='down', device_id='DEV-004'),
    ])

    session.add_all([
        DisposalRecord(alert_id=1, username='admin', result='已完成风机检查', notes='已更换滤芯并恢复运行', photo_url='/static/mock/disposal-1.jpg', status='已提交', action_type='处置闭环', created_at=now - timedelta(hours=1, minutes=20)),
        DisposalRecord(alert_id=2, username='admin', result='确认温度恢复', notes='现场复核完成', photo_url='/static/mock/disposal-2.jpg', status='已归档', action_type='处置闭环', created_at=now - timedelta(hours=3)),
    ])

    session.add_all([
        NotificationMessage(username='admin', title='高等级告警提醒', content='A区处理车间排口 A-03 VOCs 浓度超标，请尽快处理。', category='告警', level='high', is_read=False, created_at=now - timedelta(minutes=45), alert_id=1),
        NotificationMessage(username='admin', title='设备巡检通知', content='今日 18:00 前请完成 A 区巡检。', category='系统', level='low', is_read=True, created_at=now - timedelta(hours=5), alert_id=None),
    ])

    session.add_all([
        AiConversation(username='admin', session_id='default', role='user', content='最近 VOCs 超标的原因是什么？', created_at=now - timedelta(minutes=35)),
        AiConversation(username='admin', session_id='default', role='assistant', content='结合历史数据，当前超标更可能来自风机效率下降与吸附饱和，需要先排查风机工况和活性炭状态。', created_at=now - timedelta(minutes=34)),
    ])

    session.add_all([
        InspectionRecord(username='admin', area_name='A区处理车间', summary='完成风机、管道与阀门巡检，发现排口 A-03 浓度偏高。', created_at=now - timedelta(days=1, hours=2)),
        InspectionRecord(username='admin', area_name='B区吸附站', summary='吸附站运行平稳，未发现明显异常。', created_at=now - timedelta(days=2, hours=1)),
    ])

    await session.commit()
