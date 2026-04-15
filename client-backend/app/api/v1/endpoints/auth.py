from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.security import create_access_token

router = APIRouter(prefix='/auth', tags=['auth'])


class TokenRequest(BaseModel):
    username: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post('/token', response_model=TokenResponse)
async def issue_token(payload: TokenRequest) -> TokenResponse:
    token = create_access_token(subject=payload.username)
    return TokenResponse(access_token=token)


@router.post("/login")
async def login(request: LoginRequest):
    # Mock authentication logic
    if request.username == "admin" and request.password == "password":
        token = create_access_token(subject=request.username)
        return {"code": 200, "data": {"access_token": token, "token_type": "bearer"}}
    raise HTTPException(status_code=400, detail="Invalid username or password")
