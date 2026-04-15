from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.entities import UserProfile

router = APIRouter(prefix='/profile', tags=['profile'])


@router.get('/me')
async def get_my_profile(db: AsyncSession = Depends(get_db)) -> dict:
    profile = await db.scalar(select(UserProfile).where(UserProfile.username == 'admin').limit(1))
    if profile is None:
        return {'code': 404, 'message': '用户不存在'}

    return {
        'code': 200,
        'data': {
            'username': profile.username,
            'role': profile.role,
            'name': profile.name,
            'email': profile.email,
            'phone': profile.phone,
            'department': profile.department,
            'joinDate': profile.join_date.strftime('%Y-%m-%d'),
        },
    }
