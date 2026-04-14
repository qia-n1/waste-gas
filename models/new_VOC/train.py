from __future__ import annotations

import argparse
import json
from contextlib import nullcontext
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from tqdm.auto import tqdm

from src.config import DataConfig, ModelConfig, TrainConfig
from src.features import VOCSFeaturePipeline
from src.model import VocsMambaForecaster, count_parameters
from src.predictor import resolve_device
from src.visualization import plot_training_history


try:
    torch.set_float32_matmul_precision("high")
except (AttributeError, RuntimeError):
    pass


def build_loader(
    X: np.ndarray,
    y: np.ndarray,
    batch_size: int,
    shuffle: bool,
    num_workers: int,
    device: torch.device,
) -> DataLoader:
    dataset = TensorDataset(torch.from_numpy(X), torch.from_numpy(y))
    loader_kwargs = {
        "batch_size": batch_size,
        "shuffle": shuffle,
        "num_workers": num_workers,
        "pin_memory": device.type == "cuda",
    }
    if num_workers > 0:
        loader_kwargs["persistent_workers"] = True
        loader_kwargs["prefetch_factor"] = 4
    return DataLoader(dataset, **loader_kwargs)


def autocast_context(device: torch.device, use_amp: bool):
    if use_amp and device.type == "cuda":
        return torch.amp.autocast(device_type="cuda")
    return nullcontext()


def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    use_amp: bool,
    desc: str | None = None,
) -> tuple[float, float]:
    model.eval()
    total_loss = 0.0
    total_mae = 0.0
    batches = 0
    with torch.inference_mode():
        iterator = loader
        if desc is not None:
            iterator = tqdm(loader, desc=desc, leave=False, unit="batch")
        for features, targets in iterator:
            features = features.to(device, non_blocking=device.type == "cuda")
            targets = targets.to(device, non_blocking=device.type == "cuda")
            with autocast_context(device, use_amp):
                predictions = model(features)
                loss = criterion(predictions, targets)
                mae = torch.mean(torch.abs(predictions - targets))
            total_loss += float(loss.item())
            total_mae += float(mae.item())
            batches += 1
            if desc is not None:
                iterator.set_postfix(loss=f"{loss.item():.4f}", mae=f"{mae.item():.4f}")
    return total_loss / max(1, batches), total_mae / max(1, batches)


def main():
    parser = argparse.ArgumentParser(description="Train new_VOC with VOCS-compatible features.")
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--device", type=str, default=None)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--d-model", type=int, default=768)
    parser.add_argument("--n-layer", type=int, default=16)
    parser.add_argument("--d-state", type=int, default=128)
    parser.add_argument("--expand", type=int, default=2)
    parser.add_argument("--headdim", type=int, default=64)
    parser.add_argument("--dropout", type=float, default=0.10)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--disable-amp", action="store_true")
    args = parser.parse_args()

    data_config = DataConfig()
    if args.dataset:
        data_config.dataset_csv = Path(args.dataset)
    train_config = TrainConfig(epochs=args.epochs, batch_size=args.batch_size)
    if args.output_dir:
        train_config.output_dir = Path(args.output_dir)

    model_config = ModelConfig(
        d_model=args.d_model,
        n_layer=args.n_layer,
        d_state=args.d_state,
        expand=args.expand,
        headdim=args.headdim,
        dropout=args.dropout,
    )

    device = resolve_device(args.device)
    torch.manual_seed(train_config.seed)
    np.random.seed(train_config.seed)

    output_dir = Path(train_config.output_dir)
    model_dir = output_dir / "models"
    log_dir = output_dir / "logs"
    model_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    data_config.scaler_path = model_dir / "new_VOC_scalers.pkl"
    data_config.checkpoint_path = model_dir / "new_VOC_best.pt"

    df = pd.read_csv(data_config.dataset_csv)
    pipeline = VOCSFeaturePipeline(data_config)
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = pipeline.create_temporal_datasets(df)

    if len(X_train) == 0 or len(X_val) == 0 or len(X_test) == 0:
        raise ValueError(
            "Temporal split produced an empty train/val/test set. "
            "Increase dataset length or adjust seq_len/pred_len/split ratios."
        )

    train_loader = build_loader(
        X_train,
        y_train,
        train_config.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        device=device,
    )
    val_loader = build_loader(
        X_val,
        y_val,
        train_config.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        device=device,
    )
    test_loader = build_loader(
        X_test,
        y_test,
        train_config.batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        device=device,
    )

    model = VocsMambaForecaster(
        input_dim=pipeline.input_dim or X_train.shape[-1],
        config=model_config,
        pred_len=data_config.pred_len,
    ).to(device)
    parameter_count = count_parameters(model)

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=train_config.learning_rate,
        weight_decay=train_config.weight_decay,
    )
    criterion = nn.SmoothL1Loss()
    use_amp = device.type == "cuda" and not args.disable_amp
    scaler = torch.amp.GradScaler(device="cuda", enabled=use_amp)

    best_val_loss = float("inf")
    patience = 0
    history = []

    for epoch in range(1, train_config.epochs + 1):
        model.train()
        train_losses = []
        train_iterator = tqdm(
            train_loader,
            desc=f"Epoch {epoch}/{train_config.epochs} [train]",
            leave=False,
            unit="batch",
        )
        for features, targets in train_iterator:
            features = features.to(device, non_blocking=device.type == "cuda")
            targets = targets.to(device, non_blocking=device.type == "cuda")
            optimizer.zero_grad(set_to_none=True)
            with autocast_context(device, use_amp):
                predictions = model(features)
                loss = criterion(predictions, targets)
            if scaler.is_enabled():
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(model.parameters(), train_config.grad_clip)
                scaler.step(optimizer)
                scaler.update()
            else:
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), train_config.grad_clip)
                optimizer.step()
            train_losses.append(float(loss.item()))
            train_iterator.set_postfix(loss=f"{loss.item():.4f}")

        val_loss, val_mae = evaluate(
            model,
            val_loader,
            criterion,
            device,
            use_amp=use_amp,
            desc=f"Epoch {epoch}/{train_config.epochs} [val]",
        )
        train_loss = float(np.mean(train_losses)) if train_losses else 0.0
        history.append(
            {
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "val_mae": val_mae,
            }
        )
        print(
            f"epoch={epoch:03d} train_loss={train_loss:.6f} "
            f"val_loss={val_loss:.6f} val_mae={val_mae:.6f}"
        )

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience = 0
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "model_config": asdict(model_config),
                    "data_config": asdict(data_config),
                    "input_dim": pipeline.input_dim,
                    "best_val_loss": best_val_loss,
                    "parameter_count": parameter_count,
                },
                data_config.checkpoint_path,
            )
        else:
            patience += 1
            if patience >= train_config.early_stop_patience:
                print(f"Early stopping at epoch {epoch}")
                break

    pipeline.save(data_config.scaler_path)
    checkpoint = torch.load(data_config.checkpoint_path, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    test_loss, test_mae = evaluate(
        model.to(device),
        test_loader,
        criterion,
        device,
        use_amp=use_amp,
        desc="Test evaluation",
    )

    summary = {
        "dataset": str(data_config.dataset_csv),
        "checkpoint": str(data_config.checkpoint_path),
        "scaler": str(data_config.scaler_path),
        "parameter_count": parameter_count,
        "best_val_loss": best_val_loss,
        "test_loss": test_loss,
        "test_mae": test_mae,
    }
    with open(log_dir / "train_summary.json", "w", encoding="utf-8") as handle:
        json.dump({"summary": summary, "history": history}, handle, ensure_ascii=False, indent=2)
    plot_training_history(history, log_dir / "train_curves.png")

    print(f"parameter_count={parameter_count:,}")
    print(f"best_val_loss={best_val_loss:.6f} test_loss={test_loss:.6f} test_mae={test_mae:.6f}")
    print(f"artifacts={output_dir}")


if __name__ == "__main__":
    main()
