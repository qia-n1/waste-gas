from __future__ import annotations

import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
import torch
from numpy.lib.stride_tricks import sliding_window_view
from tqdm.auto import tqdm

from .config import DataConfig, ModelConfig
from .features import VOCSFeaturePipeline
from .model import VocsMambaForecaster
from .schemas import Alert, PredictionResult, SensorData


try:
    torch.set_float32_matmul_precision("high")
except (AttributeError, RuntimeError):
    pass


def get_local_timestamp() -> str:
    return datetime.now().astimezone().isoformat()


def resolve_device(explicit_device: str | None = None) -> torch.device:
    if explicit_device:
        return torch.device(explicit_device)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


class VOCSMambaPredictor:
    def __init__(
        self,
        data_config: DataConfig | None = None,
        model_config: ModelConfig | None = None,
        checkpoint_path: Path | None = None,
        scaler_path: Path | None = None,
        device: str | None = None,
    ):
        self.data_config = data_config or DataConfig()
        self.model_config = model_config or ModelConfig()
        self.checkpoint_path = checkpoint_path or self.data_config.checkpoint_path
        self.scaler_path = scaler_path or self.data_config.scaler_path
        self.device = resolve_device(device)
        self.pipeline: VOCSFeaturePipeline | None = None
        self.model: VocsMambaForecaster | None = None

    def _move_tensor(self, array: np.ndarray) -> torch.Tensor:
        tensor = torch.from_numpy(array)
        return tensor.to(self.device, non_blocking=self.device.type == "cuda")

    def load(self) -> bool:
        if not Path(self.scaler_path).exists() or not Path(self.checkpoint_path).exists():
            return False
        self.pipeline = VOCSFeaturePipeline.load(self.scaler_path, self.data_config)
        checkpoint = torch.load(self.checkpoint_path, map_location="cpu", weights_only=False)
        model_cfg = checkpoint.get("model_config")
        if model_cfg:
            self.model_config = ModelConfig(**model_cfg)
        input_dim = checkpoint.get("input_dim") or self.pipeline.input_dim
        self.model = VocsMambaForecaster(
            input_dim=input_dim,
            config=self.model_config,
            pred_len=self.data_config.pred_len,
        )
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.to(self.device)
        self.model.eval()
        return True

    def warmup_prediction(self, records: Sequence[SensorData]) -> PredictionResult:
        vocs_values = [record.rto_out_conc for record in records]
        avg_value = float(np.mean(vocs_values)) if vocs_values else 0.0
        trend = 0.0
        if len(vocs_values) >= 5:
            trend = (vocs_values[-1] - vocs_values[-5]) / 5.0
        predicted = []
        for idx in range(self.data_config.pred_len):
            predicted_value = max(0.0, min(500.0, avg_value + trend * (idx / 4.0)))
            predicted.append(float(predicted_value))
        return PredictionResult(
            timestamp=get_local_timestamp(),
            prediction_horizon=self.data_config.pred_len,
            predicted_values=predicted,
            confidence=min(0.85, 0.40 + 0.45 * len(records) / self.data_config.seq_len),
            alert_triggered=False,
            alert_message=f"Warmup prediction ({len(records)}/{self.data_config.seq_len})",
            prediction_type="Warmup",
        )

    def predict(self, records: Sequence[SensorData]) -> PredictionResult:
        if len(records) < self.data_config.seq_len:
            return self.warmup_prediction(records)
        if self.pipeline is None or self.model is None:
            loaded = self.load()
            if not loaded:
                return self.warmup_prediction(records)

        assert self.pipeline is not None
        assert self.model is not None
        frame = self.pipeline.sensor_records_to_frame(records[-self.data_config.seq_len :])
        features = self.pipeline.transform_frame(frame)
        tensor = self._move_tensor(features).unsqueeze(0)
        with torch.inference_mode():
            prediction_scaled = self.model(tensor).squeeze(0).cpu().numpy()
        prediction = self.pipeline.target_scaler.inverse_transform(prediction_scaled).reshape(-1)
        prediction = np.clip(prediction, 0.0, 500.0)
        return PredictionResult(
            timestamp=get_local_timestamp(),
            prediction_horizon=self.data_config.pred_len,
            predicted_values=prediction.tolist(),
            confidence=0.86,
            alert_triggered=False,
            alert_message="new_VOC prediction",
            prediction_type="Mamba3-SISO",
        )

    def predict_dataframe(
        self,
        df: pd.DataFrame,
        stride: int = 1,
        show_progress: bool = True,
        batch_size: int = 256,
    ) -> pd.DataFrame:
        if self.pipeline is None or self.model is None:
            loaded = self.load()
            if not loaded:
                raise FileNotFoundError(
                    f"Checkpoint or scaler not found: {self.checkpoint_path}, {self.scaler_path}"
                )

        assert self.pipeline is not None
        assert self.model is not None

        if len(df) < self.data_config.seq_len:
            return pd.DataFrame()

        features = self.pipeline.transform_frame(df)
        windows = sliding_window_view(features, window_shape=self.data_config.seq_len, axis=0)
        windows = np.swapaxes(windows, 1, 2)

        step = max(1, stride)
        selected_windows = np.ascontiguousarray(windows[::step], dtype=np.float32)
        window_end_indices = range(self.data_config.seq_len - 1, len(df), step)

        prediction_batches = []
        batch_indices = range(0, len(selected_windows), max(1, batch_size))
        iterator = tqdm(batch_indices, desc="Inference", unit="batch") if show_progress else batch_indices
        with torch.inference_mode():
            for start_idx in iterator:
                batch = selected_windows[start_idx : start_idx + max(1, batch_size)]
                if len(batch) == 0:
                    continue
                batch_tensor = self._move_tensor(batch)
                pred_scaled = self.model(batch_tensor).cpu().numpy()
                prediction_batches.append(pred_scaled)

        if prediction_batches:
            prediction_scaled = np.concatenate(prediction_batches, axis=0)
        else:
            prediction_scaled = np.empty((0, self.data_config.pred_len, 1), dtype=np.float32)

        flat_prediction = prediction_scaled.reshape(-1, 1)
        restored = self.pipeline.target_scaler.inverse_transform(flat_prediction)
        restored = restored.reshape(-1, self.data_config.pred_len)
        restored = np.clip(restored, 0.0, 500.0)

        rows = []
        for row_idx, end_idx in enumerate(window_end_indices):
            pred = restored[row_idx]
            row = {
                "window_end": str(df.iloc[end_idx]["timestamp"]),
                "max_prediction": float(np.max(pred)),
                "mean_prediction": float(np.mean(pred)),
            }
            for step_idx, value in enumerate(pred, start=1):
                row[f"t+{step_idx}"] = float(value)
            rows.append(row)
        return pd.DataFrame(rows)

    def maybe_build_alert(self, prediction: PredictionResult) -> Alert | None:
        max_value = max(prediction.predicted_values)
        if max_value <= self.data_config.exceed_threshold:
            return None
        return Alert(
            alert_id=f"ALT-{uuid.uuid4().hex[:10].upper()}",
            timestamp=get_local_timestamp(),
            level="critical" if max_value > 100 else "warning",
            message=f"VOCs threshold exceeded! Max: {max_value:.2f}, Threshold: {self.data_config.exceed_threshold}",
            value=float(max_value),
            threshold=self.data_config.exceed_threshold,
            acknowledged=False,
        )
