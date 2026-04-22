import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.init_db import init_db, seed_if_empty
from app.db.seed_zsq import ensure_zsq_test_data
from app.db.session import SessionLocal
from app.services.redis_client import close_redis
from app.services.scheduler import start_scheduler, stop_scheduler
from app.services.sensor_demo_writer import sensor_demo_writer_loop


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    await init_db()
    async with SessionLocal() as session:
        await seed_if_empty(session)
    async with SessionLocal() as session:
        await ensure_zsq_test_data(session)
    start_scheduler()
    writer_task = asyncio.create_task(sensor_demo_writer_loop())
    try:
        yield
    finally:
        writer_task.cancel()
        try:
            await writer_task
        except asyncio.CancelledError:
            pass
        stop_scheduler()
        await close_redis()


def create_app() -> FastAPI:
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

    return app


app = create_app()
