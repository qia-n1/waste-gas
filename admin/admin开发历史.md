# 管理端开发历史

## 项目概述

气盾卫士 - 废气综合管理平台 管理端（admin），独立于同事的用户端（`frontend/` + `backend/`），在 `admin/` 目录下搭建独立前后端。

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
- 居中标题 "气盾卫士 - 废气综合管理平台"
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

---

## Phase 7：模型服务联调与前端联动

### 环境修复
- 安装 PyTorch CPU 版本 (`torch 2.8.0+cpu`)，解决两个模型服务的 `ModuleNotFoundError: No module named 'torch'`
- 修复 ensemble_docker `api_src/config.py` Python 3.9 兼容性：`tuple[...] | tuple[()]` → `Union[Tuple[...], Tuple[()]]`，添加 `from __future__ import annotations`
- 创建缺失的 `api_src/schemas.py`（`SensorData` Pydantic 模型），修复 `features.py` 导入错误
- 修复 Vite 代理端口：`/api` 从 `localhost:8002` → `localhost:8003`

### 前端改造

#### EquipmentStatusChart → 细分指标贡献度
- 标题从"设备状态分布"改为"细分指标贡献度"（当有 attribution 数据时）
- 饼图数据来源改为 `feature_contributions`，比例按 `ratio` 设置
- 图例显示 feature 名称 + 百分比（如 `coating_flow 81%`）
- 中心数字从"在线设备"改为"预测均值"（`attribution.target`）
- 按 group 分色：废气源与环境组(青)、转轮浓缩系统(琥珀)、RTO焚烧系统(红)
- 当 ensemble 不可用时 fallback 回原始设备状态饼图

#### FactoryScene 超标红色闪烁
- 新增 `isExceedWarning` prop
- 当 `alertLevel !== "normal"` 时，园区工艺场景边框添加 `warning-pulse` CSS 动画
- 动画效果：红色边框 + box-shadow 渐变闪烁（2s 周期，ease-in-out）

#### VocsTrendChart 高度修复
- 卡片从 `height: 208px` 改为 `flex: 0 0 380px`，图表区域充足
- Y 轴改为 `min: 0, splitNumber: 4, minInterval: 10`，低数据时刻度更合理

### 数据链路验证
- `predictionType: DLinear-PCA-Ensemble`（非 Fallback）
- `confidence: 88%`
- `attribution.feature_contributions` 完整返回（coating_flow 81.2% 主因）
- `group_contributions` 三组聚合正常
- 预测序列 24 步，值域 33.0~38.6 mg/m³

### 启动脚本
- 创建 `admin/start_admin.bat` 一键启动全部 4 个服务

---

## Phase 8：RAG 处置方案接入（基础）

### 背景
队友在 `admin/backend/rag/` 下提交了基于 BGE-large-zh 嵌入 + DeepSeek LLM 的 SOP 检索增强生成模块，但未接入告警诊断流程。本阶段把 RAG 卡片挂到 `/api/alerts/{id}/diagnosis` 响应上。

### 后端改造
- **`admin/backend/rag/rag_service.py`**
  - 修正模型路径 bug：`../../models/bge-large-zh` → `models/bge-large-zh`（相对项目根）
  - 删掉顶层多余的 `SentenceTransformer` 加载，交给 `SimpleVectorDB` 统一管理
- **`admin/backend/services/vocs_proxy.py`**
  - 采用 lazy-import + 失败降级：`try: from rag.rag_service import ...` 失败时置 `RAG_AVAILABLE = False`，不阻塞服务启动
  - 日志统一 ASCII 前缀（`[RAG] module loaded` / `[RAG] module unavailable`），避免 Windows GBK 控制台 `UnicodeEncodeError`
  - 新增 `_invoke_rag_diagnosis(vocs, shap_reason, shap_score)`：构造 RAG 入参 + `asyncio.to_thread` 包装同步调用，避免阻塞事件循环
  - `get_alert_diagnosis()` 在构造 attribution 后追加 RAG 卡片字段

### 前端改造
- **`admin/frontend/src/types/dashboard.ts`**
  - 新增 `RagCard` 接口（title / suggestionShort / sopSteps / safetyRedline / standard / level / reason / version / generatedAt / fromCache）
  - `DiagnosisResponse` 扩展 `ragCard?: RagCard | null`
- **`admin/frontend/src/components/dashboard/DecisionSupport.vue`**
  - 新增 `ragCard` prop；标题 tag + standard + suggestion_short + SOP 有序列表 + 安全红线横幅
  - CSS 按 level 切换 `--accent-amber` / `--accent-red` / `--accent-cyan`
- **`admin/frontend/src/views/AdminDashboard.vue`**
  - 新增 `decisionRagCard` computed，注入 `<DecisionSupport :rag-card="decisionRagCard">`

### 功能测试
- RAG 模块可用 / 不可用两条分支均通过（fallback 不崩溃）
- SOP 步骤、safety_redline、standard 字段在 UI 正常渲染
- Windows 控制台无乱码

---

## Phase 9：RAG 方案落库（管理端持久化 + 一线端共享）

### 架构决策
- 告警表 `wg_alerts` + 方案表 `wg_alert_rag_plans` 均走共享云库（TimescaleDB @ `98.142.241.155:5432/aqimonitor`）
- **管理端**：运行 RAG → 生成方案 → 写入 `wg_alert_rag_plans`（缓存优先：同告警已有方案直接返回）
- **一线端**：只读 `wg_alert_rag_plans`（本期不动），自己连 AI API 做问答；**不再部署 RAG**
- 多版本策略：同 `alert_id` 可多次重新生成，旧版 `is_current=false`，`version` 单调递增

### 数据库迁移
- **新建** `admin/backend/migrations/001_wg_alert_rag_plans.sql`（已应用到云库）
  - 19 字段表：`id / alert_id FK→wg_alerts(ON DELETE CASCADE) / version / title / suggestion_short / sop_steps JSONB / safety_redline / standard / level / reason / top_feature / top_feature_label / shap_score / current_vocs / model_name / confidence / generated_by / generated_at / is_current`
  - 唯一键 `(alert_id, version)`；两个索引：当前版本部分索引 + 按生成时间倒序索引

### 后端新增模块
- **`admin/backend/config.py`**：新增 7 个 `PG_*` 配置字段（host/port/db/user/password/pool_min/pool_max/connect_timeout）
- **`admin/backend/services/db.py`**（新文件）
  - `ThreadedConnectionPool` + `RealDictCursor`
  - `init_pool() / close_pool() / is_ready() / health_check()`
  - `@contextmanager cursor(dict_rows=False)` 自动 commit/rollback/putconn
- **`admin/backend/services/rag_plans.py`**（新文件）
  - `PLAN_COLUMNS` 定义 19 列顺序
  - `get_current_plan(alert_id)` / `list_plans(alert_id, limit)`
  - `upsert_plan(alert_id, rag_card, context, generated_by)`：先算 `MAX(version)+1`，旧版置 `is_current=FALSE`，插入新行 `RETURNING *`
  - `delete_plans_for_alert(alert_id)`、`parse_alert_id(str) -> int | None`（非数字 ID 如 `WATCHDOG-xxx` 返回 None）
- **`admin/backend/main.py`**：lifespan 中调用 `db.init_pool()` + `db.health_check()`；失败不阻塞启动；关闭时 `db.close_pool()`
- **`admin/backend/requirements.txt`**：新增 `psycopg2-binary==2.9.10`

### `vocs_proxy.get_alert_diagnosis()` 缓存优先重构
1. 构建 overview + contributors（不变）
2. `parse_alert_id()` → `int | None`
3. 若 int：`get_current_plan(aid)` 命中直接返回 `fromCache=True`
4. 未命中 + `RAG_AVAILABLE` + attribution 齐全：`asyncio.to_thread(_invoke_rag_diagnosis, ...)` → `upsert_plan(...)` → 返回 `fromCache=False`
5. 新增 `_plan_row_to_card(plan)` / `_raw_to_card(raw)` 两个 mapper
6. 本地 fallback 告警（`WATCHDOG-xxx` / `LOCAL-FALLBACK-xxx`）跳过落库，直接返回实时 RAG 结果

### 集成测试（真实云库）
5 项全部通过：
1. 连接池初始化 + `health_check()` OK
2. CRUD round-trip：`upsert_plan` → `get_current_plan` → version 自增 → `list_plans` 倒序
3. `parse_alert_id` 边界：数字 / `WATCHDOG-123` / `LOCAL-FALLBACK-xxx` / 空串
4. 诊断接口端到端：首调 `version=1 fromCache=False`，二调 `version=1 fromCache=True`，`WATCHDOG-xxx` 永远 `fromCache=False`
5. 连接池关闭无残留连接
- 测试后用 `delete_plans_for_alert(88)` 清理痕迹

### 前端兼容
- `RagCard.version / generatedAt / fromCache` 字段已在 Phase 8 声明，UI 无需改动即可显示缓存标记

---

## Phase 10：园区工艺场景 标签精简

### 需求
3D 工厂可视化底图上同时存在两类浮层标签：
- **厂房名**（喷涂生产厂房 / 转轮吸附厂房 / RTO 主处理厂房 / 公辅燃烧区 / 排口烟囱区 / 监测附属区）— 对应真实工艺单元，保留
- **通用点位标签**（监测点位 / 关键设备 / 1号排口）— 来自 mock 的 `factoryNodes`，与实际工艺单元重复且语义模糊，按需求移除

### 改造 `admin/frontend/src/components/dashboard/FactoryScene.vue`
- 删除 `labelPositions` computed（映射 `props.nodes` 到屏幕坐标）
- 删除模板中 `<div v-for="node in labelPositions" class="node-tag">` 整块
- 删除未再引用的 `.node-tag` / `.node-tag--active` / `.node-pin` CSS
- 从 `vue` 导入去掉不再使用的 `computed`
- **保留** `buildingLabels` / `projectedBuildingLabels` / `.building-tag*`（厂房名继续显示）
- **保留** `hoveredNodeId` + 3D marker 高亮逻辑（`markerMeshes` / `pulseMeshes` 仍响应射线拾取，颜色区分正常/预警/告警）

### 效果
- 3D 场景下方不再悬浮"监测点位 / 关键设备 / 1号排口"三条浅色文字
- 状态仍由 3D 球形 marker 的颜色 + 脉冲光圈传达，语义更贴合工艺图
