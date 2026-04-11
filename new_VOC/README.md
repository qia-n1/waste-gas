# new_VOC

面向 `VOCS` 项目的 Mamba 适配框架，保持原系统的输入输出协议不变：

- 输入仍然是 `26` 字段传感器 JSON / CSV。
- 特征工程仍然对齐 `VOCS`：`96` 步历史窗口，构造成 `51` 维输入特征。
- 输出仍然是 `24` 步 VOCs 预测，形状为 `(batch, 24, 1)`。

## 目录

- `src/config.py`：字段定义、数据配置、模型配置和 880M 参数上限。
- `src/features.py`：与 `VOCS` 对齐的时间特征、滚动统计、Scaler 保存格式。
- `src/model.py`：基于官方 `Mamba3` 模块的时序预测模型。
- `src/predictor.py`：推理与 warmup 预测逻辑。
- `src/visualization.py`：训练曲线和预测窗口可视化。
- `train.py`：训练入口。
- `server.py`：兼容 `VOCS` 主接口格式的 FastAPI 服务骨架。
- `new_VOC_workflow.ipynb`：按 notebook 单元格范式组织的使用示例。

## 依赖

推荐优先安装官方 CUDA 版本依赖（Linux + NVIDIA CUDA）：

```bash
pip install -r requirements.txt
```

其中关键包为：

- `mamba-ssm`
- `causal-conv1d`

若环境中已安装 `mamba_ssm`，代码会优先使用 site-packages 的官方实现。

如果你希望复用工作区中已经拉取的 Mamba 源码（只读，不改 third_party），支持以下路径：

- `../../third_party/state-spaces-mamba`

打包时也支持把依赖随项目一起放在下面任一位置：

- `third_party/state-spaces-mamba`
- `../third_party/state-spaces-mamba`

也可以通过环境变量覆盖：

```bash
export MAMBA_SSM_PATH=/path/to/state-spaces-mamba
```

未安装官方 `mamba_ssm` 时，会自动尝试上述源码路径。

## 训练

```bash
cd ./new_VOC
PYTHONPATH=. python train.py --epochs 5
```

## 启动兼容服务

```bash
cd ./new_VOC
PYTHONPATH=. python server.py
```

## 参数规模约束

模型构建时会检查总参数量，默认严格限制在 `880,000,000` 以内。当前默认配置是便于本地开发和调试的平衡版，不会直接把模型堆到上限。
