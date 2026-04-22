# 管理端前端 —— Vue3 + Vite 构建产物，由 Nginx 托管
# 多阶段：node 构建 → nginx 运行

# ===== Stage 1: build =====
FROM node:20-alpine AS build

WORKDIR /app

# 利用层缓存：先装依赖
COPY admin/frontend/package.json admin/frontend/package-lock.json* ./
RUN npm config set registry https://registry.npmmirror.com \
    && (npm ci || npm install)

# 复制源码并构建
COPY admin/frontend/ ./
RUN npm run build

# ===== Stage 2: runtime =====
FROM nginx:1.27-alpine

ENV TZ=Asia/Shanghai
RUN apk add --no-cache tzdata curl \
    && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

# Nginx 配置：托管 SPA + 反向代理 /api 到 admin-backend、/vocs 到 vocs-server
COPY admin/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# 拷贝构建产物
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://127.0.0.1/ >/dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
