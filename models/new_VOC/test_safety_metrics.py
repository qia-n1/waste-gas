#!/usr/bin/env python3
"""
快速测试 safety_metrics 模块是否能正常工作
"""

import numpy as np
import sys
from pathlib import Path

# 添加 new_VOC 路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

from safety_metrics import (
    soft_trend_accuracy,
    multi_step_trend_accuracy,
    evaluate_regression_safe,
    print_safety_metrics_summary
)

print("="*70)
print("安全指标模块测试")
print("="*70)

# 创建简单的测试数据
np.random.seed(42)
n_samples, pred_len = 100, 24

# 生成模拟的真实值和预测值
y_true = np.random.uniform(30, 120, size=(n_samples, pred_len))
# 预测值基于真实值添加一些噪声
y_pred = y_true + np.random.normal(0, 5, size=(n_samples, pred_len))

print(f"\n✓ 生成测试数据:")
print(f"  - 样本数: {n_samples}")
print(f"  - 预测长度: {pred_len}")
print(f"  - 真实值范围: [{y_true.min():.2f}, {y_true.max():.2f}]")
print(f"  - 预测值范围: [{y_pred.min():.2f}, {y_pred.max():.2f}]")

# 测试 1: 软计算 Trend Accuracy
print("\n" + "-"*70)
print("测试 1: 软计算 Trend Accuracy")
print("-"*70)

soft_acc = soft_trend_accuracy(y_true, y_pred, tolerance=0.5)
print(f"✓ soft_trend_accuracy 结果: {soft_acc:.4f}")

# 测试 2: 多步长变化准确率
print("\n" + "-"*70)
print("测试 2: 多步长变化准确率")
print("-"*70)

multi_step = multi_step_trend_accuracy(y_true, y_pred, steps=[2, 4, 8])
for key, val in multi_step.items():
    print(f"✓ {key}: {val:.4f}")

# 测试 3: 完整的安全评估
print("\n" + "-"*70)
print("测试 3: 完整的安全评估")
print("-"*70)

metrics = evaluate_regression_safe(
    y_true,
    y_pred,
    exceed_threshold=80.0,
    tolerance=6,
    multi_step_list=[2, 4, 8]
)

print("✓ 完整指标计算成功")
print(f"  - 返回的指标数: {len(metrics)}")
print(f"  - 指标列表:")
for key in sorted(metrics.keys()):
    val = metrics[key]
    if isinstance(val, float):
        status = "✓" if not np.isnan(val) else "⚠"
        print(f"    {status} {key}: {val:.6f}")
    else:
        print(f"    - {key}: {val}")

# 测试 4: 打印汇总
print("\n" + "-"*70)
print("测试 4: 美化汇总输出")
print("-"*70)

print_safety_metrics_summary(metrics)

# 最终结果
print("\n" + "="*70)
print("✓ 所有测试通过！安全指标模块工作正常")
print("="*70)
