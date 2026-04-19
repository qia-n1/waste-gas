from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Any, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import get_settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/token')


def hash_password(password: str, salt: str | None = None) -> str:
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_value.encode('utf-8'),
        120000,
    )
    return f'{salt_value}${digest.hex()}'


def verify_password(password: str, stored_hash: str) -> bool:
    salt_value, separator, digest_value = stored_hash.partition('$')
    if not salt_value or separator != '$' or not digest_value:
        return False
    candidate = hash_password(password, salt_value)
    return hmac.compare_digest(candidate, stored_hash)


def create_access_token(subject: str, extra_claims: Optional[dict[str, Any]] = None) -> str:
    settings = get_settings()
    expire_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload: dict[str, Any] = {'sub': subject, 'exp': expire_at}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def get_current_username(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
        ) from exc

    subject = payload.get('sub')
    if not isinstance(subject, str) or not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid authentication credentials',
        )

    return subject
