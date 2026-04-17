from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import serialize_user
from app.core.security import get_current_username, hash_password, verify_password
from app.db.session import get_db
from app.models.entities import AreaZone, DisposalRecord, InspectionRecord, NotificationMessage, UserProfile

router = APIRouter(prefix='/profile', tags=['profile'])


class PasswordChangeRequest(BaseModel):
    old_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    email: str = Field(min_length=3, max_length=128)
    phone: str = Field(min_length=6, max_length=32)


async def _get_profile(db: AsyncSession, username: str) -> UserProfile:
    profile = await db.scalar(select(UserProfile).where(UserProfile.username == username).limit(1))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='用户不存在')
    return profile


@router.get('/me')
async def get_my_profile(
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile = await _get_profile(db, username)
    areas = (await db.scalars(select(AreaZone).where(AreaZone.manager_username == username))).all()

    return {
        'code': 200,
        'data': {
            **serialize_user(profile).model_dump(),
            'areas': [item.name for item in areas],
        },
    }


@router.post('/change-password')
async def change_password(
    payload: PasswordChangeRequest,
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile = await _get_profile(db, username)
    if not verify_password(payload.old_password, profile.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='原密码不正确')
    profile.password_hash = hash_password(payload.new_password)
    await db.commit()
    return {'code': 200, 'message': '密码修改成功'}


@router.post('/update')
async def update_profile(
    payload: ProfileUpdateRequest,
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile = await _get_profile(db, username)
    profile.name = payload.name.strip()
    profile.email = payload.email.strip()
    profile.phone = payload.phone.strip()
    await db.commit()
    await db.refresh(profile)

    areas = (await db.scalars(select(AreaZone).where(AreaZone.manager_username == username))).all()
    return {
        'code': 200,
        'message': '个人信息更新成功',
        'data': {
            **serialize_user(profile).model_dump(),
            'areas': [item.name for item in areas],
        },
    }


@router.get('/notifications')
async def get_notifications(
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    rows = (await db.scalars(select(NotificationMessage).where(NotificationMessage.username == username).order_by(NotificationMessage.created_at.desc()))).all()
    return {
        'code': 200,
        'data': [
            {
                'id': row.id,
                'title': row.title,
                'content': row.content,
                'category': row.category,
                'level': row.level,
                'isRead': row.is_read,
                'createdAt': row.created_at.strftime('%Y-%m-%d %H:%M'),
                'alertId': row.alert_id,
            }
            for row in rows
        ],
    }


@router.get('/disposals')
async def get_my_disposals(
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    rows = (await db.scalars(select(DisposalRecord).where(DisposalRecord.username == username).order_by(DisposalRecord.created_at.desc()))).all()
    return {
        'code': 200,
        'data': [
            {
                'id': row.id,
                'alertId': row.alert_id,
                'result': row.result,
                'notes': row.notes,
                'photoUrl': row.photo_url,
                'status': row.status,
                'actionType': row.action_type,
                'createdAt': row.created_at.strftime('%Y-%m-%d %H:%M'),
            }
            for row in rows
        ],
    }


@router.get('/inspections')
async def get_inspections(
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    rows = (await db.scalars(select(InspectionRecord).where(InspectionRecord.username == username).order_by(InspectionRecord.created_at.desc()))).all()
    return {
        'code': 200,
        'data': [
            {
                'id': row.id,
                'areaName': row.area_name,
                'summary': row.summary,
                'createdAt': row.created_at.strftime('%Y-%m-%d %H:%M'),
            }
            for row in rows
        ],
    }
