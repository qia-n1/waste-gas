# 数据聚合与推送模块 API 与模块设计报告

## 1. 文档目的

本文档描述 admin 后端中数据聚合与推送模块的 API 设计与模块设计。

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

## 3. API 设计

### 3.1 接口 1：实时 JSON 上报

- 路径：`POST /api/data-fusion/ingest/{device_id}`
- 功能：接收实时 JSON 数据并写入设备 CSV。
- 处理逻辑：
  1. 兼容以下 payload 结构：`records[]`、`data{}`、`record{}`、直接对象。
  2. 调用预处理与标准化逻辑。
  3. 写入 `{device_id}.csv`。

#### 请求示例

```json
{
  "timestamp": "2026-04-20T12:00:00Z",
  "ambient_temp": 21.5,
  "rto_out_conc": 46.2
}
```

#### 成功响应示例

```json
{
  "status": "ok",
  "device_id": "device_A",
  "written": 1
}
```

#### 失败响应

- `400`：无有效记录。

### 3.2 接口 2：实时/批量文件上传

- 路径：`POST /api/data-fusion/upload/{device_id}`
- 功能：接收文件并解析后写入设备 CSV。
- 支持格式：`.csv`, `.json`, `.jsonl`, `.txt`, `.xlsx/.xlsm/.xltx/.xltm`
- 处理逻辑：
  1. 读取文件内容。
  2. 按扩展名解析为记录数组。
  3. 调用预处理与标准化逻辑。
  4. 写入 `{device_id}.csv`。

#### 成功响应示例

```json
{
  "status": "ok",
  "device_id": "device_A",
  "filename": "upload_payload.csv",
  "written": 10
}
```

#### 失败响应

- `400`：空文件。
- `400`：不支持文件类型。
- `400`：解析后无记录。

### 3.3 接口 3：历史 CSV 上传与聚合重建

- 路径：`POST /api/data-fusion/upload-history-csv`
- 功能：上传历史数据 CSV，生成新的历史快照文件 `device_history_{timestamp}.csv`，并触发历史聚合重建。
- 输入限制：仅支持 `.csv`。
- 处理逻辑：
  1. 解析 CSV 记录。
  2. 每次上传生成新的 `device_history_{timestamp}.csv`。
  3. 触发重建：动态锁定本次上传生成的历史文件，以最大时间戳向前按 15 分钟分桶聚合。
  4. 将聚合结果按时间戳增量插入 `15.csv`，同时间戳更新，整体保持排序。
  5. 聚合函数必须显式传入本次 `history_file`；未传入直接报错，不进行自动选择与回退，避免重复计算。

#### 成功响应示例

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

#### 失败响应

- `400`：文件扩展名不是 csv。
- `400`：空文件。
- `400`：解析后无记录。

## 4. 模块设计

### 4.1 路由层

文件：`admin/backend/routers/data_fusion.py`

职责：
1. 接收请求并做输入基础校验。
2. 调用服务层。
3. 返回统一字典响应。

### 4.2 服务层

文件：`admin/backend/services/data_fusion.py`

职责分块：
1. 解析模块：`parse_upload_file`（多格式文件解析）。
2. 标准化模块：`_normalize_record`（时间戳、别名、数值转换）。
3. 存储模块：`append_device_records` 与 `save_history_snapshot`（实时追加与历史快照写入）。
4. 历史聚合模块：`_rebuild_aggregate_from_history_csv`。
5. 实时聚合模块：`_window_average`。
6. 推送准备模块：`_build_predict_payload`（96 步序列构造、补零、缺失回填）。
7. 调度模块：`_scheduler_loop`（周期触发聚合与推送）。

### 4.3 配置模块

文件：`admin/backend/config.py`

关键配置：
1. `AGGREGATION_GRANULARITY_MINUTES`：聚合粒度（默认 15）。
2. `INGEST_DATA_DIR`：CSV 持久化目录。
3. `VOCS_BASE_URL`：模型服务地址（用于推送请求）。
4. `FRONTEND_PUSH_URL`：前端回调地址（可选，未配置则不回调）。
5. `FRONTEND_PUSH_TIMEOUT`：前端回调超时（秒）。

## 5. 数据预处理设计

### 5.1 时间戳标准化

1. 支持字符串格式：
   1. `%Y-%m-%d %H:%M:%S`
   2. `%Y-%m-%d %H:%M`
   3. `%Y-%m-%dT%H:%M:%S`
   4. `%Y-%m-%dT%H:%M:%S%z`
   5. ISO 8601（含 `Z`）
2. 支持 Unix 秒和毫秒时间戳。
3. 输出格式：`%Y-%m-%d %H:%M:00`。

### 5.2 字段映射与容错

1. 按 `SENSOR_FIELDS` 作为目标标准字段集合。
2. 使用 `FIELD_ALIASES` 兼容异构字段命名。
3. 数值字段通过 `_to_float` 转换；非法值容错。
4. 稀疏字段可为空，保证弱耦合接入。

### 5.3 CSV 持久化策略

1. 每个设备独立文件 `{device_id}.csv`。
2. 写入前合并已有字段与新字段并集，避免字段丢失。
3. 以追加语义写入，不覆盖设备历史数据。
4. 历史上传接口（接口 3）采用快照写入语义：每次上传生成新的 `device_history_{timestamp}.csv`，避免覆盖历史批次数据。

## 6. 聚合与推送设计

### 6.1 历史数据聚合（接口 3 触发）

1. 输入：本次上传生成的 `device_history_{timestamp}.csv`。
2. 以 `max(timestamp)` 为锚点，向前按 15 分钟分桶。
3. 每桶每维度取均值。
4. 结果增量并入 `15.csv`：同时间戳更新，不同时间戳插入，并保持全局时间排序。

### 6.2 实时数据聚合（调度触发）

1. 每个周期计算 `(now-15min, now]` 窗口内所有设备数据均值。
2. 产出一行聚合数据，追加写入 `15.csv`（或当前粒度文件）。

### 6.3 推送前数据构造（模型边界）

1. 从聚合文件读取最近 96 条数据。
2. 不足 96 条时左侧补零。
3. 缺失字段使用上次观测值回填。
4. 输出结构：`{"data_sequence": [{"timestamp": ..., "feature_values": [...]}, ...]}`。

### 6.4 时间桩与阶段耗时统计

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

## 7. 运行时状态与可观测性

状态项：
1. `running`：调度器状态。
2. `last_aggregation_timestamp`：最近聚合时间。
3. `last_model_push_timestamp`：最近推送时间。
4. `last_model_push_ok`：最近推送是否成功。
5. `last_model_push_message`：最近推送摘要信息。
6. `last_frontend_push_timestamp`：最近前端回调时间。
7. `last_frontend_push_ok`：最近前端回调是否成功。
8. `last_frontend_push_message`：最近前端回调摘要信息。
9. `last_history_upload_file`：最近一次参与历史聚合的历史快照文件名。

## 8. 异常处理策略

1. 输入异常：返回 `400`。
2. 不支持文件类型：返回 `400`。
3. 聚合无有效数据：返回 `ok=false` 与提示信息。
4. 模型推送失败：记录运行时状态，不影响服务存活。

## 9. 验收口径

### 9.1 实时上传验收

1. 接口 1/2 返回 `status=ok`。
2. `written` 与有效记录数一致。
3. 对应设备 CSV 新增记录可查。

### 9.2 历史上传验收

1. 接口 3 返回 `aggregation.ok=true`。
2. 返回中 `history_file` 为新生成的 `device_history_{timestamp}.csv`。
3. `aggregation.written > 0`。
4. `15.csv` 时间有序且为增量合并结果（可观测 `inserted/updated` 变化）。

### 9.3 预处理验收

1. 混合时间格式可统一落盘。
2. 字段别名可正确映射。
3. 缺失字段不阻塞写入。

### 9.4 定时链路验收

1. 调度器自动触发后，`last_model_push_ok=true`。
2. 若配置回调地址，`last_frontend_push_ok=true`。
3. 聚合产物文件与状态时间戳一致。

## 10. 后续实现建议

1. 引入统一响应 envelope（`code/message/request_id/data`）。
2. 为历史上传增加幂等键（批次号或文件哈希）。
3. 增加接口级自动化测试（包含格式异常与边界时间戳）。
