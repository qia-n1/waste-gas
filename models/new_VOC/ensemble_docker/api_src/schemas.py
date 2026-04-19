from __future__ import annotations

from typing import List

from pydantic import BaseModel


class SensorData(BaseModel):
    timestamp: str
    feature_values: List[float]
