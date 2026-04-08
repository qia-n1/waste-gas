import sys
import copy
import json
import time
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
from tqdm.auto import tqdm

# Add VOCS src to path for baseline LSTM model
vocs_src_root = Path('/openbayes/home/服务外包大赛/VOCS/src')
if str(vocs_src_root) not in sys.path:
    sys.path.append(str(vocs_src_root))

from vocs_model import Config as LSTMConfig
from vocs_model import ImprovedSeq2SeqModel

from src.config import DataConfig, ModelConfig, TrainConfig
from src.features import VOCSFeaturePipeline
from src.model import DLinearForecasterLarge, DLinearMambaEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

import random
def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def evaluate_regression(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    metrics = {
        'avg_r2': float(np.mean([r2_score(y_true[:, i], y_pred[:, i]) for i in range(y_true.shape[1])])),
        'avg_mae': float(np.mean([mean_absolute_error(y_true[:, i], y_pred[:, i]) for i in range(y_true.shape[1])])),
        'avg_rmse': float(np.mean([np.sqrt(mean_squared_error(y_true[:, i], y_pred[:, i])) for i in range(y_true.shape[1])])),
    }
    pred_diff = np.diff(y_pred, axis=1)
    true_diff = np.diff(y_true, axis=1)
    metrics['trend_accuracy'] = float(np.mean(np.sign(pred_diff) == np.sign(true_diff)))
    exceed_th = 80.0
    metrics['exceed_accuracy'] = float(np.mean((y_pred > exceed_th) == (y_true > exceed_th)))
    return metrics

def train_dlinear(variant_name, x_train, y_train, x_val, y_val, x_test, y_test, device, input_dim, pred_len, seq_len, 
                  epochs=7, lr=3e-4, wd=1e-5, bsz=32, hidden_dims=(256, 128), is_mamba=False):
    model_cfg = ModelConfig(d_model=256, n_layer=1)
    if is_mamba:
        model = DLinearMambaEncoder(input_dim=input_dim, config=model_cfg, pred_len=pred_len, decomp_kernel=25, seq_len=seq_len, encoder_layers=1).to(device)
    else:
        model = DLinearForecasterLarge(input_dim=input_dim, config=model_cfg, pred_len=pred_len, decomp_kernel=35, seq_len=seq_len, hidden_dims=hidden_dims, branch_dropout=0.1).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    scaler = torch.amp.GradScaler(device="cuda", enabled=(device.type == "cuda"))
    train_loader = DataLoader(TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train)), batch_size=bsz, shuffle=True, pin_memory=True)
    val_loader = DataLoader(TensorDataset(torch.from_numpy(x_val), torch.from_numpy(y_val)), batch_size=bsz, shuffle=False)
    
    best_val = float("inf")
    best_state = None
    for epoch in range(1, epochs + 1):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device, non_blocking=True), yb.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device_type="cuda", enabled=(device.type == "cuda")):
                loss = model.loss(xb, yb)
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

        model.eval()
        val_losses = []
        with torch.inference_mode():
            for xb, yb in val_loader:
                xb, yb = xb.to(device, non_blocking=True), yb.to(device, non_blocking=True)
                with torch.amp.autocast(device_type="cuda", enabled=(device.type == "cuda")):
                    val_losses.append(model.loss(xb, yb).item())
        va_loss = np.mean(val_losses)
        
        if va_loss < best_val:
            best_val = va_loss
            best_state = copy.deepcopy(model.state_dict())
            
    model.load_state_dict(best_state)
    model.eval()
    
    test_loader = DataLoader(TensorDataset(torch.from_numpy(x_test), torch.from_numpy(y_test)), batch_size=bsz, shuffle=False)
    preds = []
    with torch.inference_mode():
        for xb, _ in test_loader:
            xb = xb.to(device)
            preds.append(model(xb).cpu().numpy())
    return np.concatenate(preds, axis=0), model

def train_lstm(variant_name, num_layers, x_train, y_train, x_val, y_val, x_test, y_test, device, input_dim, pred_len, seq_len, 
               epochs=12, bsz=64, lr=8e-4, wd=1e-5):
    cfg_lstm = LSTMConfig()
    cfg_lstm.NUM_LAYERS = num_layers
    cfg_lstm.BATCH_SIZE = bsz
    cfg_lstm.LEARNING_RATE = lr
    cfg_lstm.WEIGHT_DECAY = wd
    cfg_lstm.EPOCHS = epochs
    
    # We use x_train.shape[-1] as input_dim
    model = ImprovedSeq2SeqModel(cfg_lstm, input_dim=input_dim).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=wd)
    criterion = torch.nn.MSELoss()
    
    train_loader = DataLoader(TensorDataset(torch.from_numpy(x_train), torch.from_numpy(y_train)), batch_size=bsz, shuffle=True, num_workers=0)
    val_loader = DataLoader(TensorDataset(torch.from_numpy(x_val), torch.from_numpy(y_val)), batch_size=bsz, shuffle=False, num_workers=0)
    test_loader = DataLoader(TensorDataset(torch.from_numpy(x_test), torch.from_numpy(y_test)), batch_size=bsz, shuffle=False, num_workers=0)

    best_val = float('inf')
    best_state = None
    for epoch in range(1, epochs + 1):
        model.train()
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            pred = model(xb, target=yb, teacher_forcing_ratio=0.3)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()

        model.eval()
        val_losses = []
        with torch.inference_mode():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                pred = model(xb, target=None, teacher_forcing_ratio=0.0)
                val_losses.append(criterion(pred, yb).item())
        va_loss = np.mean(val_losses)
        if va_loss < best_val:
            best_val = va_loss
            best_state = copy.deepcopy(model.state_dict())

    model.load_state_dict(best_state)
    model.eval()
    preds = []
    with torch.inference_mode():
        for xb, _ in test_loader:
            xb = xb.to(device)
            preds.append(model(xb, target=None, teacher_forcing_ratio=0.0).cpu().numpy())
    return np.concatenate(preds, axis=0), model

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    set_seed(42)
    
    data_cfg = DataConfig(seq_len=96, pred_len=24, dataset_csv=Path('/openbayes/home/服务外包大赛/VOCS/src/data/vocs_dataset.csv'))
    # Ensure PCA is enabled
    data_cfg.pca_enabled = True 
    pipeline = VOCSFeaturePipeline(data_cfg)
    df = pd.read_csv(data_cfg.dataset_csv)
    
    print("Preparing Datasets with PCA...")
    (x_train, y_train), (x_val, y_val), (x_test, y_test) = pipeline.create_temporal_datasets(df)
    input_dim = pipeline.input_dim
    print(f"PCA Reduced Input Dim: {input_dim}")
    print(f"X_train shape: {x_train.shape}")
    
    target_scaler = pipeline.target_scaler
    true_scaled = y_test.reshape(-1, data_cfg.pred_len)
    true_inv = target_scaler.inverse_transform(true_scaled.reshape(-1, 1)).reshape(true_scaled.shape)
    true_inv = np.clip(true_inv, 0.0, 500.0)
    
    out_dir = Path("artifacts_pca_ensemble")
    out_dir.mkdir(exist_ok=True)
    
    models_to_train = [
        {"name": "pca_dlinear_large", "type": "dlinear", "kwargs": {"epochs": 7, "hidden_dims": (256, 128)}},
        {"name": "pca_dlinear_deep_large", "type": "dlinear", "kwargs": {"epochs": 7, "hidden_dims": (96, 48, 24)}},
        {"name": "pca_mamba_fusion", "type": "mamba", "kwargs": {"epochs": 3}},
        {"name": "pca_lstm_1layer", "type": "lstm", "kwargs": {"num_layers": 1, "epochs": 12}},
        {"name": "pca_lstm_2layer", "type": "lstm", "kwargs": {"num_layers": 2, "epochs": 12}},
    ]
    
    results = {}
    preds_dict = {}
    
    # Train each member
    for cfg in models_to_train:
        print(f"Training {cfg['name']}...")
        start_t = time.perf_counter()
        
        if cfg['type'] == 'dlinear':
            pred_scaled, model = train_dlinear(cfg['name'], x_train, y_train, x_val, y_val, x_test, y_test, device, 
                                               input_dim, data_cfg.pred_len, data_cfg.seq_len, **cfg['kwargs'])
        elif cfg['type'] == 'mamba':
            pred_scaled, model = train_dlinear(cfg['name'], x_train, y_train, x_val, y_val, x_test, y_test, device, 
                                               input_dim, data_cfg.pred_len, data_cfg.seq_len, is_mamba=True, **cfg['kwargs'])
        elif cfg['type'] == 'lstm':
            pred_scaled, model = train_lstm(cfg['name'], x_train=x_train, y_train=y_train, x_val=x_val, y_val=y_val, 
                                            x_test=x_test, y_test=y_test, device=device, input_dim=input_dim, 
                                            pred_len=data_cfg.pred_len, seq_len=data_cfg.seq_len, **cfg['kwargs'])
            
        elapsed = time.perf_counter() - start_t
        
        # evaluation
        pred_scaled = pred_scaled.reshape(-1, data_cfg.pred_len)
        pred_inv = target_scaler.inverse_transform(pred_scaled.reshape(-1, 1)).reshape(pred_scaled.shape)
        pred_inv = np.clip(pred_inv, 0.0, 500.0)
        
        metrics = evaluate_regression(true_inv, pred_inv)
        print(f"{cfg['name']} trained in {elapsed:.1f}s. Avg R2: {metrics['avg_r2']:.4f}")
        
        preds_dict[cfg['name']] = pred_inv
        results[cfg['name']] = metrics
        # Save models
        torch.save(model.state_dict(), out_dir / f"{cfg['name']}.pt")
        
    # Ensemble Evaluation
    print("Evaluating Ensembles...")
    member_names = list(preds_dict.keys())
    stack_preds = np.stack([preds_dict[n] for n in member_names], axis=0)
    
    mean_pred = np.mean(stack_preds, axis=0)
    mean_metrics = evaluate_regression(true_inv, mean_pred)
    
    r2_weights = np.array([max(0.0, results[n]['avg_r2']) for n in member_names], dtype=np.float64)
    if r2_weights.sum() > 0:
        r2_weights /= r2_weights.sum()
    else:
        r2_weights = np.ones_like(r2_weights) / len(r2_weights)
        
    weighted_pred = np.tensordot(r2_weights, stack_preds, axes=(0, 0))
    weighted_metrics = evaluate_regression(true_inv, weighted_pred)
    
    rows = []
    for n in member_names:
        rows.append({"model": n, "type": "single", **results[n]})
    rows.append({"model": "ensemble_mean", "type": "ensemble", **mean_metrics})
    rows.append({"model": "ensemble_weighted_r2", "type": "ensemble", **weighted_metrics})
    
    df_res = pd.DataFrame(rows)
    df_res = df_res.sort_values("avg_r2", ascending=False).reset_index(drop=True)
    
    print("\n--- Final PCA Ensemble Results ---")
    print(df_res.to_string(index=False))
    
    df_res.to_csv(out_dir / "pca_ensemble_results.csv", index=False)
    
    print(f"\nAll models uniformly trained with PCA. Artifacts saved: {out_dir}")

if __name__ == '__main__':
    main()
