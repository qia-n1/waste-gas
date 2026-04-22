# 智洁园区 · 废气综合管理平台 — Docker 一键部署

把这 5 个文件 / 配置交给任何人，他在装好 Docker 的机器上就能 30 分钟内跑起整套系统。

---

## 一、运行环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Linux (Ubuntu 22.04+/CentOS 9 推荐) / Windows 11 + WSL2 / macOS |
| Docker Engine | ≥ 24.0 |
| Docker Compose | ≥ v2.20 (内置 `docker compose` 子命令) |
| CPU | 4 核及以上 |
| 内存 | ≥ 8 GB（ensemble + vocs-server 都会加载 Torch 模型） |
| 磁盘 | ≥ 15 GB（构建产物 + 镜像缓存） |
| 端口占用 | 3001 / 8000 / 8001 / 8003 必须空闲 |

---

## 二、四个服务一览

| 服务 | 容器名 | 对外端口 | 镜像 |
|------|---------|---------|------|
| 集成学习预测 (ensemble_docker) | `wg-ensemble`        | **8000** | `waste-gas/ensemble:latest` |
| VOCs 实时推理 (vocs_server)    | `wg-vocs-server`     | **8001** | `waste-gas/vocs-server:latest` |
| 管理端后端 (FastAPI)           | `wg-admin-backend`   | **8003** | `waste-gas/admin-backend:latest` |
| 管理端前端 (Nginx + Vue3)      | `wg-admin-frontend`  | **3001** | `waste-gas/admin-frontend:latest` |

四个容器共用 `waste-gas-net` 桥接网络，容器内通过服务名互访（如 `http://vocs-server:8001`）。
浏览器最终只需要访问 **`http://<服务器IP>:3001`** 一个入口。

---

## 三、首次部署

### 1) 准备环境变量

```bash
cp .env.example .env
# 编辑 .env：把 ADMIN_PASSWORD / ADMIN_JWT_SECRET / PG_* 改成自己的值
```

> 不改也能跑 —— 默认账户 `admin / admin123456`，PG 走项目组开发库。

### 2) 构建镜像

```bash
docker compose -f docker-compose.prod.yml build
```

首次构建约 8-15 分钟（取决于网速，主要是 torch、sentence-transformers）。
之后改代码再 build 大部分层会命中缓存。

### 3) 启动

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4) 验证

```bash
docker compose -f docker-compose.prod.yml ps    # 四个容器都应是 Up
docker compose -f docker-compose.prod.yml logs -f --tail=50

# 健康检查
curl http://localhost:8000/health        # ensemble
curl http://localhost:8001/status        # vocs-server
curl http://localhost:8003/api/health    # admin-backend
curl http://localhost:3001/healthz       # admin-frontend (nginx)
```

浏览器打开 **http://localhost:3001** 即可看到登录页 → 用 `admin / admin123456` 进入大屏。

---

## 四、常用运维命令

```bash
# 查看实时日志（指定服务）
docker compose -f docker-compose.prod.yml logs -f admin-backend

# 重启某个服务
docker compose -f docker-compose.prod.yml restart admin-frontend

# 改了前端代码，单独重建并替换
docker compose -f docker-compose.prod.yml build admin-frontend
docker compose -f docker-compose.prod.yml up -d admin-frontend

# 全部停掉并删除容器（数据卷保留）
docker compose -f docker-compose.prod.yml down

# 清理全部（包括数据卷，慎用）
docker compose -f docker-compose.prod.yml down -v
```

---

## 五、上云 / 离线交付

### 方式 A：导出镜像 tar 包（无网环境部署）

```bash
# 在有网机器上构建好后导出
docker save \
  waste-gas/ensemble:latest \
  waste-gas/vocs-server:latest \
  waste-gas/admin-backend:latest \
  waste-gas/admin-frontend:latest \
  | gzip > waste-gas-images.tar.gz

# 把 waste-gas-images.tar.gz + docker-compose.prod.yml + .env.example
# + models/  + vocs_realtime_data/  打包，传到目标服务器后：
gunzip -c waste-gas-images.tar.gz | docker load
docker compose -f docker-compose.prod.yml up -d
```

### 方式 B：推到镜像仓库（阿里云 ACR / Harbor / Docker Hub）

```bash
# 1. 登录
docker login registry.cn-hangzhou.aliyuncs.com

# 2. 重打 tag
docker tag waste-gas/admin-frontend:latest \
  registry.cn-hangzhou.aliyuncs.com/<命名空间>/admin-frontend:1.0.0

# 3. 推送
docker push registry.cn-hangzhou.aliyuncs.com/<命名空间>/admin-frontend:1.0.0
```

之后只需把 `docker-compose.prod.yml` 中 `build:` 块换成 `image: registry.../xxx:tag`，
目标服务器 `docker compose pull && docker compose up -d` 即可。

---

## 六、常见问题

| 现象 | 排查 |
|------|------|
| `port is already allocated` | 已被占用，改 compose 端口映射或释放原占用进程 |
| 前端白屏，控制台 `/api/* 502` | `admin-backend` 没起来；`docker logs wg-admin-backend` 看 |
| SSE 不实时刷新 | 检查反代是否生效，`nginx.conf` 已默认关闭 `proxy_buffering` |
| `ensemble` OOM 被杀 | 加内存 / 调大 `deploy.resources.limits.memory` |
| `psycopg2 OperationalError` | `.env` 里的 PG_* 配错 / 数据库白名单未放行 |
| 构建拉包慢 | 镜像加速器配 `daemon.json`；npm 已默认走 `npmmirror.com` |

---

## 七、文件清单（部署交付物）

```
waste-gas/
├── docker-compose.prod.yml             ★ 一键编排
├── .env.example                        ★ 环境变量样板
├── .dockerignore                        优化构建上下文
├── Dockerfile                           vocs-server 镜像
├── vocs_server.py / models/ / vocs_realtime_data/   ML 服务运行时资源
├── admin/
│   ├── backend/Dockerfile              ★ admin-backend 镜像
│   └── frontend/
│       ├── Dockerfile                  ★ admin-frontend 镜像（多阶段）
│       └── nginx.conf                  ★ 反代 + SSE 配置
└── models/new_VOC/ensemble_docker/     ensemble 服务（已有 Dockerfile）
```

带 ★ 的是本次新增 / 修改的部署相关文件。
