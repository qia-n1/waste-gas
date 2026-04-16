@echo off
chcp 65001 >nul
title Smart Clean Park - Admin Dashboard Launcher

set "ROOT=%~dp0.."
set "ADMIN=%~dp0"

echo ============================================================
echo   智洁园区 - 废气综合管理平台  管理端启动器
echo ============================================================
echo.

REM ── 1. ensemble_docker (port 8000) — 可选 ──
echo [1/4] 集成预测模型服务 (ensemble_docker:8000) ...
cd /d "%ROOT%\models\new_VOC\ensemble_docker"
if exist "docker-compose.yml" (
    echo       检测到 docker-compose.yml，尝试 docker compose up ...
    docker compose up -d 2>nul
    if errorlevel 1 (
        echo       Docker 不可用，尝试本地 uvicorn 启动 ...
        start "Ensemble-8000" cmd /k "cd /d \"%ROOT%\models\new_VOC\ensemble_docker\" && python -m uvicorn app:app --host 0.0.0.0 --port 8000"
    ) else (
        echo       Docker 容器已启动
    )
) else (
    echo       未找到 docker-compose.yml，跳过
)
echo.

REM ── 2. vocs_server (port 8001) — 可选 ──
echo [2/4] VOCs 实时数据服务 (vocs_server:8001) ...
if exist "%ROOT%\vocs_server.py" (
    start "VOCs-Server-8001" cmd /k "cd /d \"%ROOT%\" && python vocs_server.py"
    echo       vocs_server.py 已在新窗口启动
) else (
    echo       未找到 vocs_server.py，跳过（将使用 CSV fallback）
)
echo.

REM ── 3. admin backend (port 8003) ──
echo [3/4] 管理端后端 (admin backend:8003) ...
start "Admin-Backend-8003" cmd /k "cd /d \"%ADMIN%backend\" && python -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload"
echo       admin backend 已在新窗口启动
echo.

REM ── 等待后端就绪 ──
echo       等待后端启动 (3秒) ...
timeout /t 3 /nobreak >nul

REM ── 4. admin frontend (port 3001) ──
echo [4/4] 管理端前端 (admin frontend:3001) ...
start "Admin-Frontend-3001" cmd /k "cd /d \"%ADMIN%frontend\" && npm run dev"
echo       admin frontend 已在新窗口启动
echo.

echo ============================================================
echo   所有服务已启动！
echo.
echo   前端地址:    http://localhost:3001
echo   后端 API:    http://localhost:8003/docs
echo   Ensemble:    http://localhost:8000/health
echo   VOCs SSE:    http://localhost:8001/status
echo.
echo   默认登录:    admin / admin123456
echo ============================================================
echo.
echo 按任意键关闭此窗口（各服务窗口独立运行）...
pause >nul
