# backend 初始化骨架

该目录提供与方案技术栈一致的后端初始化框架：

- FastAPI 模块化入口
- API 路由聚合结构
- JWT 鉴权基础工具
- AsyncIOScheduler 任务调度初始化
- PostgreSQL/Redis 连接初始化
- RAG 服务占位（便于接入 LangChain 或 LlamaIndex）

## 快速启动

1. 安装依赖：

   pip install -r requirements-init.txt

2. 初始化环境变量：

   cp .env.example .env

3. 启动服务：

   python run.py

4. 访问健康检查：

   http://127.0.0.1:8002/api/v1/health
