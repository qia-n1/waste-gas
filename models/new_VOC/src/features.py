from __future__ import annotations

import pickle
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view
from sklearn.preprocessing import MinMaxScaler

from .config import DataConfig, ROLLING_WINDOWS, SENSOR_COLUMNS, TARGET_COLUMN
from .schemas import SensorData


class VOCSFeaturePipeline:
    def __init__(self, config: DataConfig):
        self.config = config
        self.feature_scaler = MinMaxScaler()
        self.target_scaler = MinMaxScaler()
        self.feature_columns: list[str] = []
        self.input_dim: int | None = None

    def sensor_records_to_frame(self, records: Sequence[SensorData]) -> pd.DataFrame:
        return pd.DataFrame.from_records(record.model_dump() for record in records)

    @staticmethod
    def _rolling_linear_trend(values: np.ndarray, window: int) -> np.ndarray:
        result = np.zeros(values.shape[0], dtype=np.float32)
        if window < 2 or values.shape[0] < window:
            return result

        x = np.arange(window, dtype=np.float64)
        windows = sliding_window_view(values.astype(np.float64, copy=False), window_shape=window)
        sum_x = float(x.sum())
        denom = float(window * np.square(x).sum() - sum_x * sum_x)
        if denom == 0.0:
            return result

        sum_y = windows.sum(axis=1)
        sum_xy = windows @ x
        slopes = (window * sum_xy - sum_x * sum_y) / denom
        result[window - 1 :] = slopes.astype(np.float32, copy=False)
        return result

    def _ensure_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df.copy()
        for column in SENSOR_COLUMNS:
            if column not in data.columns:
                data[column] = 0.0 if column != "timestamp" else pd.Timestamp.now().isoformat()
        return data[SENSOR_COLUMNS]

    def add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df
        data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
        data["hour_sin"] = np.sin(2 * np.pi * data["timestamp"].dt.hour / 24)
        data["hour_cos"] = np.cos(2 * np.pi * data["timestamp"].dt.hour / 24)
        data["weekday_sin"] = np.sin(2 * np.pi * data["timestamp"].dt.weekday / 7)
        data["weekday_cos"] = np.cos(2 * np.pi * data["timestamp"].dt.weekday / 7)
        data["month_sin"] = np.sin(2 * np.pi * data["timestamp"].dt.month / 12)
        data["month_cos"] = np.cos(2 * np.pi * data["timestamp"].dt.month / 12)
        return data

    def add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        data = df
        target_series = data[TARGET_COLUMN].astype(np.float64, copy=False)
        target_values = target_series.to_numpy(copy=False)

        for window in ROLLING_WINDOWS:
            data[f"{TARGET_COLUMN}_rolling_mean_{window}"] = (
                target_series.rolling(window=window, min_periods=1).mean()
            )
            data[f"{TARGET_COLUMN}_rolling_std_{window}"] = (
                target_series.rolling(window=window, min_periods=1).std().fillna(0.0)
            )
            data[f"{TARGET_COLUMN}_rolling_trend_{window}"] = self._rolling_linear_trend(
                target_values,
                window,
            )
        data[f"{TARGET_COLUMN}_diff_1"] = target_series.diff(1).fillna(0.0)
        data[f"{TARGET_COLUMN}_diff_4"] = target_series.diff(4).fillna(0.0)
        data[f"{TARGET_COLUMN}_diff_24"] = target_series.diff(24).fillna(0.0)
        data[f"{TARGET_COLUMN}_diff_96"] = target_series.diff(96).fillna(0.0)
        data[f"{TARGET_COLUMN}_ma_diff_24"] = (
            target_series - data[f"{TARGET_COLUMN}_rolling_mean_24"]
        )
        return data

    def build_feature_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        data = self._ensure_columns(df)
        data = self.add_time_features(data)
        data = self.add_rolling_features(data)
        return data

    def augment_exceed_samples(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.config.exceed_sample_weight <= 1.0:
            return df
        exceed_mask = df[TARGET_COLUMN] > self.config.exceed_threshold
        exceed_samples = df[exceed_mask].copy()
        if exceed_samples.empty:
            return df
        noise = np.random.normal(0.0, 1.0, size=len(exceed_samples))
        exceed_samples[TARGET_COLUMN] = exceed_samples[TARGET_COLUMN] + noise
        return pd.concat([df, exceed_samples], ignore_index=True)

    def fit(self, df: pd.DataFrame) -> pd.DataFrame:
        feature_df = self.build_feature_frame(df)
        exclude_cols = ["timestamp", TARGET_COLUMN]
        self.feature_columns = [col for col in feature_df.columns if col not in exclude_cols]
        X = feature_df[self.feature_columns].values
        y = feature_df[[TARGET_COLUMN]].values
        self.feature_scaler.fit(X)
        self.target_scaler.fit(y)
        self.input_dim = len(self.feature_columns) + 1
        return feature_df

    def transform_frame(self, df: pd.DataFrame) -> np.ndarray:
        if not self.feature_columns:
            raise RuntimeError("Feature pipeline is not fitted. Call fit() or load() first.")
        feature_df = self.build_feature_frame(df)
        X = feature_df[self.feature_columns].values
        y = feature_df[[TARGET_COLUMN]].values
        X_scaled = self.feature_scaler.transform(X)
        y_scaled = self.target_scaler.transform(y)
        return np.concatenate([X_scaled, y_scaled], axis=1).astype(np.float32)

    def create_sequences(
        self,
        df: pd.DataFrame,
        fit: bool = False,
        augment: bool = True,
    ) -> tuple[np.ndarray, np.ndarray]:
        working_df = self.augment_exceed_samples(df) if augment else df
        if fit or not self.feature_columns:
            self.fit(working_df)
        feature_df = self.build_feature_frame(working_df)
        X_scaled = self.feature_scaler.transform(feature_df[self.feature_columns].values)
        y_scaled = self.target_scaler.transform(feature_df[[TARGET_COLUMN]].values)
        X_with_hist = np.concatenate([X_scaled, y_scaled], axis=1).astype(np.float32)

        total_len = len(X_with_hist)
        num_samples = total_len - self.config.seq_len - self.config.pred_len + 1
        if num_samples <= 0:
            empty_x = np.empty((0, self.config.seq_len, X_with_hist.shape[1]), dtype=np.float32)
            empty_y = np.empty((0, self.config.pred_len, 1), dtype=np.float32)
            return empty_x, empty_y

        feature_windows = sliding_window_view(
            X_with_hist,
            window_shape=self.config.seq_len,
            axis=0,
        )
        feature_windows = np.swapaxes(feature_windows[:num_samples], 1, 2)

        target_windows = sliding_window_view(
            y_scaled,
            window_shape=self.config.pred_len,
            axis=0,
        )
        target_windows = np.swapaxes(target_windows, 1, 2)
        target_windows = target_windows[self.config.seq_len : self.config.seq_len + num_samples]

        return (
            np.ascontiguousarray(feature_windows, dtype=np.float32),
            np.ascontiguousarray(target_windows, dtype=np.float32),
        )

    def split_dataframe_by_time(
        self,
        df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        data = df.reset_index(drop=True)
        n_rows = len(data)
        train_end = int(n_rows * self.config.train_ratio)
        val_end = int(n_rows * (self.config.train_ratio + self.config.val_ratio))

        if not (0 < train_end < val_end < n_rows):
            raise ValueError(
                "Invalid temporal split. Please check dataset length and split ratios."
            )

        train_df = data.iloc[:train_end].copy()
        val_df = data.iloc[max(0, train_end - self.config.seq_len) : val_end].copy()
        test_df = data.iloc[max(0, val_end - self.config.seq_len) :].copy()
        return train_df, val_df, test_df

    def create_temporal_datasets(
        self,
        df: pd.DataFrame,
    ) -> tuple[
        tuple[np.ndarray, np.ndarray],
        tuple[np.ndarray, np.ndarray],
        tuple[np.ndarray, np.ndarray],
    ]:
        train_df, val_df, test_df = self.split_dataframe_by_time(df)

        train_fit_df = self.augment_exceed_samples(train_df)
        self.fit(train_fit_df)

        train_sequences = self.create_sequences(train_fit_df, fit=False, augment=False)
        val_sequences = self.create_sequences(val_df, fit=False, augment=False)
        test_sequences = self.create_sequences(test_df, fit=False, augment=False)
        return train_sequences, val_sequences, test_sequences

    def split_sequences(
        self, X: np.ndarray, y: np.ndarray
    ) -> tuple[tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]:
        n_samples = len(X)
        train_end = int(n_samples * self.config.train_ratio)
        val_end = int(n_samples * (self.config.train_ratio + self.config.val_ratio))
        return (
            (X[:train_end], y[:train_end]),
            (X[train_end:val_end], y[train_end:val_end]),
            (X[val_end:], y[val_end:]),
        )

    def save(self, path: Path | str) -> Path:
        if not self.feature_columns or self.input_dim is None:
            raise RuntimeError("Feature pipeline is not fitted.")
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "feature_scaler": self.feature_scaler,
            "target_scaler": self.target_scaler,
            "feature_columns": self.feature_columns,
            "input_dim": self.input_dim,
            "save_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(target, "wb") as handle:
            pickle.dump(payload, handle)
        return target

    @staticmethod
    def _load_pickle_with_numpy_compat(handle):
        try:
            return pickle.load(handle)
        except ModuleNotFoundError as exc:
            # Compatibility shim for pickles created under a different NumPy internal path layout.
            if "numpy._core.numeric" not in str(exc):
                raise
            import numpy.core.numeric as np_core_numeric

            sys.modules.setdefault("numpy._core.numeric", np_core_numeric)
            handle.seek(0)
            return pickle.load(handle)

    @classmethod
    def load(cls, path: Path | str, config: DataConfig) -> "VOCSFeaturePipeline":
        pipeline = cls(config)
        with open(path, "rb") as handle:
            payload = cls._load_pickle_with_numpy_compat(handle)
        pipeline.feature_scaler = payload["feature_scaler"]
        pipeline.target_scaler = payload["target_scaler"]
        pipeline.feature_columns = payload["feature_columns"]
        pipeline.input_dim = payload["input_dim"]
        return pipeline
