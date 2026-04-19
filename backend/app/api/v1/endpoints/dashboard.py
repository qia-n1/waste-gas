from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/overview")
async def get_dashboard_overview(window: str = "24h"):
    # Mock data for demonstration
    return {
        "code": 200,
        "data": {
            "actual_series": [
                {"time": "2026-04-08 10:00", "vocs": 45.2},
                {"time": "2026-04-08 10:15", "vocs": 48.1}
            ],
            "forecast_series": [
                {"time": "2026-04-08 10:30", "vocs": 55.4, "lower": 50.1, "upper": 60.2},
                {"time": "2026-04-08 10:45", "vocs": 82.3, "lower": 76.0, "upper": 88.1}
            ],
            "threshold": 80,
            "model_version": "seq2seq_v2",
            "base_time": "2026-04-08 10:15"
        }
    }