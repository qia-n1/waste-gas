from datetime import date, datetime, timedelta

from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import engine
from app.models.entities import Alert, AlertRecord, Base, DeviceInfo, SensorReading, SystemSetting, UserProfile


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_ensure_user_profile_password_hash_column)


def _ensure_user_profile_password_hash_column(connection) -> None:
    inspector = inspect(connection)
    if 'wg_user_profiles' not in inspector.get_table_names():
        return

    column_names = {column['name'] for column in inspector.get_columns('wg_user_profiles')}
    if 'password_hash' in column_names:
        return

    connection.execute(text('ALTER TABLE wg_user_profiles ADD COLUMN password_hash VARCHAR(255)'))
    connection.execute(
        text('UPDATE wg_user_profiles SET password_hash = :password_hash WHERE password_hash IS NULL'),
        {'password_hash': hash_password('password')},
    )


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
    await session.commit()
