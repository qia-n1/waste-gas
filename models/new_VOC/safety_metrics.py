"""
安全导向的污染物预测评估指标模块。
支持：
  1. 软计算 trend_accuracy（考虑维持区间）
  2. 多步长变化准确率（2步、4步、8步）
  3. 传统回归指标（R2、MAE、RMSE）
  4. 超标相关指标（超标准确率、超标召回率等）
"""

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from typing import Dict


def soft_trend_accuracy(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    tolerance: float = 3.0,
) -> float:
    """
    软计算 trend_accuracy：考虑维持区间的趋势方向准确率。
    
    Args:
        y_true: 真实值，形状 (n_samples, pred_len)
        y_pred: 预测值，形状 (n_samples, pred_len)
        tolerance: 维持区间阈值。当 |diff| < tolerance 时，认为该步是"平稳"，
                   对平稳步的判断更温和（平稳 vs 平稳 = 正确，非平稳 vs 平稳 = 部分正确）
    
    Returns:
        soft_trend_accuracy 分数（0~1）
    """
    pred_diff = np.diff(y_pred, axis=1)  # (n_samples, pred_len - 1)
    true_diff = np.diff(y_true, axis=1)
    
    # 判断每一步是否处于"平稳"状态
    pred_stable = np.abs(pred_diff) < tolerance
    true_stable = np.abs(true_diff) < tolerance
    
    # 对于稳定状态，只要两边都稳定就算对；对于非稳定状态，方向要一致
    matches = np.zeros_like(true_diff, dtype=float)
    
    # 两边都稳定：完全匹配
    both_stable = pred_stable & true_stable
    matches[both_stable] = 1.0
    
    # 都不稳定：方向一致则匹配
    both_unstable = (~pred_stable) & (~true_stable)
    direction_match = np.sign(pred_diff[both_unstable]) == np.sign(true_diff[both_unstable])
    matches[both_unstable] = direction_match.astype(float)
    
    # 一稳一不稳：部分匹配（0.5）
    mixed = (pred_stable != true_stable)
    matches[mixed] = 0.5
    
    return float(np.mean(matches))


def multi_step_trend_accuracy(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    steps: list = None,
    tolerance: float = 3.0,
) -> Dict[str, float]:
    """
    计算不同步长的污染物浓度变化准确率。
    
    例如 2 步：比较 y[t+2] - y[t] 的方向是否一致。
    这样可以避免短期波动的影响，更好地捕捉污染物的长期趋势。
    默认整合软边界的计算逻辑（考虑波动容忍度）。
    
    Args:
        y_true: 真实值，形状 (n_samples, pred_len)
        y_pred: 预测值，形状 (n_samples, pred_len)
        steps: 要计算的步长列表，默认 [2, 4, 8]
        tolerance: 判断平稳状态的允许区间，用于软计算
    
    Returns:
        Dict，键为 f'trend_accuracy_{step}step'，值为对应的准确率
    """
    if steps is None:
        steps = [2, 4, 8]
    
    results = {}
    for step in steps:
        if step >= y_true.shape[1]:
            results[f'trend_accuracy_{step}step'] = float('nan')
            continue
        
        # 计算 step 步后的变化差分
        pred_diff = y_pred[:, step:] - y_pred[:, :-step]  # (n_samples, pred_len - step)
        true_diff = y_true[:, step:] - y_true[:, :-step]
        
        # 判断多步后的状态是否可以认为是"平稳"（采用相同的 tolerance 阈值）
        pred_stable = np.abs(pred_diff) < tolerance
        true_stable = np.abs(true_diff) < tolerance
        
        matches = np.zeros_like(true_diff, dtype=float)
        
        # 两边都稳定：完全匹配 1.0
        both_stable = pred_stable & true_stable
        matches[both_stable] = 1.0
        
        # 都不稳定：方向是否一致
        both_unstable = (~pred_stable) & (~true_stable)
        direction_match = np.sign(pred_diff[both_unstable]) == np.sign(true_diff[both_unstable])
        matches[both_unstable] = direction_match.astype(float)
        
        # 一稳一不稳：部分匹配 0.5
        mixed = (pred_stable != true_stable)
        matches[mixed] = 0.5
        
        accuracy = float(np.mean(matches))
        results[f'trend_accuracy_{step}step'] = accuracy
    
    return results


def evaluate_regression_safe(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    exceed_threshold: float = 80.0,
    tolerance: float = 3.0,
    multi_step_list: list = None,
) -> Dict[str, float]:
    """
    综合安全评估函数：集合传统回归指标、趋势指标、超标指标。
    
    Args:
        y_true: 真实值，形状 (n_samples, pred_len)
        y_pred: 预测值，形状 (n_samples, pred_len)
        exceed_threshold: 超标阈值（用于计算超标准确率、超标召回率）
        tolerance: soft_trend_accuracy 的维持区间阈值
        multi_step_list: 多步长列表，默认 [2, 4, 8]
    
    Returns:
        包含所有指标的字典
    """
    if multi_step_list is None:
        multi_step_list = [2, 4, 8]
    
    metrics = {}
    
    # ========== 传统回归指标 ==========
    metrics['avg_r2'] = float(
        np.mean([r2_score(y_true[:, i], y_pred[:, i]) for i in range(y_true.shape[1])])
    )
    metrics['avg_mae'] = float(
        np.mean([mean_absolute_error(y_true[:, i], y_pred[:, i]) for i in range(y_true.shape[1])])
    )
    metrics['avg_rmse'] = float(
        np.mean([np.sqrt(mean_squared_error(y_true[:, i], y_pred[:, i])) for i in range(y_true.shape[1])])
    )
    
    # ========== 硬计算 Trend Accuracy（原始版本，保留兼容性） ==========
    pred_diff = np.diff(y_pred, axis=1)
    true_diff = np.diff(y_true, axis=1)
    metrics['trend_accuracy_hard'] = float(np.mean(np.sign(pred_diff) == np.sign(true_diff)))
    
    # ========== 软计算 Trend Accuracy ==========
    metrics['trend_accuracy_soft'] = soft_trend_accuracy(y_true, y_pred, tolerance=tolerance)
    
    # ========== 多步长趋势准确率 ==========
    multi_step_metrics = multi_step_trend_accuracy(y_true, y_pred, steps=multi_step_list, tolerance=tolerance)
    metrics.update(multi_step_metrics)
    
    # ========== 超标相关指标 ==========
    # 超标准确率：真实值和预测值的超标状态是否一致
    y_true_exceed = y_true > exceed_threshold
    y_pred_exceed = y_pred > exceed_threshold
    metrics['exceed_accuracy'] = float(np.mean(y_true_exceed == y_pred_exceed))
    
    # 超标召回率：真实超标时，模型有多少次也预测超标
    num_true_exceed = np.sum(y_true_exceed)
    if num_true_exceed > 0:
        num_true_positive = np.sum(y_true_exceed & y_pred_exceed)
        metrics['exceed_recall'] = float(num_true_positive / num_true_exceed)
    else:
        metrics['exceed_recall'] = float('nan')
    
    # 超标漏报率：真实超标但预测未超标（与recall互补）
    if num_true_exceed > 0:
        num_missed = np.sum((~y_pred_exceed) & y_true_exceed)
        metrics['exceed_miss_rate'] = float(num_missed / num_true_exceed)
    else:
        metrics['exceed_miss_rate'] = float('nan')
    
    # 超标误报率：真实未超标但预测超标
    num_true_not_exceed = np.sum(~y_true_exceed)
    if num_true_not_exceed > 0:
        num_false_positive = np.sum(y_pred_exceed & (~y_true_exceed))
        metrics['exceed_false_positive_rate'] = float(num_false_positive / num_true_not_exceed)
    else:
        metrics['exceed_false_positive_rate'] = float('nan')
    
    # ========== 按预测跨度分段评估 ==========
    short_end = min(8, y_true.shape[1])
    medium_end = min(16, y_true.shape[1])
    
    metrics['short_r2'] = float(
        r2_score(y_true[:, :short_end].reshape(-1), y_pred[:, :short_end].reshape(-1))
    )
    metrics['medium_r2'] = float(
        r2_score(y_true[:, short_end:medium_end].reshape(-1), y_pred[:, short_end:medium_end].reshape(-1))
    ) if medium_end > short_end else float('nan')
    metrics['long_r2'] = float(
        r2_score(y_true[:, medium_end:].reshape(-1), y_pred[:, medium_end:].reshape(-1))
    ) if y_true.shape[1] > medium_end else float('nan')
    
    return metrics


def print_safety_metrics_summary(metrics: Dict[str, float]) -> None:
    """
    打印安全评估指标的汇总信息。
    
    Args:
        metrics: 由 evaluate_regression_safe 返回的指标字典
    """
    print("\n" + "=" * 70)
    print("安全导向评估指标汇总")
    print("=" * 70)
    
    section_order = [
        ("传统回归指标", ["avg_r2", "avg_mae", "avg_rmse"]),
        ("趋势准确率", ["trend_accuracy_hard", "trend_accuracy_soft"]),
        ("多步长趋势准确率", [k for k in metrics.keys() if k.startswith("trend_accuracy_") and "step" in k]),
        ("超标相关指标", ["exceed_accuracy", "exceed_recall", "exceed_miss_rate", "exceed_false_positive_rate"]),
        ("分段预测性能", ["short_r2", "medium_r2", "long_r2"]),
    ]
    
    for section_name, keys in section_order:
        valid_keys = [k for k in keys if k in metrics]
        if valid_keys:
            print(f"\n【{section_name}】")
            for key in valid_keys:
                val = metrics[key]
                if isinstance(val, float):
                    print(f"  {key:30s}: {val:10.6f}")
                else:
                    print(f"  {key:30s}: {val}")
    
    print("\n" + "=" * 70)
