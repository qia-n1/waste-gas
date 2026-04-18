# VOCs 集成预测微服务后端交接文档

> 迁移说明：当前生产部署请优先采用固定 v6 协议链路，见同目录 `迁移到协议v6.md` 与仓库根目录 `模型端后端交互协议_v6.md`。

本文档面向后端/运维工程师，旨在说明“VOCs 废气（转轮+RTO）预测与预警模型”的 Docker 化微服务如何构建、启动、对接以及项目结构分布。

---

## 1. 部署与一键打包指令

本服务已实现与训练环境的 **100% 物理完全解耦**。在打包发送给第三方或服务器部署前，需执行抽离提取指令将所需依赖自动隔离进独立包中。

### 1.1 提取与构建（一键脚本）
在终端中进入项目主目录并执行打包脚本：
```bash
cd ./new_VOC/ensemble_docker
chmod +x build_and_pack.sh
./build_and_pack.sh
```
*(注：该脚本会自动从庞大的训练环境库中提取模型定义 `*.py`、最优权重 `pca_dlinear_large.pt` 以及预处理基线数据，并修正所有的相对引用路径。)*

### 1.2 启动服务 (Docker Compose)
构建指令会自动拉起 Docker Compose 环境，如果需要手动干预或重启服务，可以执行：
```bash
docker compose up --build -d
```
服务将在宿主机的 **8000** 端口提供 HTTP REST 接口。（基于 `python:3.10-slim`，已限定最大可用内存为 4GB）。

---

## 2. API 接口规格说明

服务启动后，提供标准的 FastAPI RESTful 接口进行模型推理与 XAI (可解释性AI) 归因分析响应。

### 2.1 模型预测与异常归因接口
- **路径**：`POST /predict`
- **Content-Type**: `application/json`
- **业务功能**：接收过去 96 个维度的真实传感器历史序列，输出未来 24 步（下个小时）的预测预测浓度、超标预警以及增量瀑布图归因定责。

#### 【请求体 Request Body】
必须包含绝对长度等于 `96` 步的历史时序字典序列，内置工业传感器特征值需严格对齐。
```json
{
  "data_sequence": [
    {
      "timestamp": "2026-04-05T00:00:00",
      "feature_values": [1.5, 2.1, 8.4, "... (总计特征规模见config)"]
    },
    // ... 必须正好包含 96 个时间步对象
  ]
}
```

#### 【响应体 Response Body】
包含完整的预测序列、安全巡断以及带有业务机理解释性的 XAI 视图数据：
```json
{
  "status": "success",
  "predictions": [
    39.45, 41.22, 81.33, 79.55 // ... 返回未来24步预估值 (RTO出口排污浓度: ug/m³)
  ],
  "is_exceed_warning": true, // 【核心阻断标识】如果预测曲线中出现大于80.0的点，系统自动抛出true
  "alerts": [ // 当 is_exceed_warning 为 true 时下发详情警告时间步
    {
      "step": 3,
      "value": 81.33,
      "warning": "污染物超标预警!"
    }
  ],
  "incremental_attribution": { // 【前端大屏瀑布图数据源】超标事件定责分析
    "baseline": 35.0, // 系统安全基线
    "target": 70.80,  // 本次事件推演的预测均值
    "total_increment": 35.80, // 总计超标偏移量
    "feature_contributions": [ // 细分指标贡献度（推荐作为主展示来源）
      { "feature": "coating_conc", "group": "废气源与环境组", "ratio": 0.24, "contribution": 8.59 },
      { "feature": "coating_flow", "group": "废气源与环境组", "ratio": 0.16, "contribution": 5.73 },
      { "feature": "rotor_speed", "group": "转轮浓缩系统", "ratio": 0.10, "contribution": 3.58 },
      { "feature": "combustion_temp", "group": "RTO焚烧系统", "ratio": 0.07, "contribution": 2.51 }
    ],
    "group_contributions": [ // 分组责任划扣结果，前端据此可直接画带上下箭头的瀑布大屏图
      { "group": "废气源与环境组", "contribution": 28.99 }, // 例：车间产排是超标主因
      { "group": "转轮浓缩系统", "contribution": 5.01 },
      { "group": "RTO焚烧系统", "contribution": 1.80 }
    ],
    "heatmap": { // 【时间-特征溯源热力图】前端可画 24步*特征组 的热力区块图
      "time_steps": ["t+1", "t+2", "...", "t+24"],
      "feature_groups": ["废气源与环境组", "转轮浓缩系统", "RTO焚烧系统"],
      "contribution_matrix": [[...], [...], "..."] 
    }
  }
}
```

说明：
- `feature_contributions` 是细分指标级别的贡献度，适合精细化溯源、TopN 展示和审计。
- `group_contributions` 由 `feature_contributions` 自动聚合得到，主要用于兼容历史前端图表。

### 2.2 健康检查接口
- **路径**：`GET /health`
- **响应**：`{"status": "healthy"}` (适用于 K8s / 负载均衡器探测健康状态)

---

## 3. 相关文件与架构目录说明

`ensemble_docker/` 是交付给后端的**高度解耦**的干净根目录。所有用于生产推演的必要物资均被自动化脚本锁入该文件夹，其主要分布如下：

| 文件 / 目录名 | 用途说明 | 开发/归属备注 |
| :--- | :--- | :--- |
| **`app.py`** | FastAPI 路由核心入口文件。包含上述 `/predict` 接口控制以及入参/出参的 Pydantic 模型 Schema 约束。 | 负责外层 HTTP 传输及业务裁决（拦截超标、组装预警Alerts等） |
| **`Dockerfile` & `docker-compose.yml`** | Docker 构建约束与一键拉起编排文件。基础镜像使用的是无头瘦身版的 `python:3.10-slim`。 | - |
| **`build_and_pack.sh`** | 部署工程构建脚本。将本目录打包交给客户前，必须跑一次。负责去上级代码母库将需要的碎片抽离进当前下设隔离区中。| 强隔离保证，无需修改。 |
| **`requirements_deploy.txt`** | 纯净的推理运行环境。去除了极其沉重的如 mamba-ssm、causal-conv1d 等模型训练包仅保留推演底层 `torch`。 | 后端若扩展依赖请在此追加。 |
| **`api_src/`** | 执行打包脚本后自动生成的隔离源码区。它从科研目录复制了轻量级 `model.py`、`features.py` 和 `config.py`。 | 核心网路权重结构图及数据前处理架构层（请勿改动）。|
| **`api_src/ensemble_predictor.py`** | **【微服务后端对接核心】** `EnsemblePredictor` 推演包装类。在 `app.py` 被实例化，接管从张量 Tensor 构建、过 PCA 处理、PyTorch 加载及推理，至推导物理引擎归因的底座。 | 算法与系统后端的承接适配器。如果要接真实 XAI `Input*Grad` 反向传播计算逻辑，在这里写。 |
| **`models/`** | 执行脚本后生成的权重库区。装载有生产推演的主力军 `pca_dlinear_large.pt`。 | 若后续更新模型字典权重库，请覆盖丢入该目录。 |
| **`data/`** | 执行脚本后生成的静态数据区。包含 `vocs_dataset.csv` 基线数据，供系统的前置处理 Pipeline (例如 PCA) 定位缩放器标度用。 | - |

> **交接备注**：当前架构已经跑通 `FastAPI -> PyTorch (DLinear PCA Large) -> 业务诊断响应` 的正向通道验证。后续可直接以本文件夹作为代码提交或 `tar.gz` 发版包单元给乙方私有化部署。