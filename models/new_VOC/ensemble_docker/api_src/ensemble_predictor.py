from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from api_src.config import DataConfig, ModelConfig, SENSOR_COLUMNS


@dataclass
class EnsembleRuntimeConfig:
    seq_len: int = 96
    pred_len: int = 24
    exceed_threshold: float = 80.0
    baseline_value: float = 35.0


class EnsemblePredictor:
    def __init__(self) -> None:
        self.config = EnsembleRuntimeConfig()
        self._loaded = False
        self._device = None
        self._pipeline = None
        self._model = None
        self._data_cfg = DataConfig(seq_len=self.config.seq_len, pred_len=self.config.pred_len)
        self._model_cfg = ModelConfig(d_model=256, n_layer=1)

    def is_loaded(self) -> bool:
        return bool(self._loaded)

    def load_models(self) -> None:
        try:
            import torch
            from api_src.features import VOCSFeaturePipeline
            from api_src.model import DLinearForecasterLarge

            base_dir = Path(__file__).resolve().parents[1]
            model_candidates = [
                base_dir / "models" / "pca_dlinear_large.pt",
                base_dir.parent / "artifacts_pca_ensemble" / "pca_dlinear_large.pt",
            ]
            csv_candidates = [
                base_dir / "data" / "vocs_dataset.csv",
                base_dir.parent.parent / "VOCS" / "src" / "data" / "vocs_dataset.csv",
            ]

            model_path = next((p for p in model_candidates if p.exists()), None)
            csv_path = next((p for p in csv_candidates if p.exists()), None)
            if model_path is None or csv_path is None:
                self._loaded = False
                return

            df = pd.read_csv(csv_path)
            data_cfg = DataConfig(seq_len=self.config.seq_len, pred_len=self.config.pred_len, dataset_csv=csv_path)
            data_cfg.pca_enabled = True
            pipeline = VOCSFeaturePipeline(data_cfg)
            pipeline.fit(df)

            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            model = DLinearForecasterLarge(
                input_dim=int(pipeline.input_dim),
                pred_len=self.config.pred_len,
                seq_len=self.config.seq_len,
                config=self._model_cfg,
                hidden_dims=(256, 128),
            ).to(device)
            model.load_state_dict(torch.load(model_path, map_location=device))
            model.eval()

            self._device = device
            self._pipeline = pipeline
            self._model = model
            self._loaded = True
        except Exception:
            self._loaded = False

    def _records_to_frame(self, sequence: Sequence[Any]) -> pd.DataFrame:
        feature_columns = SENSOR_COLUMNS[1:]
        rows = []
        for item in sequence:
            timestamp = getattr(item, "timestamp", None)
            if timestamp is None and isinstance(item, dict):
                timestamp = item.get("timestamp")
            values = getattr(item, "feature_values", None)
            if values is None and isinstance(item, dict):
                values = item.get("feature_values", [])
            if not isinstance(values, list):
                values = []

            row = {"timestamp": str(timestamp) if timestamp is not None else ""}
            for idx, col in enumerate(feature_columns):
                row[col] = float(values[idx]) if idx < len(values) else 0.0
            rows.append(row)
        return pd.DataFrame(rows)

    @staticmethod
    def _dynamic_feature_contributions(seq: Sequence[Any], total_increment: float, preds: np.ndarray) -> list[dict[str, float | str]]:
        feature_names = SENSOR_COLUMNS[1:25]
        group_map = {
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
            "rto_in_conc": "RTO焚烧系统",
            "rto_in_temp": "RTO焚烧系统",
            "rto_in_pressure": "RTO焚烧系统",
            "burner_gas_flow": "RTO焚烧系统",
            "combustion_temp": "RTO焚烧系统",
            "rto_out_temp": "RTO焚烧系统",
        }

        rows = []
        for item in seq:
            vals = getattr(item, "feature_values", None)
            if vals is None and isinstance(item, dict):
                vals = item.get("feature_values", [])
            if isinstance(vals, list) and len(vals) > 0:
                rows.append(vals)
        if len(rows) == 0:
            return []

        x = np.asarray(rows, dtype=np.float64)
        n_feat = min(x.shape[1], len(feature_names))
        if n_feat <= 0:
            return []

        x = x[:, :n_feat]
        names = feature_names[:n_feat]
        mu = x.mean(axis=0)
        sigma = x.std(axis=0) + 1e-6
        level = np.abs(x[-1] - mu) / sigma
        trend = np.abs(x[-1] - x[0]) / sigma
        vol = x.std(axis=0)

        pred_peak = float(np.max(preds)) if preds.size > 0 else 0.0
        exceed_pressure = max(0.0, pred_peak - 80.0) / 80.0
        slope = float(np.mean(np.abs(np.diff(preds)))) if preds.size > 1 else 0.0
        base = max(1.0, float(np.mean(np.abs(preds))) if preds.size > 0 else 1.0)
        pressure = 1.0 + 0.35 * exceed_pressure + 0.15 * (slope / base)

        raw = (0.50 * level + 0.30 * trend + 0.20 * vol) * pressure
        raw = np.clip(raw, 0.0, None)
        top_k = min(12, n_feat)
        top_idx = np.argsort(raw)[-top_k:]
        top_scores = raw[top_idx]
        s = float(top_scores.sum())
        if s <= 1e-8:
            return []

        ratios = top_scores / s
        out = []
        for idx, ratio in sorted(zip(top_idx, ratios), key=lambda t: t[1], reverse=True):
            name = names[int(idx)]
            out.append(
                {
                    "feature": name,
                    "group": group_map.get(name, "其它"),
                    "ratio": float(ratio),
                    "contribution": float(total_increment * ratio),
                }
            )
        return out

    @staticmethod
    def _group_aggregate(feature_rows: Sequence[dict[str, Any]]) -> list[dict[str, float | str]]:
        group_sum: dict[str, float] = {}
        for row in feature_rows:
            group = str(row.get("group", "其它"))
            group_sum[group] = group_sum.get(group, 0.0) + float(row.get("contribution", 0.0))
        return [{"group": k, "contribution": float(v)} for k, v in group_sum.items()]

    def _warmup_predict(self, frame: pd.DataFrame) -> np.ndarray:
        target = frame.get("rto_out_conc", pd.Series([0.0] * len(frame))).astype(float).to_numpy()
        if target.size == 0:
            return np.zeros((self.config.pred_len,), dtype=np.float32)
        avg = float(np.mean(target[-min(len(target), 24) :]))
        trend = float((target[-1] - target[max(0, len(target) - 5)]) / max(1, min(5, len(target) - 1))) if len(target) > 1 else 0.0
        pred = [max(0.0, min(500.0, avg + trend * (i / 4.0))) for i in range(self.config.pred_len)]
        return np.asarray(pred, dtype=np.float32)

    def predict(self, data_sequence: Sequence[Any]):
        frame = self._records_to_frame(data_sequence)

        preds: np.ndarray
        if self._loaded and self._pipeline is not None and self._model is not None:
            try:
                import torch

                features = self._pipeline.transform_frame(frame.tail(self.config.seq_len))
                x = torch.tensor(features, dtype=torch.float32, device=self._device).unsqueeze(0)
                with torch.inference_mode():
                    pred_scaled = self._model(x).detach().cpu().numpy()[0]
                pred_inv = self._pipeline.target_scaler.inverse_transform(pred_scaled.reshape(-1, 1)).reshape(-1)
                preds = np.clip(pred_inv, 0.0, 500.0).astype(np.float32)
            except Exception:
                preds = self._warmup_predict(frame)
        else:
            preds = self._warmup_predict(frame)

        baseline = float(self.config.baseline_value)
        target = float(np.mean(preds))
        total_increment = float(target - baseline)
        feature_rows = self._dynamic_feature_contributions(data_sequence, total_increment, preds)
        group_rows = self._group_aggregate(feature_rows)

        attribution = {
            "baseline": baseline,
            "target": target,
            "total_increment": total_increment,
            "feature_contributions": feature_rows,
            "group_contributions": group_rows,
            "heatmap": {"time_steps": [], "feature_groups": [], "contribution_matrix": []},
        }
        return preds, attribution
