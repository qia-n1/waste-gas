from typing import List

from pydantic import BaseModel


class SensorData(BaseModel):
    timestamp: str
    ambient_temp: float = 0.0
    ambient_humidity: float = 0.0
    ambient_pressure: float = 0.0
    coating_flow: float = 0.0
    coating_conc: float = 0.0
    coating_temp: float = 0.0
    coating_pressure: float = 0.0
    rotor_speed: float = 0.0
    adsorption_fan_power: float = 0.0
    desorption_fan_power: float = 0.0
    rotor_inlet_temp: float = 0.0
    rotor_inlet_humid: float = 0.0
    desorption_temp: float = 0.0
    concentrated_flow: float = 0.0
    concentrated_conc: float = 0.0
    concentrated_temp: float = 0.0
    concentrated_pressure: float = 0.0
    rto_in_flow: float = 0.0
    rto_in_conc: float = 0.0
    rto_in_temp: float = 0.0
    rto_in_pressure: float = 0.0
    burner_gas_flow: float = 0.0
    combustion_temp: float = 0.0
    rto_out_conc: float = 0.0
    rto_out_temp: float = 0.0


class PredictionResult(BaseModel):
    timestamp: str
    prediction_horizon: int
    predicted_values: List[float]
    confidence: float
    alert_triggered: bool
    alert_message: str
    prediction_type: str


class Alert(BaseModel):
    alert_id: str
    timestamp: str
    level: str
    message: str
    value: float
    threshold: float
    acknowledged: bool
