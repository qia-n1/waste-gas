from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'VOCs Control Platform API'
    app_version: str = '0.1.0'
    api_v1_prefix: str = '/api/v1'
    debug: bool = False

    cors_origins: list[str] = Field(default_factory=lambda: ['*'])

    jwt_secret_key: str = 'replace-this-in-production'
    jwt_algorithm: str = 'HS256'
    jwt_expire_minutes: int = 60

    postgres_dsn: str = 'sqlite+aiosqlite:///./vocs.db'
    # Optional for client prototype; if empty/None, redis features are disabled.
    redis_url: Optional[str] = 'redis://localhost:6379/0'

    rag_enabled: bool = False
    chroma_persist_dir: str = './chroma_data'


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
