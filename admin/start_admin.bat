@echo off
setlocal
chcp 65001 >nul
title Smart Clean Park - Admin Launcher

set "ADMIN=%~dp0"
for %%I in ("%ADMIN%..") do set "ROOT=%%~fI"
set "ENSEMBLE_DIR=%ROOT%\models\new_VOC\ensemble_docker"
set "ADMIN_BACKEND_DIR=%ADMIN%backend"
set "ADMIN_FRONTEND_DIR=%ADMIN%frontend"
set "VOCS_SERVER=%ROOT%\vocs_server.py"

echo ============================================================
echo   Smart Clean Park - Admin Service Launcher
echo ============================================================
echo.

echo [1/4] Start ensemble_docker on port 8000...
if exist "%ENSEMBLE_DIR%\docker-compose.yml" (
    pushd "%ENSEMBLE_DIR%"
    docker compose up -d >nul 2>nul
    if errorlevel 1 (
        echo       docker compose failed. Fallback to local uvicorn.
        start "Ensemble-8000" /D "%ENSEMBLE_DIR%" cmd /k "python -m uvicorn app:app --host 0.0.0.0 --port 8000"
    ) else (
        echo       docker compose up -d started successfully.
    )
    popd
) else (
    if exist "%ENSEMBLE_DIR%\app.py" (
        echo       docker-compose.yml not found. Fallback to local uvicorn.
        start "Ensemble-8000" /D "%ENSEMBLE_DIR%" cmd /k "python -m uvicorn app:app --host 0.0.0.0 --port 8000"
    ) else (
        echo       ensemble_docker directory not found. Skipped.
    )
)
echo.

echo [2/4] Start vocs_server on port 8001...
if exist "%VOCS_SERVER%" (
    start "VOCs-Server-8001" /D "%ROOT%" cmd /k "python vocs_server.py"
    echo       vocs_server.py started in a new window.
) else (
    echo       vocs_server.py not found. Skipped.
)
echo.

echo [3/4] Start admin backend on port 8003...
if exist "%ADMIN_BACKEND_DIR%\main.py" (
    start "Admin-Backend-8003" /D "%ADMIN_BACKEND_DIR%" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8003 --reload"
    echo       Admin backend started in a new window.
) else (
    echo       %ADMIN_BACKEND_DIR%\main.py not found. Skipped.
)
echo.

echo       Wait 3 seconds for backend startup...
timeout /t 3 /nobreak >nul
echo.

echo [4/4] Start admin frontend on port 3001...
if exist "%ADMIN_FRONTEND_DIR%\package.json" (
    start "Admin-Frontend-3001" /D "%ADMIN_FRONTEND_DIR%" cmd /k "npm run dev"
    echo       Admin frontend started in a new window.
) else (
    echo       %ADMIN_FRONTEND_DIR%\package.json not found. Skipped.
)
echo.

echo ============================================================
echo   Startup commands have been issued.
echo.
echo   Frontend:      http://localhost:3001
echo   Admin backend: http://localhost:8003/docs
echo   Ensemble:      http://localhost:8000/health
echo   VOCs SSE:      http://localhost:8001/status
echo.
echo   Note: Vite proxy should point /api to http://localhost:8003
echo ============================================================
echo.
echo Press any key to close this launcher window...
pause >nul
