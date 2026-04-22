import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.init_db import init_db, seed_if_empty
from app.db.session import SessionLocal

@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    await init_db()
    async with SessionLocal() as session:
        await seed_if_empty(session)
    # Skip ensure_zsq_test_data for now
    print("Database initialized successfully")
    yield
    print("Shutting down...")

settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(api_router, prefix='/api/v1')

@app.get('/')
def read_root():
    return {'message': 'Welcome to Waste Gas Monitoring API'}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8002)