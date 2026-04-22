from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserProfile(Base):
    __tablename__ = 'wg_user_profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str] = mapped_column(String(128), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    department: Mapped[str] = mapped_column(String(64), nullable=False)
    join_date: Mapped[date] = mapped_column(Date, nullable=False)


class SystemSetting(Base):
    __tablename__ = 'wg_system_settings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_notify: Mapped[bool] = mapped_column(Boolean, default=True)
    system_notify: Mapped[bool] = mapped_column(Boolean, default=True)
    offline_notify: Mapped[bool] = mapped_column(Boolean, default=True)
    dark_mode: Mapped[bool] = mapped_column(Boolean, default=False)
    language: Mapped[str] = mapped_column(String(32), default='简体中文')


class DeviceInfo(Base):
    __tablename__ = 'wg_device_info'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    device_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    last_online: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    firmware_version: Mapped[str] = mapped_column(String(32), nullable=False)
    location: Mapped[str] = mapped_column(String(128), nullable=False)


class SensorReading(Base):
    __tablename__ = 'wg_sensor_readings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    vocs: Mapped[float] = mapped_column(Float, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    humidity: Mapped[float] = mapped_column(Float, nullable=False)
    pressure: Mapped[float] = mapped_column(Float, nullable=False)


class Alert(Base):
    __tablename__ = 'wg_alerts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    handled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False)
    location: Mapped[str] = mapped_column(String(128), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False)
    metric_label: Mapped[str] = mapped_column(String(64), nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    threshold_value: Mapped[float] = mapped_column(Float, nullable=False)

    records: Mapped[list['AlertRecord']] = relationship('AlertRecord', back_populates='alert', cascade='all, delete-orphan')


class AlertRecord(Base):
    __tablename__ = 'wg_alert_records'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey('wg_alerts.id', ondelete='CASCADE'), nullable=False)
    time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    content: Mapped[str] = mapped_column(String(256), nullable=False)
    operator: Mapped[str] = mapped_column(String(64), nullable=False)

    alert: Mapped[Alert] = relationship('Alert', back_populates='records')


class AreaZone(Base):
    __tablename__ = 'wg_area_zones'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    manager_username: Mapped[str] = mapped_column(String(64), nullable=False)
    device_count: Mapped[int] = mapped_column(Integer, default=0)
    online_rate: Mapped[float] = mapped_column(Float, default=0)
    alert_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_vocs: Mapped[float] = mapped_column(Float, default=0)


class AreaSourcePoint(Base):
    __tablename__ = 'wg_area_source_points'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    area_name: Mapped[str] = mapped_column(String(64), nullable=False)
    source_name: Mapped[str] = mapped_column(String(64), nullable=False)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    concentration: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    trend: Mapped[str] = mapped_column(String(16), nullable=False)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False)


class DisposalRecord(Base):
    __tablename__ = 'wg_disposal_records'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[int] = mapped_column(Integer, nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[str] = mapped_column(String(64), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default='')
    photo_url: Mapped[str] = mapped_column(String(255), default='')
    status: Mapped[str] = mapped_column(String(32), default='已提交')
    action_type: Mapped[str] = mapped_column(String(32), default='处置闭环')
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class NotificationMessage(Base):
    __tablename__ = 'wg_notification_messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    alert_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AiConversation(Base):
    __tablename__ = 'wg_ai_conversations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    session_id: Mapped[str] = mapped_column(String(64), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class InspectionRecord(Base):
    __tablename__ = 'wg_inspection_records'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    area_name: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class RagPlan(Base):
    __tablename__ = 'wg_rag_plans'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    alert_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(128), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    steps: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array as string
    qa_hint: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
