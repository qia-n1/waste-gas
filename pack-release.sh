#!/usr/bin/env bash
# ============================================================
# 智洁园区·废气综合管理平台 —— 离线交付包打包脚本
#
# 产出：
#   release/waste-gas-<VERSION>/
#     ├── waste-gas-images.tar.gz   ← 4 个镜像合包
#     ├── waste-gas-source.tar.gz   ← compose / .env.example / models / 配置
#     ├── install.sh                ← 用户端一键安装脚本
#     └── README.txt                ← 给收件人看的 5 行说明
#
# 用法：
#   bash pack-release.sh           # 默认版本号 = 当天日期
#   bash pack-release.sh 1.0.0     # 指定版本号
# ============================================================

set -euo pipefail

VERSION="${1:-$(date +%Y%m%d)}"
OUT_DIR="release/waste-gas-${VERSION}"
COMPOSE_FILE="docker-compose.prod.yml"

IMAGES=(
  "waste-gas/ensemble:latest"
  "waste-gas/vocs-server:latest"
  "waste-gas/admin-backend:latest"
  "waste-gas/admin-frontend:latest"
)

echo "================================================"
echo "  打包版本: ${VERSION}"
echo "  输出目录: ${OUT_DIR}"
echo "================================================"

# ---------- Step 0: 检查 Docker 与 compose ----------
command -v docker >/dev/null || { echo "[ERR] 未找到 docker"; exit 1; }
docker compose version >/dev/null || { echo "[ERR] 未找到 docker compose v2"; exit 1; }

mkdir -p "${OUT_DIR}"

# ---------- Step 1: 构建 4 个镜像 ----------
echo ""
echo "[1/4] 构建 4 个镜像 (首次约 8-15 分钟)..."
docker compose -f "${COMPOSE_FILE}" build

# ---------- Step 2: 导出镜像 tar.gz ----------
echo ""
echo "[2/4] 导出镜像到 waste-gas-images.tar.gz ..."
docker save "${IMAGES[@]}" | gzip -1 > "${OUT_DIR}/waste-gas-images.tar.gz"
echo "      镜像包大小: $(du -sh "${OUT_DIR}/waste-gas-images.tar.gz" | cut -f1)"

# ---------- Step 3: 打包源码与运行时资源 ----------
echo ""
echo "[3/4] 打包源码与运行时资源到 waste-gas-source.tar.gz ..."

# 用 tar 直接从项目根目录抓必要文件，排除大目录
tar --exclude-vcs \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='dist' \
    --exclude='release' \
    --exclude='backend' \
    --exclude='frontend' \
    --exclude='client-backend' \
    --exclude='client-frontend' \
    --exclude='uniapp-client' \
    --exclude='vocs-project' \
    --exclude='nginx-1.28.0' \
    --exclude='Postman测试' \
    --exclude='*.log' \
    --exclude='.env' \
    -czf "${OUT_DIR}/waste-gas-source.tar.gz" \
    docker-compose.prod.yml \
    .env.example \
    .dockerignore \
    Dockerfile \
    vocs_server.py \
    requirements.txt \
    models \
    vocs_realtime_data \
    admin \
    Docker部署快速指南.md \
    部署手册-Docker版.docx 2>/dev/null || true

echo "      源码包大小: $(du -sh "${OUT_DIR}/waste-gas-source.tar.gz" | cut -f1)"

# ---------- Step 4: 生成用户端 install.sh 与 README ----------
echo ""
echo "[4/4] 生成 install.sh 与 README.txt ..."

cat > "${OUT_DIR}/install.sh" <<'INSTALL_EOF'
#!/usr/bin/env bash
# 用户端一键安装脚本
#   把 waste-gas-images.tar.gz / waste-gas-source.tar.gz / install.sh
#   三个文件放在同一目录下后执行：bash install.sh
set -euo pipefail

echo "[1/3] 解压源码包..."
tar -xzf waste-gas-source.tar.gz
echo "      已展开到当前目录"

echo "[2/3] 加载 Docker 镜像 (约 4-8 分钟)..."
gunzip -c waste-gas-images.tar.gz | docker load

echo "[3/3] 启动服务..."
[ -f .env ] || cp .env.example .env
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml ps

cat <<MSG

============================================================
  部署完成！
  浏览器访问:  http://<服务器IP>:3001
  默认账号:    admin / admin123456
  修改密码:    编辑 .env 中的 ADMIN_PASSWORD 后
                docker compose -f docker-compose.prod.yml up -d
============================================================
MSG
INSTALL_EOF
chmod +x "${OUT_DIR}/install.sh"

cat > "${OUT_DIR}/README.txt" <<README_EOF
气盾卫士·多源化工废气智能治理系统  ${VERSION}
============================================================

环境要求:
  Docker Engine >= 24.0
  Docker Compose v2 >= 2.20
  端口空闲: 3001 / 8000 / 8001 / 8003

一键安装:
  bash install.sh

完成后浏览器打开:
  http://<服务器IP>:3001
  默认账号: admin / admin123456

详细文档: 见解压后根目录 部署手册-Docker版.docx
README_EOF

# ---------- 汇总 ----------
echo ""
echo "================================================"
echo "  打包完成 ✓"
echo "================================================"
ls -lh "${OUT_DIR}"
echo ""
echo "  分发以下三个文件给用户即可："
echo "    ${OUT_DIR}/waste-gas-images.tar.gz"
echo "    ${OUT_DIR}/waste-gas-source.tar.gz"
echo "    ${OUT_DIR}/install.sh   (附带 README.txt)"
echo ""
echo "  用户操作: 三个文件放一起，执行 bash install.sh"
echo "================================================"
