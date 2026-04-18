import sys
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from fastapi.testclient import TestClient

import warnings
warnings.filterwarnings('ignore')
logging.getLogger("httpx").setLevel(logging.WARNING)

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.config import DataConfig, ModelConfig
from src.features import VOCSFeaturePipeline
from src.model import DLinearForecasterLarge
from app import app, predictor

client = TestClient(app)

FEATURE_TO_GROUP = {
    "ambient_temp": "废气源与环境组",
    "ambient_humidity": "废气源与环境组",
    "coating_flow": "废气源与环境组",
    "coating_conc": "废气源与环境组",
    "rotor_speed": "转轮浓缩系统",
    "adsorption_fan_power": "转轮浓缩系统",
    "desorption_temp": "转轮浓缩系统",
    "concentrated_flow": "转轮浓缩系统",
    "rto_in_flow": "RTO焚烧系统",
    "combustion_temp": "RTO焚烧系统",
    "burner_gas_flow": "RTO焚烧系统",
}

ATTR_FEATURE_ORDER = [
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
    "rto_in_conc",
    "rto_in_temp",
    "rto_in_pressure",
    "burner_gas_flow",
    "combustion_temp",
    "rto_out_temp",
]


def _fit_dynamic_feature_attr(seq: list[dict], total_increment: float, preds: np.ndarray) -> list[dict]:
    if len(seq) == 0:
        return []

    rows = []
    for item in seq:
        vals = item.get('feature_values', [])
        if isinstance(vals, list) and len(vals) > 0:
            rows.append(vals)

    if len(rows) == 0:
        return []

    x = np.asarray(rows, dtype=np.float64)
    n_feat = min(x.shape[1], len(ATTR_FEATURE_ORDER))
    if n_feat <= 0:
        return []

    x = x[:, :n_feat]
    feat_names = ATTR_FEATURE_ORDER[:n_feat]

    mu = x.mean(axis=0)
    sigma = x.std(axis=0) + 1e-6
    level_score = np.abs(x[-1] - mu) / sigma
    trend_score = np.abs(x[-1] - x[0]) / sigma
    vol_score = x.std(axis=0)

    pred_peak = float(np.max(preds)) if preds.size > 0 else 0.0
    exceed_pressure = max(0.0, pred_peak - 80.0) / 80.0
    slope = float(np.mean(np.abs(np.diff(preds)))) if preds.size > 1 else 0.0
    base_mag = max(1.0, float(np.mean(np.abs(preds))) if preds.size > 0 else 1.0)
    slope_pressure = slope / base_mag
    pressure = 1.0 + 0.35 * exceed_pressure + 0.15 * slope_pressure

    raw_score = (0.50 * level_score + 0.30 * trend_score + 0.20 * vol_score) * pressure
    raw_score = np.clip(raw_score, 0.0, None)

    top_k = min(12, n_feat)
    top_idx = np.argsort(raw_score)[-top_k:]
    top_scores = raw_score[top_idx]
    score_sum = float(top_scores.sum())
    if score_sum <= 1e-8:
        return []

    ratios = top_scores / score_sum
    out = []
    for idx, ratio in sorted(zip(top_idx, ratios), key=lambda t: t[1], reverse=True):
        feat = feat_names[int(idx)]
        out.append({
            "feature": feat,
            "group": FEATURE_TO_GROUP.get(feat, "其它"),
            "ratio": float(ratio),
            "contribution": float(total_increment * ratio),
        })
    return out


def _to_group_attr(feature_rows: list[dict]) -> list[dict]:
    group_sum = {}
    for row in feature_rows:
        grp = row["group"]
        group_sum[grp] = group_sum.get(grp, 0.0) + float(row["contribution"])
    return [{"group": g, "contribution": float(v)} for g, v in group_sum.items()]

def run_real_test():
    print("="*80)
    print("1. 载入真实 VOCS 数据集并利用 Pipeline 执行特征预处理 (PCA降维对齐)...\n")
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
    
    print("\n3. 正在搜索测试集寻找真实的 >80 超标事件场景 ...\n")
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
        print(f"     该环境历史录像推演将导致 RTO 出口最高飙升至: {np.max(real_preds_inv):.2f} ug/m³")
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
        feature_rows = _fit_dynamic_feature_attr(seq=seq, total_increment=float(inc), preds=np.asarray(preds, dtype=np.float64))
        group_rows = _to_group_attr(feature_rows)
        
        attr = {
            "baseline": float(baseline_pred),
            "target": float(target),
            "total_increment": float(inc),
            "feature_contributions": feature_rows,
            "group_contributions": group_rows,
            "heatmap": {"time_steps": [], "feature_groups": [], "contribution_matrix": []} # 略去矩阵展示
        }
        return preds, attr
        
    predictor.predict = simulate_real_model
    sample_seq = X_test[exceed_idx]
    dummy = {
        "data_sequence": [
            {"timestamp": f"2026-04-05T{(i // 4):02d}:{(i % 4) * 15:02d}:00", "feature_values": sample_seq[i].tolist()}
            for i in range(sample_seq.shape[0])
        ]
    }
    
    res = client.post("/predict", json=dummy)
    data = res.json()
    
    print("="*80)
    print("▶ 真实模型驱动的系统业务响应报告")
    print("="*80)
    print(f"[是否触发了警报 (is_exceed_warning)]: {data['is_exceed_warning']}")
    print(f"\n[真实未来24步污染物浓度推理 (前8步)]:\n=> {np.round(data['predictions'][:8], 2).tolist()}")
    print(f"\n[报警系统下发具体时间节点预警 (Alerts)]:\n{json.dumps(data['alerts'][:3], indent=2, ensure_ascii=False)} ... (截断展示)")
    
    print(f"\n--- [增量瀑布图：AI分析事故定责 (基于真实幅度切分)] ---")
    incr = data['incremental_attribution']
    print(f"环境基准浓度: {incr['baseline']:.2f}")
    print(f"真实推理均值: {incr['target']:.2f}")
    print(f"总污染偏移量: +{incr['total_increment']:.2f} ug/m³")
    print("细分指标贡献度 Top 8:")
    for f in incr.get('feature_contributions', [])[:8]:
        print(f" ➤ {f['feature']} ({f['group']}): +{f['contribution']:.2f} [{f['ratio']:.0%}]")
    print("分组聚合贡献度(兼容):")
    for g in incr.get('group_contributions', []):
        print(f" ➤ {g['group']}: 承担 +{g['contribution']:.2f} 污染拉升份额")
        
    predictor.predict = original_predict

if __name__ == '__main__':
    run_real_test()
