from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Waste Gas Admin API"
    secret_key: str = os.getenv("ADMIN_JWT_SECRET", "waste-gas-admin-secret")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ADMIN_TOKEN_EXPIRE_MINUTES", "120"))
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123456")
    vocs_base_url: str = os.getenv("VOCS_BASE_URL", "http://127.0.0.1:8001")
    ensemble_base_url: str = os.getenv("ENSEMBLE_BASE_URL", "http://127.0.0.1:8000")
    request_timeout: float = float(os.getenv("VOCS_REQUEST_TIMEOUT", "4"))
    ensemble_timeout: float = float(os.getenv("ENSEMBLE_TIMEOUT", "10"))
    total_equipment: int = int(os.getenv("ADMIN_TOTAL_EQUIPMENT", "150"))
    csv_path: Path = Path(
        os.getenv(
            "VOCS_CSV_PATH",
            str(ROOT_DIR / "vocs_realtime_data" / "vocs_realtime_data.csv"),
        )
    )

    # PostgreSQL (云数据库) — 默认指向开发库；生产请用环境变量覆盖
    pg_host: str = os.getenv("PG_HOST", "98.142.241.155")
    pg_port: int = int(os.getenv("PG_PORT", "5432"))
    pg_db: str = os.getenv("PG_DB", "aqimonitor")
    pg_user: str = os.getenv("PG_USER", "team")
    pg_password: str = os.getenv("PG_PASSWORD", "fwwb1234")
    pg_pool_min: int = int(os.getenv("PG_POOL_MIN", "1"))
    pg_pool_max: int = int(os.getenv("PG_POOL_MAX", "8"))
    pg_connect_timeout: int = int(os.getenv("PG_CONNECT_TIMEOUT", "10"))


settings = Settings()
