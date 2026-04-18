from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.alerts import router as alerts_router
from routers.auth import router as auth_router
from routers.data_fusion import router as data_fusion_router
from routers.dashboard import router as dashboard_router
from routers.users import router as users_router
from services.data_fusion import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(_: FastAPI):
    start_scheduler()
    try:
        yield
    finally:
        await stop_scheduler()


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(alerts_router)
app.include_router(users_router)
app.include_router(data_fusion_router)


@app.get("/api/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
