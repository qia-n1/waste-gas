from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

import numpy as np
import pandas as pd
import torch


SENSOR_COLUMNS = [
    "timestamp",
    "ambient_temp",
    "ambient_humidity",
    "ambient_pressure",
    "coating_flow",
    "coating_conc",
    "coating_temp",
    "coating_pressure",
    "rotor_speed",
    "adsorption_fan_power",
    "desorption_fan_power",
    "rotor_inlet_temp",
    "rotor_inlet_humid",
    "desorption_temp",
    "concentrated_flow",
    "concentrated_conc",
    "concentrated_temp",
    "concentrated_pressure",
    "rto_in_flow",
    "rto_in_temp",
    "rto_in_pressure",
    "burner_gas_flow",
    "combustion_temp",
    "rto_in_conc",
    "rto_out_conc",
    "rto_out_temp",
]

FEATURE_GROUP_MAP = {
    "ambient_temp": "废气源与环境组",
    "ambient_humidity": "废气源与环境组",
    "ambient_pressure": "废气源与环境组",
    "coating_flow": "废气源与环境组",
    "coating_conc": "废气源与环境组",
    "coating_temp": "废气源与环境组",
    "coating_pressure": "废气源与环境组",
    "rotor_speed": "转轮浓缩系统",
    "adsorption_fan_power": "转轮浓缩系统",
    "desorption_fan_power": "转轮浓缩系统",
    "rotor_inlet_temp": "转轮浓缩系统",
    "rotor_inlet_humid": "转轮浓缩系统",
    "desorption_temp": "转轮浓缩系统",
    "concentrated_flow": "转轮浓缩系统",
    "concentrated_conc": "转轮浓缩系统",
    "concentrated_temp": "转轮浓缩系统",
    "concentrated_pressure": "转轮浓缩系统",
    "rto_in_flow": "RTO焚烧系统",
    "rto_in_temp": "RTO焚烧系统",
    "rto_in_pressure": "RTO焚烧系统",
    "rto_in_conc": "RTO焚烧系统",
    "rto_out_conc": "RTO焚烧系统",
    "burner_gas_flow": "RTO焚烧系统",
    "combustion_temp": "RTO焚烧系统",
    "rto_out_temp": "RTO焚烧系统",
}

GROUP_ORDER = ["废气源与环境组", "转轮浓缩系统", "RTO焚烧系统"]

CORE_COVARIATES = [
    "ambient_temp",
    "ambient_humidity",
    "ambient_pressure",
    "coating_flow",
    "coating_conc",
    "coating_temp",
    "coating_pressure",
    "rotor_speed",
    "adsorption_fan_power",
    "desorption_fan_power",
    "rotor_inlet_temp",
    "rotor_inlet_humid",
    "desorption_temp",
    "concentrated_flow",
    "concentrated_conc",
    "concentrated_temp",
    "concentrated_pressure",
    "rto_in_flow",
    "rto_in_temp",
    "rto_in_pressure",
    "burner_gas_flow",
    "combustion_temp",
    "rto_out_temp",
]


@dataclass
class ModuleRuntimeConfig:
    seq_len: int = 96
    pred_len: int = 24
    exceed_threshold: float = 80.0
    baseline_value: float = 35.0


class VOCSInferenceModule:
    """Decoupled inference module: preprocessing -> model inference -> response assembly."""

    def __init__(self, config: ModuleRuntimeConfig | None = None):
        self.config = config or ModuleRuntimeConfig()

    @staticmethod
    def _rolling_linear_trend(values: np.ndarray, window: int) -> np.ndarray:
        if len(values) < window or window < 2:
            return np.zeros(len(values), dtype=np.float32)
        x = np.arange(window)
        out = np.zeros(len(values), dtype=np.float32)
        for i in range(window - 1, len(values)):
            y = values[i - window + 1 : i + 1]
            slope = np.polyfit(x, y, 1)[0]
            out[i] = np.float32(slope)
        return out

    def records_to_frame(self, data_sequence: Sequence[Any]) -> pd.DataFrame:
        feature_columns = SENSOR_COLUMNS[1:]
        rows: List[Dict[str, Any]] = []
        for item in data_sequence:
            timestamp = getattr(item, "timestamp", None)
            values = getattr(item, "feature_values", None)
            if isinstance(item, dict):
                if timestamp is None:
                    timestamp = item.get("timestamp")
                if values is None:
                    values = item.get("feature_values")
            if not isinstance(values, list):
                values = []

            row: Dict[str, Any] = {"timestamp": str(timestamp or "")}
            for idx, col in enumerate(feature_columns):
                row[col] = float(values[idx]) if idx < len(values) else 0.0
            rows.append(row)
        return pd.DataFrame(rows)

    def preprocess(self, frame: pd.DataFrame, feature_scaler, target_scaler, expected_input_dim: int) -> np.ndarray:
        df = frame.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        df["hour_sin"] = np.sin(2 * np.pi * df["timestamp"].dt.hour / 24)
        df["hour_cos"] = np.cos(2 * np.pi * df["timestamp"].dt.hour / 24)
        df["weekday_sin"] = np.sin(2 * np.pi * df["timestamp"].dt.weekday / 7)
        df["weekday_cos"] = np.cos(2 * np.pi * df["timestamp"].dt.weekday / 7)
        df["month_sin"] = np.sin(2 * np.pi * df["timestamp"].dt.month / 12)
        df["month_cos"] = np.cos(2 * np.pi * df["timestamp"].dt.month / 12)

        target_col = "rto_out_conc"
        windows = [6, 12, 24, 48, 96]
        target_values = df[target_col].astype(float).to_numpy()
        for window in windows:
            df[f"{target_col}_rolling_mean_{window}"] = df[target_col].rolling(window=window, min_periods=1).mean()
            df[f"{target_col}_rolling_std_{window}"] = df[target_col].rolling(window=window, min_periods=1).std().fillna(0)
            df[f"{target_col}_rolling_trend_{window}"] = self._rolling_linear_trend(target_values, window)

        df[f"{target_col}_diff_1"] = df[target_col].diff(1).fillna(0)
        df[f"{target_col}_diff_4"] = df[target_col].diff(4).fillna(0)
        df[f"{target_col}_diff_24"] = df[target_col].diff(24).fillna(0)
        df[f"{target_col}_diff_96"] = df[target_col].diff(96).fillna(0)
        df[f"{target_col}_ma_diff_24"] = df[target_col] - df[f"{target_col}_rolling_mean_24"]

        # Keep the same explicit-trend feature family as v6 training pipeline.
        trend_columns = [target_col] + [col for col in CORE_COVARIATES if col in df.columns]
        for col in trend_columns:
            df[f"{col}_diff_1"] = df[col].diff(1).fillna(0)
            df[f"{col}_diff_2"] = df[col].diff(2).fillna(0)

        exclude_cols = ["timestamp", "rto_out_conc"]
        feature_columns = [col for col in df.columns if col not in exclude_cols]
        X = df[feature_columns].values
        y = df["rto_out_conc"].values.reshape(-1, 1)

        if not hasattr(feature_scaler, "scale_") or not hasattr(target_scaler, "scale_"):
            raise ValueError("Scalers are not ready. Fixed v6 deployment requires pre-fitted scaler artifacts.")

        X_scaled = feature_scaler.transform(X)
        y_scaled = target_scaler.transform(y)

        features = np.concatenate([X_scaled, y_scaled], axis=1).astype(np.float32)
        if features.shape[1] > expected_input_dim:
            features = features[:, :expected_input_dim]
        elif features.shape[1] < expected_input_dim:
            padding = np.zeros((features.shape[0], expected_input_dim - features.shape[1]), dtype=np.float32)
            features = np.concatenate([features, padding], axis=1)
        return features

    def infer(self, features: np.ndarray, model, target_scaler, frame: pd.DataFrame | None = None) -> np.ndarray:
        if model is None:
            raise ValueError("Model is not loaded. Fixed v6 deployment requires loaded v6 model artifact.")

        tensor = torch.FloatTensor(features).unsqueeze(0)
        with torch.no_grad():
            predictions = model(tensor)
        pred_scaled = predictions.squeeze().cpu().numpy().reshape(-1, 1)
        pred = target_scaler.inverse_transform(pred_scaled).flatten()
        pred = np.clip(pred, 0.0, 500.0)
        if len(pred) != self.config.pred_len:
            pred = np.resize(pred, self.config.pred_len)
        return pred.astype(np.float32)

    def build_alerts(self, predictions: np.ndarray) -> tuple[bool, List[Dict[str, Any]]]:
        alerts: List[Dict[str, Any]] = []
        exceed = False
        for idx, value in enumerate(predictions.tolist(), start=1):
            if value > self.config.exceed_threshold:
                exceed = True
                alerts.append({
                    "step": idx,
                    "value": float(value),
                    "warning": "污染物超标预警!",
                })
        return exceed, alerts

    def _feature_contributions(self, data_sequence: Sequence[Any], total_increment: float, preds: np.ndarray) -> List[Dict[str, Any]]:
        rows: List[List[float]] = []
        for item in data_sequence:
            values = getattr(item, "feature_values", None)
            if isinstance(item, dict) and values is None:
                values = item.get("feature_values")
            if isinstance(values, list) and values:
                rows.append([float(v) for v in values])

        if not rows:
            return []

        x = np.asarray(rows, dtype=np.float64)
        feature_names = SENSOR_COLUMNS[1:1 + x.shape[1]]
        mu = x.mean(axis=0)
        sigma = x.std(axis=0) + 1e-6
        level = np.abs(x[-1] - mu) / sigma
        trend = np.abs(x[-1] - x[0]) / sigma
        vol = x.std(axis=0)

        pred_peak = float(np.max(preds)) if preds.size else 0.0
        exceed_pressure = max(0.0, pred_peak - self.config.exceed_threshold) / self.config.exceed_threshold
        raw = (0.50 * level + 0.30 * trend + 0.20 * vol) * (1.0 + 0.35 * exceed_pressure)
        raw = np.clip(raw, 0.0, None)

        top_k = min(12, len(raw))
        top_idx = np.argsort(raw)[-top_k:]
        score_sum = float(raw[top_idx].sum())
        if score_sum <= 1e-12:
            return []

        rows_out: List[Dict[str, Any]] = []
        for idx in top_idx:
            ratio = float(raw[idx] / score_sum)
            name = feature_names[int(idx)]
            rows_out.append(
                {
                    "feature": name,
                    "group": FEATURE_GROUP_MAP.get(name, "废气源与环境组"),
                    "ratio": ratio,
                    "contribution": float(total_increment * ratio),
                }
            )
        rows_out.sort(key=lambda row: float(row["ratio"]), reverse=True)
        return rows_out

    @staticmethod
    def _group_contributions(feature_rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        grouped: Dict[str, float] = {}
        for row in feature_rows:
            group = str(row.get("group", "废气源与环境组"))
            if group not in GROUP_ORDER:
                group = "废气源与环境组"
            grouped[group] = grouped.get(group, 0.0) + float(row.get("contribution", 0.0))

        rows: List[Dict[str, Any]] = []
        for group in GROUP_ORDER:
            rows.append({"group": group, "contribution": float(grouped.get(group, 0.0))})
        return rows

    def _build_heatmap(self, preds: np.ndarray, group_rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        rows = list(group_rows)
        if not rows:
            rows = [{"group": group, "contribution": 0.0} for group in GROUP_ORDER]

        groups = [str(row["group"]) for row in rows]
        group_vals = np.array([float(row.get("contribution", 0.0)) for row in rows], dtype=np.float64)
        abs_vals = np.abs(group_vals)
        s = float(abs_vals.sum())
        group_weights = abs_vals / s if s > 1e-12 else np.ones(len(groups), dtype=np.float64) / len(groups)

        step_base = np.abs(preds.astype(np.float64))
        step_sum = float(step_base.sum())
        if step_sum <= 1e-12:
            step_weights = np.ones(self.config.pred_len, dtype=np.float64) / self.config.pred_len
        else:
            step_weights = step_base / step_sum

        matrix = np.outer(step_weights, group_weights)
        matrix = matrix.tolist()
        return {
            "time_steps": [f"t+{idx}" for idx in range(1, self.config.pred_len + 1)],
            "feature_groups": groups,
            "contribution_matrix": matrix,
        }

    def build_response(self, predictions: np.ndarray, data_sequence: Sequence[Any]) -> Dict[str, Any]:
        is_exceed_warning, alerts = self.build_alerts(predictions)
        baseline = float(self.config.baseline_value)
        target = float(np.mean(predictions))
        total_increment = float(target - baseline)

        feature_rows = self._feature_contributions(data_sequence, total_increment, predictions)
        group_rows = self._group_contributions(feature_rows)
        heatmap = self._build_heatmap(predictions, group_rows)

        return {
            "status": "success",
            "predictions": predictions.tolist(),
            "is_exceed_warning": is_exceed_warning,
            "alerts": alerts,
            "incremental_attribution": {
                "baseline": baseline,
                "target": target,
                "total_increment": total_increment,
                "feature_contributions": feature_rows,
                "group_contributions": group_rows,
                "heatmap": heatmap,
            },
        }

    def run(self, data_sequence: Sequence[Any], model, feature_scaler, target_scaler) -> Dict[str, Any]:
        frame = self.records_to_frame(data_sequence)
        if len(frame) != self.config.seq_len:
            raise ValueError(f"data_sequence length must be {self.config.seq_len}, got {len(frame)}")
        model_input_dim = int(model.encoder.weight_ih_l0.shape[1])
        features = self.preprocess(frame, feature_scaler, target_scaler, expected_input_dim=model_input_dim)
        predictions = self.infer(features, model, target_scaler, frame=frame)
        return self.build_response(predictions, data_sequence)
