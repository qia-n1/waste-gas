from fastapi import APIRouter
from app.api.v1.endpoints import alerts, auth, dashboard, health, monitor, profile, rag, settings, system

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(system.router)
api_router.include_router(rag.router)
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(monitor.router)
api_router.include_router(alerts.router)
api_router.include_router(profile.router)
api_router.include_router(settings.router)