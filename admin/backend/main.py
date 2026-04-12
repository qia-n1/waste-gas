from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.alerts import router as alerts_router
from routers.auth import router as auth_router
from routers.dashboard import router as dashboard_router


app = FastAPI(title=settings.app_name, version="0.1.0")

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


@app.get("/api/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
