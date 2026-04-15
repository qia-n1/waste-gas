from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import serialize_user
from app.core.security import get_current_username
from app.db.session import get_db
from app.models.entities import UserProfile

router = APIRouter(prefix='/profile', tags=['profile'])


@router.get('/me')
async def get_my_profile(
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile = await db.scalar(select(UserProfile).where(UserProfile.username == username).limit(1))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='用户不存在')

    return {
        'code': 200,
        'data': serialize_user(profile).model_dump(),
    }
