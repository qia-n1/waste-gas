# 管理端后端 —— Waste Gas Admin API (FastAPI, port 8003)
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# 系统依赖：psycopg2 需要 libpq；torch / sentence-transformers 需要 build-essential
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        ca-certificates \
        tzdata \
    && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && rm -rf /var/lib/apt/lists/*

# 优先复制 requirements 以利用 Docker 层缓存
COPY admin/backend/requirements.txt /app/requirements.txt

# torch CPU 版（避免拉取 CUDA wheel，体积小很多）
RUN pip install --upgrade pip \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch==2.3.1 \
    && pip install -r /app/requirements.txt

# 复制后端代码
COPY admin/backend/ /app/

# 暴露端口（与 docker-compose / 启动脚本保持一致：8003）
EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8003/api/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
