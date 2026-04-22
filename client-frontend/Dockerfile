# 第一阶段：构建阶段（可通过 DOCKER_REGISTRY 替换镜像源）
ARG DOCKER_REGISTRY=docker.io
FROM ${DOCKER_REGISTRY}/library/node:18-slim AS build-stage

WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源码
COPY . .

# 执行构建命令 (UniApp H5 构建)
RUN npm run build:h5

# 第二阶段：运行阶段
ARG DOCKER_REGISTRY=docker.io
FROM ${DOCKER_REGISTRY}/library/nginx:stable-alpine AS production-stage

# 复制构建产物到 Nginx 目录
# 注意：UniApp H5 构建产物通常在 dist/build/h5
COPY --from=build-stage /app/dist/build/h5 /usr/share/nginx/html

# 复制自定义 Nginx 配置（处理 SPA 路由与 API 反向代理）
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
