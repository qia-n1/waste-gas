# 安全导向指标模块使用指南

## 文件结构

- **`safety_metrics.py`**: 安全评估指标的核心模块（约200行）
- **`VOC_dlinear_lstm_mamba_etc.ipynb`**: 集成演示 notebook

## 核心功能概览

### 1. 软计算 Trend Accuracy（`soft_trend_accuracy`）

**背景**: 污染物浓度时间序列非常波动，相邻两时刻的简单方向比较（硬计算）不适合。

**改进方案**:
- 引入"维持区间"概念（tolerance 参数）
- 当 `|差分值| < tolerance` 时，该步认为"平稳"
- 判断规则：
  - **两边都平稳** → 完全匹配（1.0分）
  - **都不平稳** → 方向一致则匹配（1.0分），否则不匹配（0分）
  - **一稳一不稳** → 部分匹配（0.5分）

**参数**:
- `y_true, y_pred`: 真实和预测序列
- `tolerance`: 维持区间阈值（默认0.5）

**示例**:
```python
from safety_metrics import soft_trend_accuracy

score = soft_trend_accuracy(y_true, y_pred, tolerance=0.5)
# 返回 0.0~1.0 的分数
```

---

### 2. 多步长变化准确率（`multi_step_trend_accuracy`）

**背景**: 污染物浓度短期波动剧烈，但长期趋势相对稳定。单步观察容易被噪声干扰。

**改进方案**:
- 计算 2步、4步、8步后的变化方向
- 例如 2步：比较 `y[t+2] - y[t]` 的方向是否与真实值一致
- 这样可以过滤短期波动，专注长期趋势

**返回**:
```python
{
    'trend_accuracy_2step': 0.68,
    'trend_accuracy_4step': 0.72,
    'trend_accuracy_8step': 0.75,
}
```

**意义**:
- 如果多步长准确率明显高于单步，说明模型抓住了长期趋势但短期误差大
- 对于早期预警系统，多步长准确率更有参考价值

---

### 3. 安全相关指标（`evaluate_regression_safe`）

一次性计算所有指标，包括：

#### 传统回归指标
- `avg_r2`: 平均 R² 得分
- `avg_mae`: 平均绝对误差
- `avg_rmse`: 均方根误差

#### 趋势指标
- `trend_accuracy_hard`: 硬计算趋势准确率（原始版）
- `trend_accuracy_soft`: 软计算趋势准确率（新增）
- `trend_accuracy_2step`, `trend_accuracy_4step`, `trend_accuracy_8step`: 多步长趋势准确率（新增）

#### 超标相关指标（至关重要）
- `exceed_accuracy`: 超标状态判断准确率
- `exceed_recall`: **超标召回率** — 真实超标时预测有多少比例也报超标（越高越好）
- `exceed_miss_rate`: **超标漏报率** — 真实超标但预测未报的比例（越低越好）
- `exceed_false_positive_rate`: **超标误报率** — 预测超标但真实未超的比例（适度即可）

#### 分段预测性能
- `short_r2`: 短期（0~8步）R²
- `medium_r2`: 中期（8~16步）R²
- `long_r2`: 长期（16+步）R²

---

## 使用示例

### 基础用法

```python
from safety_metrics import evaluate_regression_safe, print_safety_metrics_summary

# 对模型预测进行评估
metrics = evaluate_regression_safe(
    y_true,           # 真实值，形状 (n_samples, 24)
    y_pred,           # 预测值，形状 (n_samples, 24)
    exceed_threshold=80.0,        # 超标阈值
    tolerance=0.5,                # 软计算维持区间
    multi_step_list=[2, 4, 8]     # 多步长配置
)

# 打印美化的汇总信息
print_safety_metrics_summary(metrics)
```

### 在 Notebook 中集成使用

在你的 `VOC_dlinear_lstm_mamba_etc.ipynb` 末尾已添加演示单元：

```python
from safety_metrics import evaluate_regression_safe, print_safety_metrics_summary

# 对集成模型进行评估
safe_metrics = evaluate_regression_safe(
    y_true_ensemble,
    y_pred_mean,
    exceed_threshold=80.0,
    tolerance=0.5,
    multi_step_list=[2, 4, 8]
)

# 查看所有指标
print_safety_metrics_summary(safe_metrics)

# 访问单个指标
print(f"超标召回率: {safe_metrics['exceed_recall']:.4f}")
print(f"超标漏报率: {safe_metrics['exceed_miss_rate']:.4f}")
print(f"4步准确率: {safe_metrics['trend_accuracy_4step']:.4f}")
```

---

## 关键指标解读

### 对污染物预测的意义

| 指标 | 含义 | 优化目标 | 备注 |
|------|------|----------|------|
| `exceed_recall` | 真实超标时预测也报超标的比例 | **越高越好** | 漏报最危险，应在0.85+以上 |
| `exceed_miss_rate` | 真实超标但预测遗漏的比例 | **越低越好** | recall = 1 - miss_rate |
| `exceed_false_positive_rate` | 预测超标但实际未超的比例 | **适度**（<20%） | 误报可容忍，但不能太多 |
| `trend_accuracy_soft` | 考虑波动维持的趋势准确率 | 0.5+ 即可接受 | 比硬计算更现实 |
| `trend_accuracy_4step` | 4步变化方向准确率 | 0.6+ 较好 | 对预警系统最有参考价值 |
| `avg_rmse` | 数值误差 | 尽量小，但<15较好 | 辅助指标，不是主要评价维度 |

### 实际应用中的权重建议

```
综合安全评分 = 0.4 * recall + 0.3 * (1 - miss_rate) 
              + 0.2 * trend_4step - 0.1 * false_positive
```

若 `recall < 0.8` 或 `miss_rate > 0.2`，该模型**不建议用于实际预警**。

---

## 自定义参数

### 修改超标阈值

```python
# 对于不同污染物，可调整阈值
metrics = evaluate_regression_safe(
    y_true, y_pred,
    exceed_threshold=100.0,  # 改为100而不是80
    tolerance=0.5,
    multi_step_list=[2, 4, 8]
)
```

### 调整维持区间

```python
# 更敏感：减小 tolerance
metrics_sensitive = evaluate_regression_safe(
    y_true, y_pred,
    exceed_threshold=80.0,
    tolerance=0.2,  # 更严格，较少地认为"平稳"
    multi_step_list=[2, 4, 8]
)

# 更宽松：增大 tolerance
metrics_loose = evaluate_regression_safe(
    y_true, y_pred,
    exceed_threshold=80.0,
    tolerance=1.0,  # 更宽松，更多步被认为"平稳"
    multi_step_list=[2, 4, 8]
)
```

### 自定义多步长

```python
# 只看长期趋势
metrics = evaluate_regression_safe(
    y_true, y_pred,
    exceed_threshold=80.0,
    tolerance=0.5,
    multi_step_list=[6, 12, 24]  # 自定义步长
)
```

---

## 输出文件

运行演示单元后，会生成：

1. **`safe_metrics_comparison.csv`**: 硬计算 vs 软计算 vs 多步长的对比
2. **`complete_safe_metrics.csv`**: 所有单模型和集成模型的完整指标表

这些文件保存在 `cfg.output_dir / 'logs'` 目录。

---

## 注意事项

1. **缺失值处理**: 如果多步长超过序列长度，返回 `nan`
   ```python
   # 若 pred_len=24，则 trend_accuracy_32step 会返回 nan
   ```

2. **超标指标的有效性**: 至少需要有一个样本超标或未超标，否则对应指标为 `nan`

3. **软计算的 tolerance 选择**:
   - 对于浓度数据（范围0~500），tolerance=0.5 比较合理
   - 可根据数据的标准差调整：`tolerance = 0.5 * std(data)`

4. **模态切换**: 在开发/UT阶段多看硬指标，上线后主要看 soft + 多步长 + recall

---

## 总结

新指标体系的核心优势：
- ✅ **更贴近污染物预测的实际特性**（波动大、需要长期趋势）
- ✅ **聚焦安全风险**（超标漏报、提前预警）
- ✅ **可扩展**（轻松调整参数适配不同场景）
- ✅ **向后兼容**（保留原有指标，新指标并行计算）
