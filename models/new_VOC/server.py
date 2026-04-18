from __future__ import annotations

import csv
from collections import deque
from datetime import datetime
from typing import Deque, Dict, List, Optional

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.config import DataConfig
from src.predictor import VOCSMambaPredictor, get_local_timestamp
from src.schemas import Alert, PredictionResult, SensorData


class VOCSMambaSystemManager:
    def __init__(self):
        self.data_config = DataConfig()
        self.predictor = VOCSMambaPredictor(self.data_config)
        self.sensor_data_buffer: Deque[SensorData] = deque(maxlen=self.data_config.seq_len)
        self.predictions: List[PredictionResult] = []
        self.alerts: List[Alert] = []
        self.latest_prediction: Optional[PredictionResult] = None
        self.system_start_time = datetime.now()
        self.csv_records = 0
        self.csv_fieldnames = list(SensorData.model_fields.keys())
        self.data_config.realtime_csv.parent.mkdir(parents=True, exist_ok=True)
        self.predictor.load()
        self.load_data_from_csv()

    def load_data_from_csv(self) -> int:
        if not self.data_config.realtime_csv.exists():
            self.csv_records = 0
            return 0
        df = pd.read_csv(self.data_config.realtime_csv)
        self.csv_records = len(df)
        self.sensor_data_buffer.clear()
        for row in df.tail(self.data_config.seq_len).to_dict(orient="records"):
            self.sensor_data_buffer.append(SensorData(**row))
        return self.csv_records

    def save_data_to_csv(self, data: SensorData) -> None:
        payload = data.model_dump()
        payload["timestamp"] = pd.to_datetime(payload["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        file_exists = self.data_config.realtime_csv.exists()
        with open(self.data_config.realtime_csv, "a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.csv_fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(payload)
        self.csv_records += 1

    def add_sensor_data(self, data: SensorData) -> Optional[PredictionResult]:
        self.save_data_to_csv(data)
        self.sensor_data_buffer.append(data)
        if len(self.sensor_data_buffer) < self.data_config.seq_len:
            return None
        prediction = self.predictor.predict(self.sensor_data_buffer)
        alert = self.predictor.maybe_build_alert(prediction)
        if alert:
            prediction.alert_triggered = True
            prediction.alert_message = alert.message
            self.alerts.insert(0, alert)
        self.latest_prediction = prediction
        self.predictions.append(prediction)
        return prediction

    def get_latest_sensor_data(self) -> Optional[SensorData]:
        return self.sensor_data_buffer[-1] if self.sensor_data_buffer else None

    def get_status(self) -> Dict:
        uptime = datetime.now() - self.system_start_time
        return {
            "system_name": "new_VOC",
            "status": "running",
            "model_loaded": self.predictor.model is not None,
            "data_fields_count": 26,
            "seq_len": self.data_config.seq_len,
            "pred_len": self.data_config.pred_len,
            "csv_file_path": str(self.data_config.realtime_csv),
            "csv_total_records": self.csv_records,
            "memory_buffer_size": len(self.sensor_data_buffer),
            "total_predictions": len(self.predictions),
            "total_alerts": len(self.alerts),
            "uptime_seconds": int(uptime.total_seconds()),
        }


system_manager = VOCSMambaSystemManager()
app = FastAPI(title="new_VOC", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "system": "new_VOC",
        "status": "running",
        "input_contract": "26 sensor fields",
        "model_contract": {"seq_len": 96, "input_dim": 51, "pred_len": 24},
    }


@app.get("/status")
async def get_status():
    return system_manager.get_status()


@app.post("/sensor-data")
async def receive_sensor_data(data: SensorData):
    prediction = system_manager.add_sensor_data(data)
    return {
        "success": True,
        "message": "Data received",
        "data_received": {"timestamp": data.timestamp, "rto_out_conc": data.rto_out_conc},
        "prediction_triggered": prediction is not None,
        "buffer_size": len(system_manager.sensor_data_buffer),
    }


@app.get("/predictions", response_model=List[PredictionResult])
async def get_predictions(limit: int = 10):
    return system_manager.predictions[-limit:]


@app.get("/predictions/latest", response_model=Optional[PredictionResult])
async def get_latest_prediction():
    return system_manager.latest_prediction


@app.get("/alerts", response_model=List[Alert])
async def get_alerts(limit: int = 50):
    return system_manager.alerts[:limit]


@app.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    for alert in system_manager.alerts:
        if alert.alert_id == alert_id:
            alert.acknowledged = True
            return {"success": True, "message": "Alert acknowledged"}
    raise HTTPException(status_code=404, detail="Alert not found")


@app.get("/sensor-data/latest")
async def get_latest_sensor_data():
    latest = system_manager.get_latest_sensor_data()
    if latest is None:
        return {"message": "No data"}
    return latest.model_dump()


def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002, log_level="info")


if __name__ == "__main__":
    main()
