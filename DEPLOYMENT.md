# 气盾卫士 - 多源化工废气智能治理系统部署手册

## 项目概述

### 系统简介

智洁园区废气综合管理平台是一套面向工业园区废气治理的实时监测、智能预警与辅助决策系统。系统通过对现场 RTO（蓄热式热氧化炉）、转轮吸附装置、喷涂工艺段等关键工段的多源传感器数据进行秒级采集与分钟级预测，结合 AI 模型输出未来 6 小时 VOCs 浓度趋势、异常根因归因与 RAG（检索增强生成）处置建议，支撑运行人员、运维人员与管理人员三级协同处置。

### 子系统构成

| 子系统 | 目录 | 默认端口 | 职责 |
| --- | --- | --- | --- |
| ML 推理服务 | `./`（根目录） | `8001` | 传感器数据接入、Seq2Seq 预测、SSE 实时推送 |
| 管理端后端 | `admin/backend/` | `8002` | 管理大屏聚合 API、鉴权、RAG、告警管理 |
| 管理端前端 | `admin/frontend/` | `5173`（dev） | Vue3 + Three.js 可视化大屏 |
| 用户端后端 | `client-backend/` | `8002`（当前实现） | 面向园区用户 REST API |
| 用户端前端 | `client-frontend/` | `8080`（Docker H5） | uni-app H5/小程序客户端 |
| PostgreSQL | TimescaleDB 容器 | `5432` | 历史告警、工单、RAG 计划持久化 |
| Redis | Redis 7 容器 | `6379` | 热点缓存、会话/实时辅助 |
| Nginx | `client-frontend` 镜像内 | `80`（映射 `8080`） | 静态资源托管、API 反向代理 |

> 说明：仓库中用户端后端当前监听 `8002`。如需与管理端并行部署，建议将用户端映射改为 `8003` 或使用独立主机。

### 数据流概览

现场 PLC / DCS -> `POST /sensor-data` -> `vocs_server (8001)` -> `SSE /events` -> `admin-backend (8002)` -> 管理端大屏与告警链路。

用户端链路：`client-frontend` -> `client-backend /api/v1/*` -> SQLite 或 PostgreSQL + Redis。

## 环境配置要求

### 硬件最低配置

| 项目 | 最低配置（开发/演示） | 推荐配置（生产） |
| --- | --- | --- |
| CPU | 4 核 x86_64 | 8 核及以上（建议支持 AVX2） |
| 内存 | 8 GB | 16 GB 及以上 |
| 硬盘 | 40 GB SSD | 100 GB SSD（建议 RAID1） |
| GPU | 非必须 | 可选 NVIDIA T4/A10（推理加速） |
| 网络 | 千兆内网 | 千兆内网 + 公网备用链路 |

### 操作系统与基础软件

- 操作系统：Ubuntu 22.04 LTS / Rocky Linux 9 / CentOS 7.9；Windows 10/11 仅建议本地开发
- Docker Engine：`>= 24.0`
- Docker Compose：`>= v2.20`
- Python：`3.10`（ML 服务），`3.11`（管理端后端）
- Node.js：`>= 18.18`，推荐 `20.x LTS`
- Nginx：`>= 1.24`（非 Docker 托管场景）
- PostgreSQL：14/15（推荐 `timescale/timescaledb:latest-pg15`）
- 时区：`Asia/Shanghai`

> 注意：根目录 `requirements.txt` 使用 `torch==2.7.0`，`admin/backend/requirements.txt` 使用 `torch==2.3.1`。二者应使用独立虚拟环境或独立容器，不要安装到同一 venv。

## 依赖包清单

### ML 推理服务（`requirements.txt`）

- `fastapi==0.104.1`
- `uvicorn==0.24.0`
- `torch==2.7.0`
- `numpy>=1.26.0`
- `pandas>=2.0.3`
- `pydantic==2.4.0`
- `requests==2.31.0`
- `sseclient==0.0.27`
- `scikit-learn==1.7.0`

### 管理端后端（`admin/backend/requirements.txt`）

- `fastapi==0.116.1`
- `uvicorn==0.35.0`
- `httpx==0.28.1`
- `pyjwt==2.10.1`
- `pydantic==2.11.7`
- `python-dotenv==1.2.2`
- `sentence-transformers==2.2.2`
- `torch==2.3.1`
- `openai==2.31.0`
- `numpy==1.26.4`
- `pandas==3.0.2`
- `pypdf==6.10.0`
- `python-docx==1.2.0`

### 管理端前端（`admin/frontend/package.json`）

运行依赖：

- `vue`, `vue-router`, `pinia`, `axios`
- `element-plus`, `@element-plus/icons-vue`
- `echarts`, `vue-echarts`
- `three`, `dayjs`

开发依赖：

- `vite`, `typescript`, `vue-tsc`, `@vitejs/plugin-vue`

### 用户端前端（`client-frontend/package.json`）

运行依赖：

- `@dcloudio/uni-components`
- `vue`

开发依赖：

- `@dcloudio/uni-helper-json`
- `@dcloudio/uni-mp-weixin`
- `@dcloudio/vite-plugin-uni`
- `@vitejs/plugin-vue`
- `cross-env`
- `vite`

## Docker 部署步骤

### 目录准备

```bash
git clone <your-repo-url> waste-gas
cd waste-gas
```

### 编写/确认环境变量

在根目录创建 `.env`（禁止提交到 Git）：

```env
# 管理端后端
ADMIN_JWT_SECRET=please-change-me-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=YourStrongPassword!2026
ADMIN_TOKEN_EXPIRE_MINUTES=120

# 数据库
PG_HOST=postgres
PG_PORT=5432
PG_DB=aqimonitor
PG_USER=team
PG_PASSWORD=please-change-db-password

# ML 服务
MODEL_PATH=models/vocs_seq2seq_v2_best.pth
SCALER_PATH=models/vocs_scalers_v2.pkl
CSV_PATH=vocs_realtime_data/vocs_realtime_data.csv
TZ=Asia/Shanghai

# RAG（可选）
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
```

### 一键启动（根目录 ML + 基础设施）

仓库根目录已有 `docker-compose.yml`，默认提供：

- `vocs-server`（8001）
- `postgres`（profile: infra）
- `redis`（profile: infra）

```bash
docker compose build
docker compose up -d vocs-server
docker compose --profile infra up -d
docker compose ps
docker compose logs -f vocs-server
```

### 用户端（`client-backend` + `client-frontend`）部署

用户端使用独立编排文件 `docker-compose.client.yml`：

```bash
docker compose -f docker-compose.client.yml up -d --build
docker compose -f docker-compose.client.yml ps
docker compose -f docker-compose.client.yml logs -f backend
docker compose -f docker-compose.client.yml logs -f frontend
```

默认访问地址：

- 用户端前端：`http://<服务器IP>:8080`
- 用户端后端健康检查：`http://<服务器IP>:8002/api/v1/health`

### 管理端扩展部署（推荐）

当前仓库存在 `admin/backend` 与 `admin/frontend` 代码。生产建议为管理端增加独立镜像与 compose 服务（可合并到根目录 `docker-compose.yml`）。

建议新增服务：

- `admin-backend`：映射 `8002:8002`，依赖 `vocs-server` 与 `postgres`
- `admin-frontend`：映射 `5173:80`，依赖 `admin-backend`

## 启动顺序与健康检查

1. 启动数据库与缓存：`docker compose --profile infra up -d postgres redis`
2. 检查 PostgreSQL 就绪：`docker compose logs postgres`
3. 启动 ML 服务：`docker compose up -d vocs-server`
4. 检查 ML 健康：`docker inspect --format "{{.State.Health.Status}}" vocs-control-system`
5. 启动用户端：`docker compose -f docker-compose.client.yml up -d`
6. 访问前端并验证 API。

## 数据持久化与备份

- 实时数据：`./vocs_realtime_data -> /app/vocs_realtime_data`
- 模型文件：`./models -> /app/models`
- PostgreSQL：命名卷 `postgres_data`
- Redis：命名卷 `redis_data`（AOF 开启）
- 用户端后端 SQLite：`backend_data` 卷（`/app/data/vocs.db`）

示例备份命令：

```bash
docker exec vocs-postgres pg_dump -U postgres -d vocs | gzip > backup/pg_$(date +%Y%m%d).sql.gz
```

## 非 Docker 源码部署

### ML 推理服务

```bash
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
# Linux: source .venv/bin/activate
pip install -r requirements.txt
python vocs_server.py
```

### 用户端后端

```bash
cd client-backend
python -m venv .venv
pip install -r requirements-init.txt
python run.py
```

### 用户端前端

```bash
cd client-frontend
npm install
npm run dev:h5
```

## 关键配置项说明

| 环境变量 | 默认值 | 说明 |
| --- | --- | --- |
| `ADMIN_JWT_SECRET` | `waste-gas-admin-secret` | 管理端 JWT 密钥，生产必须替换 |
| `ADMIN_USERNAME` | `admin` | 管理员账号 |
| `ADMIN_PASSWORD` | `admin123456` | 管理员密码，生产必须替换 |
| `VOCS_BASE_URL` | `http://127.0.0.1:8001` | 管理端访问 ML 服务地址 |
| `POSTGRES_DSN` | `sqlite+aiosqlite:///./data/vocs.db` | 用户端后端数据库连接 |
| `REDIS_URL` | `redis://redis:6379/0` | 用户端缓存地址 |
| `MODEL_PATH` | `models/vocs_seq2seq_v2_best.pth` | 模型路径 |
| `SCALER_PATH` | `models/vocs_scalers_v2.pkl` | 归一化器路径 |
| `TZ` | `Asia/Shanghai` | 时区 |

## 常见问题排查

### 前端打不开/白屏

排查步骤：

1. `docker compose ps` 或 `docker compose -f docker-compose.client.yml ps` 确认容器状态；
2. 检查端口监听：`ss -ltnp | grep -E '5173|5050|8080|8002'`；
3. 检查防火墙策略；
4. 确认前端构建产物存在并已挂载到 Nginx；
5. 检查 `client-frontend/nginx.conf` 的 `try_files` 配置。

### 登录后 401 / 实时数据不刷新

- JWT 过期：重新登录并检查 token 生命周期；
- SSE 被代理层缓冲：关闭 `proxy_buffering`；
- `vocs-server` 或后端未启动：检查容器日志；
- 前端 API 地址错误：确认设置为正确后端 URL。

### Torch 启动报错（OOM / Illegal instruction）

- 检查 CPU 指令集（是否支持 AVX2）；
- 检查显存与 `map_location` 配置；
- 检查 `models/` 是否正确挂载到容器。

### PostgreSQL 连接失败

- 容器网络内使用服务名 `postgres`，避免 `127.0.0.1`；
- 检查白名单、防火墙、`pg_hba.conf` 与监听地址；
- 查看应用启动日志中的连接异常。

### Docker 构建慢 / 拉取超时

- 配置镜像加速；
- Python 使用国内镜像源；
- npm 使用 `npmmirror`。

### SSE 长连接被断开

Nginx 增加：

```nginx
proxy_read_timeout 3600s;
proxy_send_timeout 3600s;
proxy_http_version 1.1;
proxy_set_header Connection "";
proxy_buffering off;
```

## 附录

### 端口一览

| 端口 | 服务 | 用途 |
| --- | --- | --- |
| `8001` | `vocs-server` | ML 推理 REST + SSE |
| `8002` | `admin-backend` 或 `client-backend` | API 服务（避免冲突） |
| `8080` | `client-frontend` | 用户端 H5 |
| `5173` | `admin-frontend`（dev） | 管理端开发服务 |
| `5432` | `postgres` | 时序数据库 |
| `6379` | `redis` | 缓存 |

### 健康检查命令速查

```bash
curl -s http://127.0.0.1:8001/status | python -m json.tool
curl -s http://127.0.0.1:8002/api/v1/health
docker exec vocs-postgres pg_isready -U postgres -d vocs
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

### 日志位置

- Docker：`docker compose logs -f <service>`
- 用户端 Nginx：容器内 `/var/log/nginx/`
- 应用日志：以容器标准输出为主

---

如排查未果，请提交以下信息给项目组：

1. `docker compose ps` 截图；
2. 故障服务最近 200 行日志；
3. 浏览器 Network/Console 截图；
4. 操作系统、Docker、Python、Node 版本信息。
