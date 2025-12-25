@echo off
chcp 65001 >nul
echo ========================================
echo Docker服务诊断脚本
echo ========================================
echo.

echo [1/6] 检查Docker服务状态...
docker compose ps
echo.

echo [2/6] 检查后端容器日志（最近50行）...
echo ----------------------------------------
docker logs operation-analysis-v2-backend --tail 50
echo.

echo [3/6] 检查数据库容器日志（最近20行）...
echo ----------------------------------------
docker logs operation-analysis-v2-postgres --tail 20
echo.

echo [4/6] 检查Redis容器日志（最近20行）...
echo ----------------------------------------
docker logs operation-analysis-v2-redis --tail 20
echo.

echo [5/6] 测试后端健康检查...
echo ----------------------------------------
curl -s http://localhost:21810/health
echo.
echo.

echo [6/6] 测试数据库连接...
echo ----------------------------------------
docker exec operation-analysis-v2-backend python -c "from app.core.database import engine; from sqlalchemy import text; conn = engine.connect(); result = conn.execute(text('SELECT 1')); print('✓ 数据库连接成功'); conn.close()"
echo.

echo ========================================
echo 诊断完成
echo ========================================
echo.
echo 如果看到错误，请检查：
echo 1. .env 文件是否配置正确
echo 2. 数据库密码是否正确
echo 3. 端口是否被占用
echo.
pause
