**气盾卫士-**

**多源化工废气智能治理系统系统部署手册（Docker 版）**

# 1.项目概述

## 1.1系统简介

气盾卫士-多源化工废气智能治理系统是一套面向工业园区废气治理的实时监测、智能预警与辅助决策系统。系统通过对现场 RTO（蓄热式热氧化炉）、转轮吸附装置、喷涂工艺段等关键工段的 26 项传感器数据进行秒级采集、分钟级预测，结合 AI 模型输出未来 6 小时 VOCs 浓度趋势、异常根因归因与 RAG（检索增强生成）处置建议，支撑运行人员、运维人员与管理人员三级协同处置。

本版本（v2.0）相比首版手册的核心变化：**全栈已完成 Docker 容器化**，部署流程从首版的逾 10 步简化至 **4 步上线**，部署机器只需安装 Docker 与 Docker Compose，无需再手动安装 Python / Node / Nginx 与各类依赖。

## 1.2子系统构成

| **子系统** | **容器名** | **端口** | **职责** |
|---|---|---|---|
| 集成学习预测服务 | wg-ensemble | 8000 | VOC 多模型集成预测 (DLinear+XGBoost) |
| VOCs 实时推理服务 | wg-vocs-server | 8001 | 传感器数据接入、Seq2Seq 预测、SSE 实时推送 |
| 管理端后端 | wg-admin-backend | 8003 | 大屏聚合 API、JWT 鉴权、RAG、告警管理 |
| 管理端前端 | wg-admin-frontend | 3001 | Vue3 + Three.js 可视化大屏 |
| PostgreSQL | （外部托管） | 5432 | 告警历史、工单、RAG 计划持久化 |

四个核心容器统一加入 `wg-net` 桥接网络，容器内部通过服务名互访（如 `http://vocs-server:8001`），上云后无需修改任何配置。**用户最终只需访问 `http://<服务器IP>:3001` 一个入口。**

## 1.3数据流概览

**现场 PLC / DCS** → `POST /sensor-data` → **vocs-server (8001)** → `SSE /events` → **admin-backend (8003)** → `GET /api/dashboard/overview` + `SSE /api/events` → **admin-frontend (3001)**

# 2.环境配置要求

## 2.1硬件最低配置

| **项目** | **最低配置（开发/演示）** | **推荐配置（生产）** |
|---|---|---|
| CPU | 4 核 (x86_64) | 8 核以上，支持 AVX2 |
| 内存 | 8 GB | 16 GB 及以上 |
| 硬盘 | 20 GB SSD（含镜像缓存） | 100 GB SSD（含日志/备份） |
| GPU | 非必须（CPU 推理已可） | 可选 NVIDIA T4/A10（加速 Torch 推理） |
| 网络 | 千兆内网 | 千兆内网 + 公网备用链路 |
| 端口 | 3001 / 8000 / 8001 / 8003 必须空闲 | 同左 |

## 2.2部署机器软件依赖

相比首版"必须装 Python + Node + Nginx + 数据库 + 依赖包"的复杂要求，本版只需：

- **Docker Engine**：`>= 24.0`
- **Docker Compose**：`>= v2.20`（内置 `docker compose` 子命令形式）
- **时区**：`Asia/Shanghai`（已在容器与 compose 中显式声明）

支持的操作系统：

- **Linux**：Ubuntu 22.04 LTS / Debian 12 / CentOS 9 / Rocky Linux 9（推荐）
- **Windows**：Windows 10/11 + WSL2 + Docker Desktop
- **macOS**：macOS 12+ + Docker Desktop（仅限本地演示）

Docker 一键安装速查（Ubuntu / Debian）：

```bash
curl -fsSL https://get.docker.com | bash
sudo usermod -aG docker $USER
newgrp docker
docker --version              # 应输出 Docker version 24.x.x
docker compose version        # 应输出 Docker Compose version v2.x.x
```

# 3.依赖包清单

以下依赖均已固化在对应镜像中，**部署人员无需手动安装**。本节仅供二次开发或镜像审计参考。

## 3.1集成学习预测服务镜像（python:3.10-slim）

| **包名** | **版本** | **说明** |
|---|---|---|
| fastapi | >=0.104.1 | Web 框架 |
| uvicorn | >=0.24.0 | ASGI 服务器 |
| pydantic | >=2.4.0 | 数据校验 |
| numpy | >=1.26.0 | 数值计算 |
| pandas | >=2.0.3 | 时序数据处理 |
| scikit-learn | >=1.3.0 | 集成学习底层依赖 |
| torch | >=2.0.0 | DLinear 模型推理 |

## 3.2VOCs 实时推理服务镜像（python:3.10-slim）

| **包名** | **版本** | **说明** |
|---|---|---|
| fastapi | 0.104.1 | Web 框架 |
| uvicorn | 0.24.0 | ASGI 服务器 |
| torch | 2.7.0 | 深度学习推理，Seq2Seq 预测模型 |
| numpy | >=1.26.0 | 数值计算 |
| pandas | >=2.0.3 | 时序数据处理 |
| pydantic | 2.4.0 | 数据校验与序列化 |
| requests | 2.31.0 | 同步 HTTP 客户端（测试脚本） |
| sseclient | 0.0.27 | SSE 测试客户端 |
| scikit-learn | 1.7.0 | StandardScaler 反归一化 |

## 3.3管理端后端镜像（python:3.11-slim）

| **包名** | **版本** | **说明** |
|---|---|---|
| fastapi | 0.116.1 | Web 框架 |
| uvicorn | 0.35.0 | ASGI 服务器 |
| httpx | 0.28.1 | 异步 HTTP，代理到 vocs/ensemble |
| pyjwt | 2.10.1 | 管理员 JWT 颁发与校验 |
| pydantic | 2.11.7 | 数据模型 |
| psycopg2-binary | 2.9.10 | PostgreSQL 驱动 |
| python-dotenv | 1.2.2 | .env 加载 |
| sentence-transformers | 2.2.2 | RAG 向量化 |
| torch (CPU 版) | 2.3.1 | 向量模型推理 |
| openai | 2.31.0 | 大模型接口（RAG 生成端） |
| numpy | 1.26.4 | 向量运算 |
| pandas | 3.0.2 | 结构化数据 |
| pypdf | 6.10.0 | RAG 知识库 PDF 解析 |
| python-docx | 1.2.0 | RAG 知识库 DOCX 解析 |

> **体积优化**：admin-backend Dockerfile 显式从 `download.pytorch.org/whl/cpu` 安装 torch，避免拉取约 2 GB 的 CUDA wheel，最终镜像减小约 1.5 GB。

## 3.4管理端前端镜像（多阶段：node:20-alpine → nginx:1.27-alpine）

| **依赖** | **版本** | **说明** |
|---|---|---|
| vue | ^3.5.32 | 核心框架 |
| vue-router | ^4.6.4 | 路由 |
| pinia | ^3.0.2 | 状态管理 |
| axios | ^1.15.0 | HTTP 客户端 |
| element-plus | ^2.9.7 | 暗黑主题组件库 |
| @element-plus/icons-vue | ^2.3.1 | 图标集 |
| echarts | ^6.0.0 | 图表库 |
| vue-echarts | ^8.0.1 | ECharts Vue 封装 |
| three | ^0.183.2 | 3D 工厂可视化 |
| dayjs | ^1.11.13 | 时间格式化 |
| vite | ^5.4.19 | 构建工具（仅 build 阶段） |
| typescript | ~6.0.2 | 类型系统（仅 build 阶段） |
| vue-tsc | ^3.2.6 | Vue 类型检查（仅 build 阶段） |

## 3.5镜像清单与体积

| **镜像名** | **基础镜像** | **预估大小** | **Dockerfile 位置** |
|---|---|---|---|
| waste-gas/ensemble:latest | python:3.10-slim | ~1.6 GB | models/new_VOC/ensemble_docker/ |
| waste-gas/vocs-server:latest | python:3.10-slim | ~1.4 GB | ./Dockerfile |
| waste-gas/admin-backend:latest | python:3.11-slim | ~2.2 GB | admin/backend/Dockerfile |
| waste-gas/admin-frontend:latest | nginx:1.27-alpine | ~45 MB | admin/frontend/Dockerfile |

# 4.Docker 部署步骤（4 步上线）

整个部署流程精简为 4 步：**获取交付物 → 配置环境变量 → 构建镜像 → 启动并验证**。

## 4.1Step 1：获取交付物

**方式 A：从 Git 克隆（在线环境）**

```bash
git clone <your-repo-url> waste-gas
cd waste-gas
```

**方式 B：从离线包解压（无网环境）**

```bash
# 1) 解压源码包
tar -xzf waste-gas-bundle.tar.gz
cd waste-gas

# 2) 加载预先导出的镜像（约 4.5 GB）
gunzip -c waste-gas-images.tar.gz | docker load
```

解压/克隆后，根目录应包含：`docker-compose.prod.yml`、`.env.example`、`Dockerfile`、`vocs_server.py`、`models/`、`admin/`、`models/new_VOC/ensemble_docker/`。

## 4.2Step 2：配置环境变量

```bash
cp .env.example .env
# 用任意编辑器打开 .env，按需修改：
#   ADMIN_PASSWORD=改成强密码
#   ADMIN_JWT_SECRET=改成长随机串
#   PG_HOST / PG_USER / PG_PASSWORD（如使用自有数据库）
```

> **最小可用**：若仅作演示，**可不修改直接进入下一步**——默认账户 `admin / admin123456`，PG 默认指向项目组开发库，所有功能立即可用。

## 4.3Step 3：一键构建镜像

```bash
docker compose -f docker-compose.prod.yml build
```

首次构建约 **8-15 分钟**（主要在拉取 torch、sentence-transformers、node_modules）。后续修改代码再 build，多数层会命中缓存，1-3 分钟完成。

> 如使用离线镜像（Step 1 方式 B 已 `docker load`），**跳过本步**，直接进入 Step 4。

## 4.4Step 4：启动并验证

```bash
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps   # 4 个容器都应是 Up
```

快速健康检查：

```bash
curl http://localhost:8000/health        # ensemble
curl http://localhost:8001/status        # vocs-server
curl http://localhost:8003/api/health    # admin-backend
curl http://localhost:3001/healthz       # admin-frontend
```

完成！浏览器访问 `http://<服务器IP>:3001`，使用 `admin / admin123456` 登录即可看到大屏。

# 5.云端部署 / 离线交付

## 5.1方式 A：导出镜像 tar 包（适合无网环境）

```bash
# 在有网机器上构建好后导出
docker save \
  waste-gas/ensemble:latest \
  waste-gas/vocs-server:latest \
  waste-gas/admin-backend:latest \
  waste-gas/admin-frontend:latest \
  | gzip > waste-gas-images.tar.gz

# 把 tar.gz + 项目源码 + .env + models/ + vocs_realtime_data/
# 一起拷贝到目标服务器，按 Step 1 方式 B 加载即可
```

## 5.2方式 B：推送到镜像仓库（阿里云 ACR / Harbor / Docker Hub）

```bash
# 1) 登录仓库
docker login registry.cn-hangzhou.aliyuncs.com

# 2) 重打 tag
docker tag waste-gas/admin-frontend:latest \
  registry.cn-hangzhou.aliyuncs.com/<命名空间>/admin-frontend:1.0.0
# (其余 3 个镜像同理)

# 3) 推送
docker push registry.cn-hangzhou.aliyuncs.com/<命名空间>/admin-frontend:1.0.0
```

之后将 `docker-compose.prod.yml` 中的 `build:` 块替换为 `image:`，目标服务器执行 `docker compose pull && docker compose up -d` 即可。

# 6.服务管理命令

## 6.1全系统

```bash
# 查看实时日志
docker compose -f docker-compose.prod.yml logs -f

# 查看指定服务日志
docker compose -f docker-compose.prod.yml logs -f admin-backend

# 重启某个服务
docker compose -f docker-compose.prod.yml restart admin-frontend

# 修改前端代码后单独重建并替换
docker compose -f docker-compose.prod.yml build admin-frontend
docker compose -f docker-compose.prod.yml up -d admin-frontend
```

## 6.2全部停止

```bash
# 停止并删除容器（数据卷保留）
docker compose -f docker-compose.prod.yml down
```

## 6.3彻底卸载（清空数据）

```bash
# 停止并删除容器 + 数据卷（慎用，本机持久化数据将丢失）
docker compose -f docker-compose.prod.yml down -v
```

## 6.4备份外部数据库

```bash
# 通过宿主机 psql 客户端备份（PG 是外部托管）
PGPASSWORD=$PG_PASSWORD pg_dump \
  -h $PG_HOST -p 5432 -U $PG_USER -d $PG_DB \
  | gzip > backup/pg_$(date +%Y%m%d).sql.gz
```

# 7.关键配置项说明

## 7.1`.env` 环境变量（用户可覆盖）

| **环境变量** | **默认值** | **说明** |
|---|---|---|
| ADMIN_JWT_SECRET | please-change-me-... | JWT 签名密钥，生产必须更换 |
| ADMIN_USERNAME | admin | 管理员登录名 |
| ADMIN_PASSWORD | admin123456 | 管理员登录密码 |
| ADMIN_TOKEN_EXPIRE_MINUTES | 120 | Token 有效期（分钟） |
| PG_HOST | 98.142.241.155 | 默认指向开发库，生产必须覆盖 |
| PG_PORT | 5432 | PostgreSQL 端口 |
| PG_DB | aqimonitor | 库名 |
| PG_USER | team | 用户名 |
| PG_PASSWORD | fwwb1234 | 密码 |
| OPENAI_API_KEY | （未设置） | RAG 大模型 Key（可选） |
| OPENAI_BASE_URL | （未设置） | RAG 大模型地址（可选） |

## 7.2compose 内部固定项（不通过 .env 覆盖）

| **环境变量** | **值** | **说明** |
|---|---|---|
| VOCS_BASE_URL | http://vocs-server:8001 | 容器内服务发现 |
| ENSEMBLE_BASE_URL | http://ensemble:8000 | 容器内服务发现 |
| TZ | Asia/Shanghai | 时区 |
| MODEL_PATH | models/vocs_seq2seq_v2_best.pth | ML 模型路径 |
| SCALER_PATH | models/vocs_scalers_v2.pkl | 归一化器 |

## 7.3端口冲突修改

如部署机器上已有服务占用 3001 / 8000 / 8001 / 8003，可直接修改 `docker-compose.prod.yml` 中对应服务的 `ports` 字段，例如把前端从 `"3001:80"` 改为 `"3002:80"` 即可。

## 7.4数据持久化

- `./vocs_realtime_data` → `wg-vocs-server:/app/vocs_realtime_data`（CSV 回放数据）
- `./models` → `wg-vocs-server:/app/models`（模型文件，支持热更新）
- PostgreSQL 数据由**外部数据库**承载，不占用本机卷

# 8.常见问题排查

## 8.1容器启动失败 / 端口占用

**现象**：`docker compose up` 报错：`Bind for 0.0.0.0:3001 failed: port is already allocated`。

**排查与处理**：

1. Linux：`ss -ltnp | grep -E '3001|8000|8001|8003'` 找到占用进程；
2. Windows：`netstat -ano | findstr :3001` 然后 `taskkill /PID <pid> /F`；
3. 或修改 `docker-compose.prod.yml` 中端口映射，例如 `"3002:80"`。

## 8.2前端打不开 / 白屏

**现象**：浏览器访问 `http://<IP>:3001` 空白，或控制台报 `Failed to load resource: net::ERR_CONNECTION_REFUSED`。

**排查步骤**：

1. 确认容器存活：`docker compose -f docker-compose.prod.yml ps`，STATUS 应为 `Up`。
2. 确认端口监听：`ss -ltnp | grep 3001`。
3. 确认防火墙放行：`ufw status` / `firewall-cmd --list-ports`。
4. 浏览器强刷（Ctrl+F5）排除前端缓存。
5. 检查 `wg-admin-frontend` 的 nginx 日志：`docker logs wg-admin-frontend`。

## 8.3前端控制台报 `/api/* 502`

**原因**：`wg-admin-backend` 未启动或健康检查失败。

```bash
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs admin-backend --tail 100
# 常见根因：
#   - PG_PASSWORD 错误 → 看到 psycopg2.OperationalError
#   - VOCS_BASE_URL 配错 → 看到 httpx.ConnectError
```

## 8.4登录后 401 / 实时数据不刷新

**可能原因**：

- JWT 过期：检查 `ADMIN_TOKEN_EXPIRE_MINUTES`，登录后重新获取 token。
- SSE 被前端反代缓冲：`nginx.conf` 中 `/api/` 与 `/vocs/` 已默认 `proxy_buffering off`、`proxy_read_timeout 3600s`，如自定义反代需保留该配置。
- vocs-server 未启动或健康检查失败：`docker logs wg-vocs-server`。
- 浏览器控制台 `/api/events` 连接断开：检查 `chunked_transfer_encoding` 是否开启。

## 8.5Torch 启动报错 `CUDA out of memory` 或 `Illegal instruction`

某些旧服务器缺少 AVX2 指令集，PyTorch 默认二进制会触发 `Illegal instruction (core dumped)`。

**排查**：

1. `cat /proc/cpuinfo | grep -o 'avx2' | head -1` 验证 CPU 指令集。
2. `nvidia-smi` 查看显存占用。
3. 镜像内已为 admin-backend 默认使用 CPU 版 torch；如 vocs-server 同样问题，可在其 Dockerfile 把 `torch==2.7.0` 改为 `torch==2.0.1+cpu` 重建。

## 8.6PostgreSQL 连接失败

**典型报错**：`psycopg2.OperationalError: could not connect to server`。

**排查**：

1. 检查 `.env` 中 `PG_HOST/PG_USER/PG_PASSWORD` 是否正确。
2. 云数据库需将服务器出口 IP 加入白名单。
3. 应用日志出现 `[DB] WARNING: init_pool failed`——RAG 持久化功能将自动降级，但**不阻塞启动**，其他功能仍可用。

## 8.7告警与持续监控面板"无数据"

- 前端已内置 mock 演示数据（`stores/alerts.ts`、`stores/dashboard.ts`），即使后端断开也会回退显示；若 mock 也不出现，多为浏览器缓存了旧产物——按 Ctrl+F5 强刷。
- 确认 vocs-server 有数据：`curl http://localhost:8001/alerts?limit=5`。
- 管理端后端日志 `httpx.ConnectError`：检查容器网络是否正常 `docker network inspect waste-gas-net`。

## 8.8 ensemble 容器 OOM 被杀

**现象**：`wg-ensemble` 状态变为 `Exited (137)`，`docker inspect` 中 `OOMKilled: true`。

**处理**：调大 compose 中 `deploy.resources.limits.memory`（默认 4G），或为宿主机加内存。

## 8.9 3D 场景卡顿 / WebGL 不可用

- 浏览器需启用硬件加速；集成显卡建议窗口分辨率 ≤ 1920×1080。
- Chrome 地址栏输入 `about:gpu`，确认 WebGL2 处于 `Hardware accelerated`。
- 远程桌面 / RDP 下常见 WebGL fallback 到软件渲染，建议现场演示用本机浏览器。

## 8.10 Docker 构建慢 / 拉取超时

```bash
# 1) 配置 Docker 镜像加速器
sudo tee /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
EOF
sudo systemctl restart docker

# 2) admin-frontend Dockerfile 已默认 npm 国内源 (npmmirror.com)
# 3) Python 镜像可在 Dockerfile 取消下面这行的注释：
#    RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

## 8.11升级 / 回滚

**升级（已推送到镜像仓库时）**：

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

**升级（源码方式）**：

```bash
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

**回滚**：保留旧镜像 tag（如 `:1.0.0` 与 `:1.1.0` 并存），回滚时只需 `docker tag waste-gas/xxx:1.0.0 waste-gas/xxx:latest && docker compose up -d`。

# 附录

## 1.端口一览

| **端口** | **服务** | **用途** |
|---|---|---|
| 3001 | wg-admin-frontend | 用户唯一入口，Nginx 托管 SPA |
| 8003 | wg-admin-backend | 管理端聚合 API + JWT |
| 8001 | wg-vocs-server | ML 推理 REST + SSE |
| 8000 | wg-ensemble | 集成学习预测服务 |
| 5432 | （外部 PostgreSQL） | 时序数据库（不在容器内） |

## 2.健康检查命令速查

```bash
# 全量容器状态
docker compose -f docker-compose.prod.yml ps

# 各服务健康端点
curl -s http://localhost:8000/health        | python -m json.tool
curl -s http://localhost:8001/status        | python -m json.tool
curl -s http://localhost:8003/api/health
curl -s http://localhost:3001/healthz

# 容器内部网络互通验证
docker exec wg-admin-backend curl -s http://vocs-server:8001/status
docker exec wg-admin-backend curl -s http://ensemble:8000/health
```

## 3.日志位置

- Docker 全栈日志：`docker compose -f docker-compose.prod.yml logs -f`
- 单服务日志：`docker logs -f wg-admin-backend`
- Nginx 访问日志（前端容器内）：`/var/log/nginx/access.log`

## 4.与 v1.0 手册的差异

| **条目** | **v1.0（源码部署）** | **v2.0（Docker 部署）** |
|---|---|---|
| 部署步骤数 | ≥ 10 步 | **4 步** |
| 依赖安装 | 手动装 Python / Node / Nginx 等 | 仅需 Docker |
| 环境冲突风险 | 高（torch 版本、libpq 等） | 已隔离 |
| 首次部署耗时 | 30-60 分钟 | 10-20 分钟（多数为镜像构建） |
| 离线交付 | 需打包源码 + 文档教安装 | `docker save/load` 一键 |
| 回滚 | 手动逐项恢复 | 切换镜像 tag 一键 |

## 5.交付物清单

| **文件 / 目录** | **用途** |
|---|---|
| docker-compose.prod.yml | 一键编排（4 个服务） |
| .env.example | 环境变量样板 |
| .dockerignore | 优化构建上下文 |
| Dockerfile | vocs-server 镜像 |
| vocs_server.py | ML 推理主入口 |
| models/ | 预训练模型（运行时挂载） |
| vocs_realtime_data/ | CSV 回放数据（运行时挂载） |
| admin/backend/Dockerfile | admin-backend 镜像 |
| admin/frontend/Dockerfile | admin-frontend 镜像（多阶段） |
| admin/frontend/nginx.conf | 反向代理 + SSE 配置 |
| models/new_VOC/ensemble_docker/ | ensemble 镜像构建上下文 |

## 6.技术支持

如排查未果，请联系项目组并提供：

1. `docker compose -f docker-compose.prod.yml ps` 截图
2. 问题服务最近 200 行日志（`docker logs --tail 200 <container>`）
3. 浏览器控制台 Network 面板截图（如为前端问题）
4. Docker / Docker Compose 版本（`docker version`、`docker compose version`）
