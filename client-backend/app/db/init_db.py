from datetime import date, datetime, timedelta

from sqlalchemy import inspect, select, text
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


def _ensure_wg_alerts_handled_at(sync_conn) -> None:
    try:
        cols = [c['name'] for c in inspect(sync_conn).get_columns('wg_alerts')]
    except Exception:
        return
    if 'handled_at' not in cols:
        dialect = sync_conn.dialect.name
        # PostgreSQL 不支持 DATETIME；统一用各库可识别的时间类型。
        col_type = 'TIMESTAMP' if dialect == 'postgresql' else 'DATETIME'
        sync_conn.execute(text(f'ALTER TABLE wg_alerts ADD COLUMN handled_at {col_type}'))


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_wg_alerts_handled_at)


async def seed_if_empty(session: AsyncSession) -> None:
    now = datetime.now().replace(second=0, microsecond=0)

    # Check and seed UserProfile
    profile_exists = await session.scalar(select(UserProfile.id).limit(1))
    if not profile_exists:
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

    # Check and seed SystemSetting
    setting_exists = await session.scalar(select(SystemSetting.id).limit(1))
    if not setting_exists:
        session.add(
            SystemSetting(
                alert_notify=True,
                system_notify=True,
                offline_notify=True,
                dark_mode=False,
                language='简体中文',
            )
        )

    # Check and seed DeviceInfo
    device_exists = await session.scalar(select(DeviceInfo.id).limit(1))
    if not device_exists:
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

    # Check and seed SensorReading
    reading_exists = await session.scalar(select(SensorReading.id).limit(1))
    if not reading_exists:
        readings: list[SensorReading] = []
        for i in range(72):
            ts = now - timedelta(hours=71 - i)
            readings.append(
                SensorReading(
                    device_id='DEV-001',
                    recorded_at=ts,
                    vocs=12.5 + (i % 7) * 3.8 + (i % 3) * 1.1,
                    temperature=22.0 + (i % 5) * 1.8,
                    humidity=38 + (i % 8) * 3.5,
                    pressure=99.8 + (i % 6) * 0.55,
                )
            )
        session.add_all(readings)

    # Check and seed Alert
    alert_exists = await session.scalar(select(Alert.id).limit(1))
    if not alert_exists:
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
            handled_at=now - timedelta(days=3, hours=2),
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

    # Check and seed AreaZone - only seed if '喷涂生产厂房' doesn't exist
    coating_zone_exists = await session.scalar(select(AreaZone.id).where(AreaZone.name == '喷涂生产厂房').limit(1))
    if not coating_zone_exists:
        # 与 admin 端 FactoryScene 建模一致：左起排口烟囱—喷涂—转轮—RTO—公辅，前侧为监测附属（含 1 号排口）
        session.add_all([
            AreaZone(name='喷涂生产厂房', manager_username='admin', device_count=8, online_rate=98.5, alert_count=1, avg_vocs=22.4),
            AreaZone(name='排口烟囱区', manager_username='admin', device_count=2, online_rate=100.0, alert_count=0, avg_vocs=15.0),
            AreaZone(name='转轮吸附厂房', manager_username='admin', device_count=5, online_rate=100.0, alert_count=0, avg_vocs=18.2),
            AreaZone(name='RTO 主处理厂房', manager_username='admin', device_count=6, online_rate=99.0, alert_count=2, avg_vocs=44.8),
            AreaZone(name='公辅燃烧区', manager_username='admin', device_count=4, online_rate=100.0, alert_count=0, avg_vocs=12.6),
            AreaZone(name='监测附属区', manager_username='admin', device_count=3, online_rate=100.0, alert_count=0, avg_vocs=20.0),
        ])

    # Check and seed AreaSourcePoint
    point_exists = await session.scalar(select(AreaSourcePoint.id).limit(1))
    if not point_exists:
        session.add_all([
            AreaSourcePoint(
                area_name='喷涂生产厂房',
                source_name='监测点位',
                x=22,
                y=56,
                concentration=18.5,
                status='正常',
                level='low',
                trend='stable',
                device_id='DEV-001',
            ),
            AreaSourcePoint(
                area_name='排口烟囱区',
                source_name='烟囱监测点',
                x=8,
                y=36,
                concentration=24.0,
                status='正常',
                level='low',
                trend='stable',
                device_id='DEV-002',
            ),
            AreaSourcePoint(
                area_name='转轮吸附厂房',
                source_name='转轮出口',
                x=40,
                y=56,
                concentration=36.2,
                status='预警',
                level='medium',
                trend='up',
                device_id='DEV-003',
            ),
            AreaSourcePoint(
                area_name='RTO 主处理厂房',
                source_name='关键设备',
                x=62,
                y=52,
                concentration=65.2,
                status='告警',
                level='high',
                trend='up',
                device_id='DEV-004',
            ),
            AreaSourcePoint(
                area_name='公辅燃烧区',
                source_name='公辅监测点',
                x=82,
                y=54,
                concentration=12.1,
                status='正常',
                level='low',
                trend='down',
                device_id='DEV-005',
            ),
            AreaSourcePoint(
                area_name='监测附属区',
                source_name='1号排口',
                x=82,
                y=76,
                concentration=28.0,
                status='预警',
                level='medium',
                trend='up',
                device_id='DEV-006',
            ),
        ])

    # Check and seed DisposalRecord
    disposal_exists = await session.scalar(select(DisposalRecord.id).limit(1))
    if not disposal_exists:
        session.add_all([
            DisposalRecord(alert_id=1, username='admin', result='已完成风机检查', notes='已更换滤芯并恢复运行', photo_url='/static/mock/disposal-1.jpg', status='已提交', action_type='处置闭环', created_at=now - timedelta(hours=1, minutes=20)),
            DisposalRecord(alert_id=2, username='admin', result='确认温度恢复', notes='现场复核完成', photo_url='/static/mock/disposal-2.jpg', status='已归档', action_type='处置闭环', created_at=now - timedelta(hours=3)),
        ])

    # Check and seed NotificationMessage
    notification_exists = await session.scalar(select(NotificationMessage.id).limit(1))
    if not notification_exists:
        session.add_all([
            NotificationMessage(username='admin', title='高等级告警提醒', content='RTO 主处理厂房 1号排口 VOCs 浓度超标，请尽快处理。', category='告警', level='high', is_read=False, created_at=now - timedelta(minutes=45), alert_id=1),
            NotificationMessage(username='admin', title='设备巡检通知', content='今日 18:00 前请完成 A 区巡检。', category='系统', level='low', is_read=True, created_at=now - timedelta(hours=5), alert_id=None),
        ])

    # Check and seed AiConversation
    conversation_exists = await session.scalar(select(AiConversation.id).limit(1))
    if not conversation_exists:
        session.add_all([
            AiConversation(username='admin', session_id='default', role='user', content='最近 VOCs 超标的原因是什么？', created_at=now - timedelta(minutes=35)),
            AiConversation(username='admin', session_id='default', role='assistant', content='结合历史数据，当前超标更可能来自风机效率下降与吸附饱和，需要先排查风机工况和活性炭状态。', created_at=now - timedelta(minutes=34)),
        ])

    # Check and seed InspectionRecord
    inspection_exists = await session.scalar(select(InspectionRecord.id).limit(1))
    if not inspection_exists:
        session.add_all([
            InspectionRecord(username='admin', area_name='RTO 主处理厂房', summary='完成风机、管道与阀门巡检，发现 1 号排口浓度偏高。', created_at=now - timedelta(days=1, hours=2)),
            InspectionRecord(username='admin', area_name='转轮吸附厂房', summary='转轮与吸附段运行平稳，未发现明显异常。', created_at=now - timedelta(days=2, hours=1)),
        ])

    await session.commit()
