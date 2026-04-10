# waste-gas

已补充与技术栈选型对齐的初始化框架，包含：

- 后端初始化骨架：FastAPI 模块化目录、配置、日志、JWT、调度器、Redis/DB 连接占位、RAG 占位路由
- 前端初始化骨架：Vue3 + TS + Router + Pinia + Axios + Element Plus + TailwindCSS 的工程化分层
- 保持现有可运行服务不破坏：原有单文件服务 vocs_server.py 与 PIDControl 页面仍可继续使用

## 目录说明

- backend/: 新增后端模块化框架（初始化层）
- vocs-project/: 新增前端工程化初始化层
- vocs_server.py: 现有业务服务入口（保留）

## 快速体验

1. 继续跑原系统：

	python vocs_server.py

2. 体验后端新骨架：

	cd backend
	pip install -r requirements-init.txt
	cp .env.example .env
	python run.py

3. 体验前端新骨架：

	cd vocs-project
	npm install
	cp .env.example .env
	npm run dev

4. 按方案启动基础设施（可选）：

	docker compose --profile infra up -d postgres redis
