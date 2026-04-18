from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from IPython.display import clear_output, display


def render_live_preview(
    *,
    epoch: int,
    batch_idx: int,
    y_true_scaled,
    y_pred_scaled,
    pred_len: int,
    target_scaler,
    preview_dir: Path,
) -> Path:
    """Render one forecast preview in notebook and save a PNG copy."""
    y_true_np = y_true_scaled.detach().cpu().numpy().reshape(-1, pred_len)
    y_pred_np = y_pred_scaled.detach().cpu().numpy().reshape(-1, pred_len)

    y_true_inv = target_scaler.inverse_transform(y_true_np.reshape(-1, 1)).reshape(-1, pred_len)
    y_pred_inv = target_scaler.inverse_transform(y_pred_np.reshape(-1, 1)).reshape(-1, pred_len)

    fig, ax = plt.subplots(figsize=(8, 4))
    horizon = np.arange(1, pred_len + 1)
    ax.plot(horizon, y_true_inv[0], label="target", linewidth=2)
    ax.plot(horizon, y_pred_inv[0], label="prediction", linewidth=2)
    ax.set_title(f"Epoch {epoch} | batch={batch_idx}")
    ax.set_xlabel("Horizon step")
    ax.set_ylabel("rto_out_conc")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()

    preview_dir.mkdir(parents=True, exist_ok=True)
    save_path = preview_dir / f"epoch_{epoch:03d}_batch_{batch_idx:05d}.png"
    fig.savefig(save_path, dpi=140)

    clear_output(wait=True)
    display(fig)
    plt.close(fig)
    return save_path
