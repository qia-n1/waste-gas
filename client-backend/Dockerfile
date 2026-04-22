# 使用官方 Python 3.10 镜像作为基础镜像（可通过 DOCKER_REGISTRY 替换镜像源）
ARG DOCKER_REGISTRY=docker.io
FROM ${DOCKER_REGISTRY}/library/python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖（如需编译某些 Python 包）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖清单并安装
COPY requirements-init.txt .
RUN pip install --no-cache-dir -r requirements-init.txt

# 复制应用代码
COPY . .

# 暴露端口 (与 run.py 中端口一致，通常为 8002)
EXPOSE 8002

# 生产环境启动命令（禁用 reload）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
