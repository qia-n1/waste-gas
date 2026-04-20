# 数据聚合与推送模块 API 与模块设计报告

## 1. 文档目的

本文档按工程处理流程描述 admin 后端中数据聚合与推送模块的实现逻辑，重点回答“数据如何进入、如何处理、如何输出”。

范围约束如下：
1. 前端边界为设备输入（包含设备实时 JSON 输入与文件上传输入）。
2. 模型端边界为不包含模型推理算法本身（仅覆盖推理前数据构造与推送调用）。

## 2. 边界与范围

### 2.1 系统边界

1. 输入边界（含）：
   1. 设备实时数据 JSON 上报。
   2. 设备批量文件上传（csv/json/jsonl/txt/xlsx）。
   3. 历史数据 csv 上传。
2. 输出边界（不含模型推理算法）：
   1. 设备数据标准化后持久化到 `admin/backend/data_fusion/*.csv`。
   2. 聚合输出到 `N.csv`（默认 `15.csv`）。
   3. 构造推送 payload 并调用模型服务 `/predict`（不描述模型内部处理）。

### 2.2 API 范围

1. `POST /api/data-fusion/ingest/{device_id}`
2. `POST /api/data-fusion/upload/{device_id}`
3. `POST /api/data-fusion/upload-history-csv`

## 3. 工程处理流程（总览）

系统包含三条核心处理链路：
1. 实时接收链路（接口 1/2）：写入设备 CSV，等待调度器做窗口聚合。
2. 历史接收链路（接口 3）：生成历史快照文件并立即触发历史聚合。
3. 定时调度链路（后台）：周期执行实时窗口聚合、模型推送、可选前端回调。

统一处理原则：
1. 先标准化、再持久化、后聚合。
2. 历史链路与实时链路隔离，避免互相污染统计窗口。
3. 历史聚合必须显式指定本次历史文件，避免重复计算。

## 4. 流程一：实时接收处理

### 4.1 触发入口

1. 接口 1：`POST /api/data-fusion/ingest/{device_id}`（JSON）。
2. 接口 2：`POST /api/data-fusion/upload/{device_id}`（文件）。

### 4.2 处理步骤

1. 输入解析。
  1. 接口 1：兼容 `records[]`、`data{}`、`record{}`、直接对象。
  2. 接口 2：按扩展名解析 csv/json/jsonl/txt/xlsx。
2. 数据标准化。
  1. 时间戳统一为 `%Y-%m-%d %H:%M:00`。
  2. 字段按标准字段集合映射，支持别名。
  3. 非法数值容错，稀疏字段允许为空。
3. 持久化写入。
  1. 目标文件为 `{device_id}.csv`。
  2. 按追加语义写入。
4. 返回写入结果（`status/device_id/written`）。

### 4.3 输出产物

1. 设备原始标准化数据：`admin/backend/data_fusion/{device_id}.csv`。
2. 调度器后续会基于该文件参与实时聚合。

## 5. 流程二：历史接收处理

### 5.1 触发入口

1. 接口：`POST /api/data-fusion/upload-history-csv`。
2. 输入限制：仅支持 `.csv`。

### 5.2 处理步骤

1. 解析上传 CSV。
2. 生成本次历史快照文件：`device_history_{timestamp}.csv`。
3. 显式调用历史聚合函数，并传入本次 `history_file`。
4. 以快照文件最大时间戳为锚点，按 15 分钟分桶。
5. 各桶按维度计算均值。
6. 与现有 `15.csv` 执行增量合并：
  1. 同时间戳：更新。
  2. 新时间戳：插入。
  3. 全量按时间排序写回。

### 5.3 关键约束

1. 历史聚合函数未传 `history_file` 时直接报错。
2. 禁止自动选择最新历史文件，避免重复聚合。

### 5.4 输出产物

1. 历史快照文件：`device_history_{timestamp}.csv`。
2. 增量更新后的聚合文件：`15.csv`。
3. 聚合统计摘要：`written/inserted/updated/aggregate_total`。

## 6. 流程三：定时调度处理（后台）

### 6.1 触发机制

1. 应用启动后启动调度器循环。
2. 每 `AGGREGATION_GRANULARITY_MINUTES` 分钟执行一次。

### 6.2 处理步骤

1. 窗口聚合：计算 `(now-grain, now]` 区间均值。
2. 过滤源文件：
  1. 排除聚合文件 `N.csv`。
  2. 排除历史快照文件 `device_history_*.csv`（以及 legacy 历史文件）。
3. 将窗口聚合结果追加写入 `N.csv`。
4. 从聚合文件构造模型输入 payload（固定 96 步，不足补零）。
5. 调用模型服务 `/predict`。
6. 若配置 `FRONTEND_PUSH_URL`，将结果回调给前端中转服务。
7. 更新运行状态字段（最近聚合、推送成功标记、消息等）。

### 6.3 输出产物

1. 实时聚合文件：`N.csv`（默认 `15.csv`，测试时可改 1 分钟）。
2. 模型请求结果状态。
3. 可选前端回调结果状态。

## 7. API 设计

### 7.1 实时 JSON 上报

- 路径：`POST /api/data-fusion/ingest/{device_id}`。
- 功能：接收 JSON，标准化后追加写入设备文件。

成功响应示例：

```json
{
  "status": "ok",
  "device_id": "device_A",
  "written": 1
}
```

### 7.2 实时/批量文件上传

- 路径：`POST /api/data-fusion/upload/{device_id}`。
- 功能：接收文件，解析后标准化并追加写入设备文件。

成功响应示例：

```json
{
  "status": "ok",
  "device_id": "device_A",
  "filename": "upload_payload.csv",
  "written": 10
}
```

### 7.3 历史上传与聚合重建

- 路径：`POST /api/data-fusion/upload-history-csv`。
- 功能：生成历史快照文件并基于该文件做历史聚合增量并入。

成功响应示例：

```json
{
  "status": "ok",
  "device_id": "device_history",
  "history_file": "device_history_20260420_120001_123456.csv",
  "filename": "history.csv",
  "written": 1000,
  "aggregation": {
   "ok": true,
   "message": "Merged aggregate rows from device_history_20260420_120001_123456.csv",
   "history_file": "device_history_20260420_120001_123456.csv",
   "written": 68,
   "inserted": 40,
   "updated": 28,
   "aggregate_total": 560,
   "source_rows": 1000,
   "max_timestamp": "2026-04-20 12:45:00"
  }
}
```

## 8. 模块职责映射

### 8.1 路由层

文件：`admin/backend/routers/data_fusion.py`

职责：
1. 请求校验与错误映射。
2. 调用服务层流程函数。
3. 返回流程结果。

### 8.2 服务层

文件：`admin/backend/services/data_fusion.py`

职责：
1. 解析：`parse_upload_file`。
2. 标准化：`_normalize_record`。
3. 实时持久化：`append_device_records`。
4. 历史快照写入：`save_history_snapshot`。
5. 历史聚合：`_rebuild_aggregate_from_history_csv`。
6. 聚合增量合并：`_merge_aggregate_rows_incremental`。
7. 实时窗口聚合：`_window_average`。
8. 推送前构造：`_build_predict_payload`。
9. 调度：`_scheduler_loop`。

## 9. 运行状态与可观测性

状态项：
1. `running`。
2. `last_aggregation_timestamp`。
3. `last_history_upload_file`。
4. `last_model_push_timestamp`。
5. `last_model_push_ok`。
6. `last_model_push_message`。
7. `last_frontend_push_timestamp`。
8. `last_frontend_push_ok`。
9. `last_frontend_push_message`。

## 10. 异常处理

1. 输入异常：返回 `400`。
2. 文件类型不支持：返回 `400`。
3. 历史聚合未传 `history_file`：返回业务失败（`ok=false`）。
4. 聚合窗口无数据：返回业务失败（`ok=false`）。
5. 模型推送失败：记录状态，不中断服务。

## 11. 时间损耗统计

调度主链路（一次周期）记录以下阶段耗时，单位 ms：
1. `aggregate_window_ms`：窗口聚合计算耗时。
2. `append_aggregate_csv_ms`：聚合结果写文件耗时。
3. `build_predict_payload_ms`：构建推理输入耗时。
4. `model_push_ms`：模型端请求耗时。
5. `frontend_push_ms`：前端回调请求耗时。
6. `total_ms`：一次调度总耗时。

实测样例（联调）：
1. `aggregate_window_ms=2.007`
2. `append_aggregate_csv_ms=0.163`
3. `build_predict_payload_ms=0.315`
4. `model_push_ms=22.673`
5. `frontend_push_ms=10.620`
6. `total_ms=35.794`
