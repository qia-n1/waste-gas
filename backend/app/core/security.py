from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi.security import OAuth2PasswordBearer

from app.core.config import get_settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/token')


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {'sub': subject, 'exp': expire_at}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
