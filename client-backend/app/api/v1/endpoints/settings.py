from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.entities import SystemSetting

router = APIRouter(prefix='/settings', tags=['settings'])


class SettingsUpdate(BaseModel):
    alert: bool
    system: bool
    offline: bool
    darkMode: bool
    language: str


@router.get('')
async def get_settings(db: AsyncSession = Depends(get_db)) -> dict:
    setting = await db.scalar(select(SystemSetting).limit(1))
    if setting is None:
        return {'code': 404, 'message': '设置不存在'}

    return {
        'code': 200,
        'data': {
            'notificationSettings': {
                'alert': setting.alert_notify,
                'system': setting.system_notify,
                'offline': setting.offline_notify,
            },
            'displaySettings': {
                'darkMode': setting.dark_mode,
                'language': setting.language,
            },
            'cacheSize': '12.5 MB',
            'appVersion': 'v1.0.0',
        },
    }


@router.put('')
async def update_settings(payload: SettingsUpdate, db: AsyncSession = Depends(get_db)) -> dict:
    setting = await db.scalar(select(SystemSetting).limit(1))
    if setting is None:
        setting = SystemSetting()
        db.add(setting)

    setting.alert_notify = payload.alert
    setting.system_notify = payload.system
    setting.offline_notify = payload.offline
    setting.dark_mode = payload.darkMode
    setting.language = payload.language
    await db.commit()

    return {'code': 200, 'message': '设置已保存'}
