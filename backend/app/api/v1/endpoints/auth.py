from fastapi import APIRouter
from pydantic import BaseModel

from app.core.security import create_access_token

router = APIRouter(prefix='/auth', tags=['auth'])


class TokenRequest(BaseModel):
    username: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


@router.post('/token', response_model=TokenResponse)
async def issue_token(payload: TokenRequest) -> TokenResponse:
    token = create_access_token(subject=payload.username)
    return TokenResponse(access_token=token)
