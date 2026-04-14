from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from torch.utils.data import DataLoader, TensorDataset
from numpy.lib.stride_tricks import sliding_window_view

from src.config import DataConfig, ModelConfig
from src.features import VOCSFeaturePipeline
from src.model import VocsMambaForecaster
from src.predictor import resolve_device


PROJECT_ROOT = Path(__file__).resolve().parent
VOCS_ROOT = PROJECT_ROOT.parent / "VOCS"
VOCS_SRC_ROOT = VOCS_ROOT / "src"

if str(VOCS_SRC_ROOT) not in sys.path:
    sys.path.append(str(VOCS_SRC_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare new_VOC against the existing VOCS LSTM baseline on a shared temporal split."
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        default=VOCS_ROOT / "src" / "data" / "vocs_dataset.csv",
        help="Shared dataset CSV.",
    )
    parser.add_argument(
        "--mamba-checkpoint",
        type=Path,
        default=PROJECT_ROOT / "artifacts_notebook" / "models" / "new_VOC_best.pt",
        help="new_VOC checkpoint path.",
    )
    parser.add_argument(
        "--mamba-scaler",
        type=Path,
        default=PROJECT_ROOT / "artifacts_notebook" / "models" / "new_VOC_scalers.pkl",
        help="new_VOC scaler path.",
    )
    parser.add_argument(
        "--baseline-checkpoint",
        type=Path,
        default=VOCS_ROOT / "src" / "outputs" / "20260203_105917" / "models" / "vocs_seq2seq_v2_best.pth",
        help="Existing VOCS LSTM checkpoint path.",
    )
    parser.add_argument(
        "--baseline-scaler",
        type=Path,
        default=VOCS_ROOT / "src" / "outputs" / "20260203_105917" / "models" / "vocs_scalers_v2.pkl",
        help="Existing VOCS scaler path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "artifacts_notebook" / "logs" / "baseline_comparison.json",
        help="Where to save the comparison JSON.",
    )
    parser.add_argument("--device", type=str, default=None)
    return parser.parse_args()


def temporal_split_with_context(df: pd.DataFrame, config: DataConfig) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    data = df.reset_index(drop=True)
    train_end = int(len(data) * config.train_ratio)
    val_end = int(len(data) * (config.train_ratio + config.val_ratio))
    train_df = data.iloc[:train_end].copy()
    val_df = data.iloc[max(0, train_end - config.seq_len) : val_end].copy()
    test_df = data.iloc[max(0, val_end - config.seq_len) :].copy()
    return train_df, val_df, test_df


def build_split_metadata(df: pd.DataFrame, config: DataConfig) -> dict:
    train_df, val_df, test_df = temporal_split_with_context(df, config)
    raw_train_end = int(len(df) * config.train_ratio)
    raw_val_end = int(len(df) * (config.train_ratio + config.val_ratio))
    meta = {
        "n_total": int(len(df)),
        "train_rows": int(len(train_df)),
        "val_rows_with_context": int(len(val_df)),
        "test_rows_with_context": int(len(test_df)),
        "raw_train_end": raw_train_end,
        "raw_val_end": raw_val_end,
        "context_len": int(config.seq_len),
    }

    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], errors="coerce")
        meta["timestamp"] = {
            "null_count": int(ts.isna().sum()),
            "is_monotonic_non_decreasing": bool(ts.dropna().is_monotonic_increasing),
            "train_start": str(train_df["timestamp"].iloc[0]) if len(train_df) > 0 else None,
            "train_end": str(train_df["timestamp"].iloc[-1]) if len(train_df) > 0 else None,
            "val_start": str(val_df["timestamp"].iloc[0]) if len(val_df) > 0 else None,
            "val_end": str(val_df["timestamp"].iloc[-1]) if len(val_df) > 0 else None,
            "test_start": str(test_df["timestamp"].iloc[0]) if len(test_df) > 0 else None,
            "test_end": str(test_df["timestamp"].iloc[-1]) if len(test_df) > 0 else None,
        }
    return meta


def _safe_metrics_1d(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    if y_true.size == 0:
        return {"count": 0, "r2": float("nan"), "mae": float("nan"), "rmse": float("nan")}
    return {
        "count": int(y_true.size),
        "r2": float(r2_score(y_true, y_pred)) if y_true.size >= 2 else float("nan"),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def _build_regime_metrics(targets_orig: np.ndarray, preds_orig: np.ndarray, exceed_threshold: float) -> dict:
    target_trend = targets_orig[:, -1, 0] - targets_orig[:, 0, 0]
    abs_trend = np.abs(target_trend)
    fast_rise_threshold = float(np.quantile(target_trend, 0.75))
    high_vol_threshold = float(np.quantile(abs_trend, 0.75))

    masks = {
        "all": np.ones(targets_orig.shape[0], dtype=bool),
        "exceed_any": (targets_orig[:, :, 0] > exceed_threshold).any(axis=1),
        "fast_rise": target_trend > fast_rise_threshold,
        "high_volatility": abs_trend > high_vol_threshold,
    }

    out = {
        "thresholds": {
            "exceed_threshold": float(exceed_threshold),
            "fast_rise_q75": fast_rise_threshold,
            "high_volatility_abs_trend_q75": high_vol_threshold,
        },
        "buckets": {},
    }
    for bucket_name, mask in masks.items():
        y_true = targets_orig[mask, :, 0].reshape(-1)
        y_pred = preds_orig[mask, :, 0].reshape(-1)
        out["buckets"][bucket_name] = _safe_metrics_1d(y_true, y_pred)
        out["buckets"][bucket_name]["sequence_count"] = int(mask.sum())
    return out


def build_metrics_from_scaled(
    preds_scaled: np.ndarray,
    targets_scaled: np.ndarray,
    target_scaler,
    exceed_threshold: float,
) -> dict:
    metrics = []
    pred_len = targets_scaled.shape[1]
    for step_idx in range(pred_len):
        pred_t = preds_scaled[:, step_idx, 0]
        target_t = targets_scaled[:, step_idx, 0]
        metrics.append(
            {
                "step": step_idx + 1,
                "time": f"+{(step_idx + 1) * 15}min",
                "r2": float(r2_score(target_t, pred_t)),
                "mae": float(mean_absolute_error(target_t, pred_t)),
                "rmse": float(np.sqrt(mean_squared_error(target_t, pred_t))),
            }
        )

    metrics_df = pd.DataFrame(metrics)
    targets_orig = target_scaler.inverse_transform(targets_scaled.reshape(-1, 1)).reshape(targets_scaled.shape)
    preds_orig = target_scaler.inverse_transform(preds_scaled.reshape(-1, 1)).reshape(preds_scaled.shape)
    target_trend = targets_scaled[:, -1, 0] - targets_scaled[:, 0, 0]
    pred_trend = preds_scaled[:, -1, 0] - preds_scaled[:, 0, 0]

    summary = {
        "avg_r2": float(metrics_df["r2"].mean()),
        "avg_mae": float(metrics_df["mae"].mean()),
        "avg_rmse": float(metrics_df["rmse"].mean()),
        "trend_accuracy": float(((target_trend > 0).astype(int) == (pred_trend > 0).astype(int)).mean()),
        "exceed_accuracy": float(
            (
                (targets_orig > exceed_threshold).astype(int)
                == (preds_orig > exceed_threshold).astype(int)
            ).mean()
        ),
        "short_r2": float(metrics_df.iloc[:8]["r2"].mean()),
        "medium_r2": float(metrics_df.iloc[8:16]["r2"].mean()),
        "long_r2": float(metrics_df.iloc[16:]["r2"].mean()),
    }
    horizon_breakdown = {
        "short": _safe_metrics_1d(targets_scaled[:, :8, 0].reshape(-1), preds_scaled[:, :8, 0].reshape(-1)),
        "medium": _safe_metrics_1d(targets_scaled[:, 8:16, 0].reshape(-1), preds_scaled[:, 8:16, 0].reshape(-1)),
        "long": _safe_metrics_1d(targets_scaled[:, 16:, 0].reshape(-1), preds_scaled[:, 16:, 0].reshape(-1)),
    }
    regime_metrics = _build_regime_metrics(
        targets_orig=targets_orig,
        preds_orig=preds_orig,
        exceed_threshold=exceed_threshold,
    )
    return {
        "summary": summary,
        "step_metrics": metrics,
        "horizon_breakdown_scaled": horizon_breakdown,
        "regime_metrics_original": regime_metrics,
    }


def evaluate_mamba(
    dataset_df: pd.DataFrame,
    data_config: DataConfig,
    checkpoint_path: Path,
    scaler_path: Path,
    device: torch.device,
) -> dict:
    _, _, test_df = temporal_split_with_context(dataset_df, data_config)
    pipeline = VOCSFeaturePipeline.load(scaler_path, data_config)
    X_test, y_test = pipeline.create_sequences(test_df, fit=False, augment=False)

    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model_config = ModelConfig(**checkpoint["model_config"])
    model = VocsMambaForecaster(
        input_dim=checkpoint.get("input_dim") or pipeline.input_dim,
        config=model_config,
        pred_len=data_config.pred_len,
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    loader = DataLoader(
        TensorDataset(torch.from_numpy(X_test), torch.from_numpy(y_test)),
        batch_size=64,
        shuffle=False,
        num_workers=0,
    )

    preds_scaled = []
    targets_scaled = []
    with torch.inference_mode():
        for xb, yb in loader:
            pred = model(xb.to(device)).cpu().numpy()
            preds_scaled.append(pred)
            targets_scaled.append(yb.numpy())

    preds_scaled = np.concatenate(preds_scaled, axis=0)
    targets_scaled = np.concatenate(targets_scaled, axis=0)
    result = build_metrics_from_scaled(
        preds_scaled,
        targets_scaled,
        pipeline.target_scaler,
        exceed_threshold=data_config.exceed_threshold,
    )
    result["metadata"] = {
        "checkpoint": str(checkpoint_path),
        "scaler": str(scaler_path),
        "test_sequence_count": int(len(X_test)),
        "note": "new_VOC was trained with the leak-fixed temporal split.",
    }
    return result


def build_lstm_feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    def rolling_linear_trend(values: np.ndarray, window: int) -> np.ndarray:
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

    data = df.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], errors="coerce")
    data["hour_sin"] = np.sin(2 * np.pi * data["timestamp"].dt.hour / 24)
    data["hour_cos"] = np.cos(2 * np.pi * data["timestamp"].dt.hour / 24)
    data["weekday_sin"] = np.sin(2 * np.pi * data["timestamp"].dt.weekday / 7)
    data["weekday_cos"] = np.cos(2 * np.pi * data["timestamp"].dt.weekday / 7)
    data["month_sin"] = np.sin(2 * np.pi * data["timestamp"].dt.month / 12)
    data["month_cos"] = np.cos(2 * np.pi * data["timestamp"].dt.month / 12)

    target_col = "rto_out_conc"
    target_series = data[target_col]
    target_values = target_series.to_numpy(copy=False)
    for window in (6, 12, 24, 48, 96):
        data[f"{target_col}_rolling_mean_{window}"] = target_series.rolling(window=window, min_periods=1).mean()
        data[f"{target_col}_rolling_std_{window}"] = target_series.rolling(window=window, min_periods=1).std().fillna(0.0)
        data[f"{target_col}_rolling_trend_{window}"] = rolling_linear_trend(target_values, window)
    data[f"{target_col}_diff_1"] = target_series.diff(1).fillna(0.0)
    data[f"{target_col}_diff_4"] = target_series.diff(4).fillna(0.0)
    data[f"{target_col}_diff_24"] = target_series.diff(24).fillna(0.0)
    data[f"{target_col}_diff_96"] = target_series.diff(96).fillna(0.0)
    data[f"{target_col}_ma_diff_24"] = target_series - data[f"{target_col}_rolling_mean_24"]
    return data


def create_lstm_sequences(
    df: pd.DataFrame,
    feature_scaler,
    target_scaler,
    feature_columns: list[str],
    seq_len: int,
    pred_len: int,
) -> tuple[np.ndarray, np.ndarray]:
    feature_df = build_lstm_feature_frame(df)
    X = feature_df[feature_columns].values
    y = feature_df[["rto_out_conc"]].values
    X_scaled = feature_scaler.transform(X)
    y_scaled = target_scaler.transform(y)

    inputs = []
    targets = []
    total_len = len(X_scaled)
    for idx in range(total_len - seq_len - pred_len + 1):
        x_seq = X_scaled[idx : idx + seq_len]
        hist_target = y_scaled[idx : idx + seq_len]
        y_seq = y_scaled[idx + seq_len : idx + seq_len + pred_len]
        inputs.append(np.concatenate([x_seq, hist_target], axis=1))
        targets.append(y_seq)

    return np.asarray(inputs, dtype=np.float32), np.asarray(targets, dtype=np.float32)


def evaluate_baseline_lstm(
    dataset_df: pd.DataFrame,
    data_config: DataConfig,
    checkpoint_path: Path,
    scaler_path: Path,
    device: torch.device,
) -> dict:
    _, _, test_df = temporal_split_with_context(dataset_df, data_config)

    with open(scaler_path, "rb") as handle:
        scaler_payload = pickle.load(handle)
    feature_scaler = scaler_payload["feature_scaler"]
    target_scaler = scaler_payload["target_scaler"]
    feature_columns = scaler_payload["feature_columns"]

    X_test, y_test = create_lstm_sequences(
        test_df,
        feature_scaler,
        target_scaler,
        feature_columns,
        seq_len=data_config.seq_len,
        pred_len=data_config.pred_len,
    )

    from vocs_model import Config as LSTMConfig
    from vocs_model import ImprovedSeq2SeqModel

    baseline_config = LSTMConfig()
    model = ImprovedSeq2SeqModel(baseline_config, X_test.shape[-1]).to(device)
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    loader = DataLoader(
        TensorDataset(torch.from_numpy(X_test), torch.from_numpy(y_test)),
        batch_size=64,
        shuffle=False,
        num_workers=0,
    )

    preds_scaled = []
    targets_scaled = []
    with torch.inference_mode():
        for xb, yb in loader:
            pred = model(xb.to(device)).cpu().numpy()
            preds_scaled.append(pred)
            targets_scaled.append(yb.numpy())

    preds_scaled = np.concatenate(preds_scaled, axis=0)
    targets_scaled = np.concatenate(targets_scaled, axis=0)
    result = build_metrics_from_scaled(
        preds_scaled,
        targets_scaled,
        target_scaler,
        exceed_threshold=data_config.exceed_threshold,
    )
    result["metadata"] = {
        "checkpoint": str(checkpoint_path),
        "scaler": str(scaler_path),
        "test_sequence_count": int(len(X_test)),
        "note": (
            "Baseline weights and saved scaler come from the original VOCS training flow, "
            "so training-time leakage may still make this baseline optimistic."
        ),
    }
    return result


def print_comparison(mamba_result: dict, baseline_result: dict) -> None:
    keys = [
        "avg_r2",
        "avg_mae",
        "avg_rmse",
        "trend_accuracy",
        "exceed_accuracy",
        "short_r2",
        "medium_r2",
        "long_r2",
    ]
    print("\nShared-split comparison")
    print("-" * 72)
    print(f"{'metric':<18} {'baseline_lstm':>16} {'mamba':>16} {'delta(m-b)':>16}")
    print("-" * 72)
    for key in keys:
        baseline_value = baseline_result["summary"][key]
        mamba_value = mamba_result["summary"][key]
        delta = mamba_value - baseline_value
        print(f"{key:<18} {baseline_value:>16.6f} {mamba_value:>16.6f} {delta:>16.6f}")


def main() -> None:
    args = parse_args()
    device = resolve_device(args.device)
    dataset_df = pd.read_csv(args.dataset)
    data_config = DataConfig(dataset_csv=args.dataset)

    mamba_result = evaluate_mamba(
        dataset_df=dataset_df,
        data_config=data_config,
        checkpoint_path=args.mamba_checkpoint,
        scaler_path=args.mamba_scaler,
        device=device,
    )
    baseline_result = evaluate_baseline_lstm(
        dataset_df=dataset_df,
        data_config=data_config,
        checkpoint_path=args.baseline_checkpoint,
        scaler_path=args.baseline_scaler,
        device=device,
    )

    comparison = {
        "dataset": str(args.dataset),
        "device": str(device),
        "split_metadata": build_split_metadata(dataset_df, data_config),
        "baseline_lstm": baseline_result,
        "mamba": mamba_result,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(comparison, handle, ensure_ascii=False, indent=2)

    print_comparison(mamba_result, baseline_result)
    print(f"\nSaved comparison JSON to {args.output}")


if __name__ == "__main__":
    main()
