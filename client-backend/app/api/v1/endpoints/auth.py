from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.core.security import get_current_username, hash_password, verify_password
from app.db.session import get_db
from app.models.entities import UserProfile

router = APIRouter(prefix='/auth', tags=['auth'])


class TokenRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class UserResponse(BaseModel):
    username: str
    role: str
    name: str
    email: str
    phone: str
    department: str
    joinDate: str


class RegisterRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    name: str = Field(min_length=1, max_length=64)
    email: str = Field(min_length=5, max_length=128, pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    phone: str = Field(min_length=6, max_length=32)
    department: str = Field(min_length=1, max_length=64)
    role: str = '普通用户'


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=6, max_length=128)


def serialize_user(profile: UserProfile) -> UserResponse:
    return UserResponse(
        username=profile.username,
        role=profile.role,
        name=profile.name,
        email=profile.email,
        phone=profile.phone,
        department=profile.department,
        joinDate=profile.join_date.strftime('%Y-%m-%d'),
    )


async def get_user_by_username(db: AsyncSession, username: str) -> UserProfile | None:
    return await db.scalar(select(UserProfile).where(UserProfile.username == username).limit(1))


async def authenticate_user(db: AsyncSession, username: str, password: str) -> UserProfile:
    profile = await get_user_by_username(db, username)
    if profile is None or not verify_password(password, profile.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid username or password')
    return profile


def build_auth_response(profile: UserProfile) -> dict:
    token = create_access_token(subject=profile.username)
    return {
        'code': 200,
        'data': {
            'access_token': token,
            'token_type': 'bearer',
            'user': serialize_user(profile).model_dump(),
        },
    }


@router.post('/token')
async def issue_token(payload: TokenRequest, db: AsyncSession = Depends(get_db)) -> dict:
    profile = await authenticate_user(db, payload.username, payload.password)
    return build_auth_response(profile)


@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)) -> dict:
    profile = await authenticate_user(db, request.username, request.password)
    return build_auth_response(profile)


@router.post('/register')
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)) -> dict:
    profile = await get_user_by_username(db, request.username)
    if profile is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='用户名已存在')

    profile = UserProfile(
        username=request.username,
        password_hash=hash_password(request.password),
        role=request.role,
        name=request.name,
        email=request.email,
        phone=request.phone,
        department=request.department,
        join_date=date.today(),
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return build_auth_response(profile)


@router.get('/me')
async def read_current_user(
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    profile = await get_user_by_username(db, username)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='用户不存在')
    return {'code': 200, 'data': serialize_user(profile).model_dump()}
