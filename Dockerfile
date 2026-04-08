# 使用官方 Python 3.10 镜像作为基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt 并安装 Python 依赖
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制应用代码
COPY vocs_server.py .
COPY models/ ./models/

# 创建必要的目录
RUN mkdir -p vocs_realtime_data

# 暴露端口
EXPOSE 8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/status')" || exit 1

# 启动应用
CMD ["uvicorn", "vocs_server:app", "--host", "0.0.0.0", "--port", "8001"]
