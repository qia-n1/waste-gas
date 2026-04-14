# 管理端开发历史

## 项目概述

智洁园区 - 废气综合管理平台 管理端（admin），独立于同事的用户端（`frontend/` + `backend/`），在 `admin/` 目录下搭建独立前后端。

---

## Phase 1：项目初始化与骨架搭建

### 前端 `admin/frontend/`
- **技术栈**：Vue 3 + TypeScript + Vite + Pinia + Element Plus + ECharts + Three.js
- 开发服务器端口 `3001`
- Vite 代理配置：`/api` → `localhost:8002`（管理端后端），`/vocs` → `localhost:8001`（ML服务）
- Element Plus 暗黑主题注册，ECharts 组件全局注册（HeatmapChart, LineChart, PieChart 等）

### 后端 `admin/backend/`
- **技术栈**：FastAPI + httpx + PyJWT
- 端口 `8003`（避免与 new_VOC/server.py 默认 8002 冲突）
- CORS 中间件，JWT 认证
- 路由模块：auth、dashboard、alerts、users

---

## Phase 2：暗黑工业主题 & 布局

### 全局样式 `style.css`
- 背景 `#07101d`，面板 `rgba(14,25,49,0.84)`，glassmorphism `.panel-card`
- 强调色：青色 `#00d4ff`（正常）、琥珀色 `#ffaa00`（警告）、红色 `#ff4444`（严重）
- 自定义滚动条样式（6px 宽，半透明）

### 布局 `DashboardLayout.vue`
- CSS Grid 三栏布局：`minmax(310px,360px) 1fr minmax(320px,400px)`
- 顶部 HeaderBar 88px，下方三栏 `calc(100vh - 88px)`
- 左栏整体滚动 `overflow-y: auto; scrollbar-gutter: stable`
- 右栏各面板独立滚动 `overflow: hidden`

### 页眉 `HeaderBar.vue`
- 左侧 Logo SVG + "回队" 标签
- 居中标题 "智洁园区 - 废气综合管理平台"
- 右侧实时指标：时间、在线设备、告警次数、退出按钮
- `border-radius: 14px`

---

## Phase 3：大屏面板组件

### 左侧面板
| 组件 | 功能 |
|------|------|
| `VocsTrendChart.vue` | VOCs 浓度趋势折线图，实测（青色实线）+ 预测（琥珀色虚线），阈值标线 80/100，日期选择器 |
| `EquipmentStatusChart.vue` | 设备状态环形图：正常/预警/故障/离线 |
| `AnomalyHeatmap.vue` | 异常时段热力图，X轴日期 Y轴0-23小时 |

### 中央面板
| 组件 | 功能 |
|------|------|
| `FactoryScene.vue` | Three.js 3D 工厂可视化，监测点颜色随状态变化 |

### 右侧面板
| 组件 | 功能 |
|------|------|
| `AlarmCenter.vue` | 实时告警表格，搜索过滤，SSE 推送 |
| `ContinuousAlerts.vue` | 异常持续关注卡片，实时计时器 |
| `DecisionSupport.vue` | VOCs 实时大数字、关键参数、AI 建议、操作按钮 |

---

## Phase 4：后端数据层 `vocs_proxy.py`

### 数据源优先级
1. **vocs_server**（端口 8001）— SSE 实时推送 + REST API
2. **本地 CSV** — `vocs_realtime_data.csv` 作为 fallback

### 主要函数
| 函数 | 用途 |
|------|------|
| `fetch_status()` | 获取 ML 服务状态 |
| `fetch_latest_sensor()` | 最新传感器数据（26字段） |
| `fetch_latest_prediction()` | 最新预测结果 |
| `fetch_alerts()` | 告警列表 |
| `get_dashboard_overview()` | 聚合大屏全部数据 |
| `get_equipment_status()` | 设备状态统计 |
| `get_anomaly_heatmap()` | 异常热力图数据 |
| `get_alert_diagnosis()` | 告警诊断详情 |

---

## Phase 5：布局修复

### 问题与修复
- **VOCs 趋势图被截断**：`.trend-card` 从 `min-height: 0` 改为 `min-height: 380px; flex-shrink: 0`
- **右栏溢出**：AlarmCenter 改为 `flex: 1 1 0; overflow: hidden`，内部表格独立滚动
- **ContinuousAlerts 溢出**：加 `max-height: 220px; overflow: hidden`，内部列表滚动
- **DecisionSupport 溢出**：加 `.decision-body` 包装层，内容区滚动，操作按钮固定底部
- **V 字形装饰**：尝试后移除，恢复 `border-radius: 14px`

---

## Phase 6：集成预测模型服务（ensemble_docker）

### 背景
模型设计者提供了 `ensemble_docker` 微服务（端口 8000），基于 DLinear PCA Large 集成模型，支持：
- 输入 96 步历史传感器数据（25个特征字段）
- 输出未来 24 步 RTO 出口浓度预测
- **XAI 增量归因分析**：瀑布图数据（baseline → target，各特征/特征组贡献度）

### 集成改动

#### `admin/backend/config.py`
- 新增 `ensemble_base_url: str = "http://127.0.0.1:8000"` — 集成模型服务地址
- 新增 `ensemble_timeout: float = 10` — 模型推理超时（比普通请求更长）

#### `admin/backend/services/vocs_proxy.py`
- 新增 `_row_to_feature_values(row)` — 将 CSV 行转为 25 个 float 数组
- 新增 `call_ensemble_predict(history)` — 加载 96 步历史，格式化为 `{data_sequence: [{timestamp, feature_values[25]}]}`，POST 到 ensemble `/predict`
- 修改 `get_dashboard_overview()` — 并行调用 ensemble 预测，优先使用集成模型结果（含归因数据），fallback 到 vocs_server 或本地估算。返回新增 `attribution` 字段
- 修改 `get_alert_diagnosis()` — 当 ensemble 归因可用时，返回真实 `feature_contributions`（feature/group/ratio/contribution）和 `groupContributions`，替代之前的硬编码 mock

#### `admin/backend/routers/dashboard.py`
- 新增 `POST /api/dashboard/predict` — 按需触发集成模型预测，返回完整响应
- 新增 `GET /api/dashboard/ensemble-health` — 检测集成模型服务连通性

### 数据流架构

```
admin 前端 ──→ admin 后端 (8003)
                ├──→ ensemble_docker (8000) POST /predict
                │     └─ predictions[24] + incremental_attribution
                ├──→ vocs_server (8001) GET /status, /sensor-data, /predictions, /alerts
                │     └─ SSE /events 实时推送
                └──→ 本地 CSV fallback
```

### 预测数据源优先级
1. **ensemble_docker**（端口 8000）— DLinear PCA 集成模型 + XAI 归因
2. **vocs_server**（端口 8001）— Mamba3-SISO 模型
3. **本地 CSV 估算** — 基于历史均值 + 趋势的简单 fallback

### 归因数据结构（incremental_attribution）
```json
{
  "baseline": 35.0,
  "target": 70.80,
  "total_increment": 35.80,
  "feature_contributions": [
    {"feature": "coating_conc", "group": "废气源与环境组", "ratio": 0.24, "contribution": 8.59},
    {"feature": "rotor_speed", "group": "转轮浓缩系统", "ratio": 0.10, "contribution": 3.58}
  ],
  "group_contributions": [
    {"group": "废气源与环境组", "contribution": 28.99},
    {"group": "转轮浓缩系统", "contribution": 5.01},
    {"group": "RTO焚烧系统", "contribution": 1.80}
  ]
}
```

### 启动顺序
1. `ensemble_docker` (端口 8000) — `docker compose up` 或 `uvicorn app:app --port 8000`
2. `vocs_server` (端口 8001) — 可选，提供 SSE 实时推送
3. `admin backend` (端口 8003) — `uvicorn main:app --port 8003`
4. `admin frontend` — `cd admin/frontend && npm run dev`

---

## 文件清单

### 前端 `admin/frontend/src/`

| 文件 | 用途 |
|------|------|
| `main.ts` | 应用入口，注册插件 |
| `App.vue` | 根组件 |
| `style.css` | 暗黑工业主题 |
| `router/index.ts` | 路由 + 登录守卫 |
| `api/client.ts` | 管理端后端 Axios 实例 |
| `api/vocsClient.ts` | ML 服务 Axios 实例 |
| `api/sse.ts` | SSE 连接管理 |
| `stores/auth.ts` | 认证状态 |
| `stores/dashboard.ts` | 大屏状态 |
| `stores/alerts.ts` | 告警状态 |
| `stores/sensors.ts` | 传感器状态 |
| `utils/sensorMeta.ts` | 传感器中文标签/单位映射 |
| `layouts/DashboardLayout.vue` | 三栏布局 |
| `components/layout/HeaderBar.vue` | 顶栏 |
| `components/dashboard/VocsTrendChart.vue` | VOCs 趋势折线图 |
| `components/dashboard/EquipmentStatusChart.vue` | 设备状态环形图 |
| `components/dashboard/AnomalyHeatmap.vue` | 异常热力图 |
| `components/dashboard/AlarmCenter.vue` | 实时告警中心 |
| `components/dashboard/ContinuousAlerts.vue` | 持续监控区 |
| `components/dashboard/DecisionSupport.vue` | 决策支持面板 |
| `components/dashboard/FactoryScene.vue` | 3D 工厂场景 |
| `views/Login.vue` | 登录页 |
| `views/AdminDashboard.vue` | 管理大屏 |

### 后端 `admin/backend/`

| 文件 | 用途 |
|------|------|
| `main.py` | FastAPI 入口 (端口 8003) |
| `config.py` | 配置（JWT、vocs_server、ensemble 地址） |
| `routers/auth.py` | 登录认证 |
| `routers/dashboard.py` | 大屏数据 + 集成预测 + ensemble 健康检查 |
| `routers/alerts.py` | 告警管理 + 诊断 |
| `routers/users.py` | 用户管理 |
| `services/vocs_proxy.py` | ML 服务代理（vocs_server + ensemble_docker） |
