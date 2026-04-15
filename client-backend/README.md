# 废气监测后端服务

基于 FastAPI + PostgreSQL 的后端服务，已可与 `client-frontend` 直接联调。

## 功能范围

- 启动自动建表并写入首批种子数据
- 首页概览接口
- 实时监控接口
- 告警列表/详情/处理接口
- 个人信息接口
- 设置读取与保存接口

## 环境准备

1. 安装 Python 3.10+
2. 安装依赖：

   python -m pip install -r requirements-init.txt

3. 配置环境变量（已提供云数据库样例）：

   复制 `.env.example` 为 `.env`

4. 启动服务：

   python run.py

## 关键接口

- GET /api/v1/health
- GET /api/v1/dashboard/overview
- GET /api/v1/monitor/realtime
- POST /api/v1/monitor/control/start
- POST /api/v1/monitor/control/stop
- GET /api/v1/alerts
- GET /api/v1/alerts/{alert_id}
- POST /api/v1/alerts/{alert_id}/resolve
- POST /api/v1/alerts/{alert_id}/ignore
- GET /api/v1/profile/me
- GET /api/v1/settings
- PUT /api/v1/settings

## 前端联调

`client-frontend` 默认请求地址：

- http://127.0.0.1:8002/api/v1

可在客户端设置页面修改“后端地址”。
