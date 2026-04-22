"""清空 ORM 管理的全部表并重建结构；下次启动 API 时会自动种子数据。"""
import asyncio

from sqlalchemy import text
from app.db.session import engine
from app.models.entities import Base


async def main() -> None:
    try:
        async with engine.begin() as conn:
            # 先删除 rag_plans 表，再删除其他表
            await conn.execute(text("DROP TABLE IF EXISTS wg_alert_rag_plans CASCADE"))
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("OK: 已 drop_all + create_all，请执行 python run.py 启动服务。")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
