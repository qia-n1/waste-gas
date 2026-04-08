from __future__ import annotations

from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt


def plot_training_history(history: list[dict], save_path: str | Path | None = None):
    if not history:
        return None
    epochs = [item["epoch"] for item in history]
    train_loss = [item["train_loss"] for item in history]
    val_loss = [item["val_loss"] for item in history]
    val_mae = [item["val_mae"] for item in history]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(epochs, train_loss, label="train_loss")
    axes[0].plot(epochs, val_loss, label="val_loss")
    axes[0].set_title("Loss")
    axes[0].set_xlabel("Epoch")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(epochs, val_mae, label="val_mae", color="tab:orange")
    axes[1].set_title("Validation MAE")
    axes[1].set_xlabel("Epoch")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    fig.tight_layout()
    if save_path is not None:
        output = Path(save_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=160, bbox_inches="tight")
    return fig


def plot_prediction_window(
    history_values: Iterable[float],
    future_values: Iterable[float] | None,
    predicted_values: Iterable[float],
    save_path: str | Path | None = None,
    title: str = "new_VOC Forecast",
):
    history_values = list(history_values)
    predicted_values = list(predicted_values)
    future_values = list(future_values) if future_values is not None else None

    fig, ax = plt.subplots(figsize=(12, 4))
    history_x = list(range(len(history_values)))
    pred_x = list(range(len(history_values), len(history_values) + len(predicted_values)))

    ax.plot(history_x, history_values, label="history", color="tab:blue")
    ax.plot(pred_x, predicted_values, label="prediction", color="tab:red")
    if future_values is not None:
        ax.plot(pred_x, future_values, label="future_target", color="tab:green", linestyle="--")

    ax.set_title(title)
    ax.set_xlabel("Step")
    ax.set_ylabel("rto_out_conc")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()

    if save_path is not None:
        output = Path(save_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output, dpi=160, bbox_inches="tight")
    return fig
