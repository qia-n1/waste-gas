"""开发环境：周期性写入模拟传感器读数，便于前端轮询从数据库看到变化。"""
import asyncio
import logging
import random
from datetime import datetime

from sqlalchemy import desc, select

from app.db.session import SessionLocal
from app.models.entities import SensorReading

logger = logging.getLogger(__name__)

INTERVAL_SEC = 30.0


async def sensor_demo_writer_loop() -> None:
    await asyncio.sleep(5)
    while True:
        try:
            async with SessionLocal() as session:
                stmt = (
                    select(SensorReading)
                    .where(SensorReading.device_id == 'DEV-001')
                    .order_by(desc(SensorReading.recorded_at))
                    .limit(1)
                )
                last = (await session.execute(stmt)).scalar_one_or_none()
                base_vocs = float(last.vocs) if last else 28.0
                base_vocs = max(8.0, min(92.0, base_vocs + random.uniform(-3.5, 3.5)))
                base_temp = float(last.temperature) if last else 25.0
                base_hum = float(last.humidity) if last else 48.0
                base_press = float(last.pressure) if last else 100.8
                ts = datetime.now()
                session.add(
                    SensorReading(
                        device_id='DEV-001',
                        recorded_at=ts,
                        vocs=round(base_vocs, 2),
                        temperature=round(max(15.0, min(38.0, base_temp + random.uniform(-1.2, 1.2))), 2),
                        humidity=round(max(25.0, min(78.0, base_hum + random.uniform(-4.0, 4.0))), 2),
                        pressure=round(max(97.0, min(104.0, base_press + random.uniform(-0.4, 0.4))), 2),
                    )
                )
                await session.commit()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception('sensor_demo_writer failed')
        await asyncio.sleep(INTERVAL_SEC)
