import asyncio
from sqlalchemy import text
from app.db.session import engine

async def check():
    async with engine.begin() as conn:
        result = await conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
        tables = [row[0] for row in result.fetchall()]
        print('Tables:', tables)

        result = await conn.execute(text('SELECT COUNT(*) FROM wg_area_zones'))
        count = result.scalar()
        print(f'wg_area_zones count: {count}')

        if count > 0:
            result = await conn.execute(text('SELECT id, name, manager_username FROM wg_area_zones'))
            for row in result.fetchall():
                print(f'  Zone: id={row[0]}, name={row[1]}, manager={row[2]}')
    await engine.dispose()

asyncio.run(check())