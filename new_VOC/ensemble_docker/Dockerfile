FROM python:3.10-slim

# 配置国内源以加速下载包（可选，视具体网络环境而定）
# RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 设置工作目录
WORKDIR /app

# 安装必要的系统依赖库
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 仅拷贝依赖文件，便于利用构建缓存
COPY requirements_deploy.txt /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements_deploy.txt

# 将项目的所有源码复制到容器内
COPY . /app/

# 暴露 FastAPI 服务默认端口
EXPOSE 8000

# 运行主程序
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
