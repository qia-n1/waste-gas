# 用户端可运行系统原型（Docker 安装包）

目标：把 `client-backend` + `client-frontend` 打包成**一键可运行**的原型环境，用于现场演示核心功能（告警列表/详情/处置闭环/AI 方案问答入口等）。

## 交付物

- `docker-compose.client.yml`：用户端编排（backend + frontend + redis + 数据卷）
- `run-client-prototype.ps1`：Windows 一键启动（构建 + 启动 + 健康检查提示）
- `stop-client-prototype.ps1`：Windows 一键停止并清理容器（保留数据卷）
- `pack-client-prototype.ps1`：生成可分发 zip 安装包

## 运行前置条件

- Windows 10/11
- Docker Desktop（必须已启动 Docker 引擎）

## 一键启动（本机演示）

在仓库根目录执行：

```powershell
.\run-client-prototype.ps1
```

启动后访问：

- 前端（用户端 H5）：`http://localhost:8080`
- 后端健康检查：`http://localhost:8002/api/v1/health`

> 说明：前端默认会走同源 `/api/*`，由 Nginx 反向代理到后端 `/api/v1/*`，避免浏览器跨域与端口配置问题。

## 核心功能演示清单（建议按顺序）

- 告警列表：进入“告警”页，能加载列表
- 告警详情：点击任意告警进入详情页
- 接单 / 处置：详情页可“接单”，可提交处置反馈进入“持续跟踪”
- AI 方案与问答入口：详情页“AI 方案与问答”区域可加载历史/发起提问（若后端禁用 RAG，则此区域可保持不阻断主流程）

## 在线演示部署（服务器）

在 Linux/Windows Server 上安装 Docker 后：

```bash
docker compose -f docker-compose.client.yml up -d --build
```

开放端口：

- `8080`：用户端访问
- `8002`：后端 API（可选；若只允许从前端访问，可仅开放 8080）

## 常见问题

- Docker 报 “docker daemon is not running”
  - 请先启动 Docker Desktop，并确保 WSL2/Hyper-V 环境可用（按你本机配置）。

- 拉取 `docker.io/*` 超时 / 443 被阻断（最常见）
  - 这是网络/代理策略问题，不是 compose 配置问题。需要让 Docker Engine 能通过公司代理访问外网（至少能访问 `registry-1.docker.io:443`）。
  - Docker Desktop 里确认 **HTTP Proxy / HTTPS Proxy** 都已配置为你可用的代理地址，并勾选“使用代理”。
  - 验证命令（能成功拉取则 OK）：

```powershell
docker pull redis:7-alpine
docker pull python:3.10-slim
```

