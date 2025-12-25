@echo off
chcp 65001 >nul
echo ========================================
echo 启动本地开发环境后端服务
echo ========================================
echo.

REM 检查是否在 backend 目录
if not exist "main.py" (
    echo [错误] 请在 backend 目录下运行此脚本
    pause
    exit /b 1
)

REM 设置环境变量文件
set ENV_FILE=.env.local
echo [信息] 使用环境变量文件: %ENV_FILE%
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或未添加到 PATH
    pause
    exit /b 1
)

REM 检查依赖是否安装
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [警告] 依赖未安装，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

REM 检查数据库和 Redis 是否运行
echo [信息] 检查数据库和 Redis 连接...
docker ps | findstr "postgres" >nul 2>&1
if errorlevel 1 (
    echo [警告] PostgreSQL 容器未运行，正在启动...
    docker-compose up -d postgres
)

docker ps | findstr "redis" >nul 2>&1
if errorlevel 1 (
    echo [警告] Redis 容器未运行，正在启动...
    docker-compose up -d redis
)

echo.
echo [信息] 启动后端服务...
echo [信息] 访问地址: http://localhost:8000
echo [信息] API 文档: http://localhost:8000/docs
echo [信息] 按 Ctrl+C 停止服务
echo.

REM 启动服务
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
