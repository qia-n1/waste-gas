import asyncio
from app.db.session import SessionLocal
from app.db.seed_zsq import ensure_zsq_test_data

async def test():
    async with SessionLocal() as session:
        print("Starting ensure_zsq_test_data...")
        try:
            await ensure_zsq_test_data(session)
            print("ensure_zsq_test_data completed successfully")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

asyncio.run(test())