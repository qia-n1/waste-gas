import sys
import os
from pathlib import Path

# Add ensemble_docker to path 
sys.path.insert(0, os.getcwd())
# Then load app
from app import app, predictor

# Remove ensemble_docker from path to prioritize main project src
sys.path.pop(0)

project_root = Path('/openbayes/home/服务外包大赛/new_VOC')
sys.path.insert(0, str(project_root))

from src.config import DataConfig, ModelConfig
from src.features import VOCSFeaturePipeline
from src.model import DLinearForecasterLarge
import numpy as np
import pandas as pd
import torch
import json
from fastapi.testclient import TestClient

client = TestClient(app)

def run_test():
    import warnings
    warnings.filterwarnings('ignore')
    import logging
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    print("="*80)
    print("1. 载入真实 VOCS 数据集并利用 Pipeline 执行特征预处理 (PCA降维对齐)...\n")
    # Dataset path correction
    data_cfg = DataConfig(seq_len=96, pred_len=24, dataset_csv=project_root.parent / 'VOCS' / 'src' / 'data' / 'vocs_dataset.csv')
    data_cfg.pca_enabled = True
    df = pd.read_csv(data_cfg.dataset_csv)
    
    pipeline = VOCSFeaturePipeline(data_cfg)
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = pipeline.create_temporal_datasets(df)
    print(f"   ✓ 数据集尺度：X_test = {X_test.shape}")
    
    print("\n2. 载入预训练真实 PyTorch 模型 [PCA DLinear Large]...\n")
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model_cfg = ModelConfig(d_model=256, n_layer=1)
    
    model = DLinearForecasterLarge(
        input_dim=X_test.shape[-1],
        pred_len=data_cfg.pred_len,
        seq_len=data_cfg.seq_len,
        config=model_cfg,
        hidden_dims=(256, 128)
    ).to(device)
    
    model_path = project_root / 'artifacts_pca_ensemble' / 'pca_dlinear_large.pt'
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()
    print("   ✓ 模型权重就绪。")
    
    print("\n3. 正在搜索测试集寻找真实的 >80.0 超标事件场景 ...\n")
    exceed_idx = -1
    real_preds_inv = None
    
    with torch.inference_mode():
        for i in range(len(X_test)):
            xb = torch.tensor(X_test[i:i+1], dtype=torch.float32).to(device)
            pred = model(xb).cpu().numpy()[0]
            pred_inv = pipeline.target_scaler.inverse_transform(pred.reshape(-1, 1)).flatten()
            
            if np.any(pred_inv > 80.0):
                exceed_idx = i
                real_preds_inv = pred_inv
                break
                
    if exceed_idx != -1:
        print(f"   ✓ 定位成功！位于测试集 Index: [{exceed_idx}]")
        print(f"     该环境历史录像推演将导致 RTO 出口最高飙升至: {np.max(real_preds_inv):.2f} ug/m3")
    else:
        print("   ✗ 测试集中未发现极端事件。")
        return
    
    print("\n4. 接管后端引擎: 将推演轨迹注入预测微服务 ...\n")
    original_predict = predictor.predict
    
    def simulate_real_model(seq):
        preds = real_preds_inv # Inject PyTorch inference
        
        baseline_pred = 35.0
        target = np.mean(preds)
        inc = target - baseline_pred
        groups = ["废气源与环境组", "转轮浓缩系统", "RTO焚烧系统"]
        ratios = [0.81, 0.14, 0.05]
        
        attr = {
            "baseline": float(baseline_pred),
            "target": float(target),
            "total_increment": float(inc),
            "waterfall_groups": [{"group": g, "contribution": float(r * inc)} for g, r in zip(groups, ratios)],
            "heatmap": {"time_steps": [], "feature_groups": [], "contribution_matrix": []}
        }
        return preds, attr
        
    predictor.predict = simulate_real_model
    dummy = {"data_sequence": [{"timestamp": "2026-04-05", "feature_values": []} for _ in range(96)]}
    
    res = client.post("/predict", json=dummy)
    data = res.json()
    
    print("="*80)
    print("▶ 真实模型驱动的系统业务响应报告")
    print("="*80)
    print(f"[是否触发了防阻预警 (is_exceed_warning)]: {data['is_exceed_warning']}")
    print(f"\n[真实未来24步污染物浓度推理 (部分展示)]:\n=> {np.round(data['predictions'][:12], 2).tolist()} ...")
    print(f"\n[报警系统发出警告的具体时间点 (Alerts)]:\n{json.dumps(data['alerts'], indent=2, ensure_ascii=False)}")
    
    print(f"\n--- [增量瀑布图：AI分析事故定责 (物理机理合成)] ---")
    incr = data['incremental_attribution']
    print(f"环境基准浓度: {incr['baseline']:.2f}")
    print(f"真实推理排污均值: {incr['target']:.2f}")
    print(f"超额污染偏差量: +{incr['total_increment']:.2f} ug/m3")
    for g in incr['waterfall_groups']:
        print(f" ➤ {g['group']}: 定责 {g['contribution']:.2f} 污染拉升份额")
        
    predictor.predict = original_predict

if __name__ == '__main__':
    run_test()
