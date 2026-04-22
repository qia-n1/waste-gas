"""共享 PostgreSQL 连接池。

所有访问云数据库 (aqimonitor) 的代码都通过这里拿连接，避免到处 connect。
连接池在 FastAPI lifespan 启动时 init_pool()，关闭时 close_pool()。

用法：
    from services.db import cursor

    with cursor() as cur:
        cur.execute("SELECT * FROM wg_alerts WHERE id = %s", (alert_id,))
        row = cur.fetchone()

提交 / 回滚由 context manager 自动处理：
- 正常退出 → commit
- 抛异常   → rollback
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

import psycopg2
from psycopg2.extensions import cursor as PgCursor
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

from config import settings


_pool: Optional[ThreadedConnectionPool] = None


def init_pool() -> None:
    """在应用启动时调用一次。重复调用是幂等的。"""
    global _pool
    if _pool is not None:
        return
    _pool = ThreadedConnectionPool(
        minconn=settings.pg_pool_min,
        maxconn=settings.pg_pool_max,
        host=settings.pg_host,
        port=settings.pg_port,
        dbname=settings.pg_db,
        user=settings.pg_user,
        password=settings.pg_password,
        connect_timeout=settings.pg_connect_timeout,
    )
    print(
        f"[DB] connection pool ready -> {settings.pg_user}@{settings.pg_host}:"
        f"{settings.pg_port}/{settings.pg_db}  (min={settings.pg_pool_min}, max={settings.pg_pool_max})"
    )


def close_pool() -> None:
    """在应用关闭时调用。"""
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
        print("[DB] connection pool closed")


def is_ready() -> bool:
    return _pool is not None


@contextmanager
def cursor(dict_rows: bool = False) -> Iterator[PgCursor]:
    """获取一个事务性游标。
    Args:
        dict_rows: True 时使用 RealDictCursor，fetch* 返回字典而不是元组。
    """
    if _pool is None:
        raise RuntimeError("DB pool not initialized; call init_pool() first")

    conn = _pool.getconn()
    try:
        cur_factory = RealDictCursor if dict_rows else None
        with conn.cursor(cursor_factory=cur_factory) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def health_check() -> bool:
    """返回 True 表示连接池可用。供启动自检/监控用。"""
    if _pool is None:
        return False
    try:
        with cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        return True
    except psycopg2.Error as exc:
        print(f"[DB] health check failed: {exc}")
        return False
