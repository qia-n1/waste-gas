from fastapi import APIRouter
from app.api.v1.endpoints import auth, dashboard, alerts

api_router = APIRouter()

# Include authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include dashboard routes
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# Include alerts routes
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])