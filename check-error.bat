@echo off
chcp 65001 >nul
echo ========================================
echo 检查后端错误
echo ========================================
echo.

echo [1] 后端容器状态：
docker ps --filter name=operation-analysis-v2-backend --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.

echo [2] 最近的错误日志（最近100行）：
echo ----------------------------------------
docker logs operation-analysis-v2-backend --tail 100 2>&1 | findstr /i "error exception traceback failed"
echo.

echo [3] 完整日志（最近50行）：
echo ----------------------------------------
docker logs operation-analysis-v2-backend --tail 50
echo.

echo [4] 测试健康检查：
curl -s http://localhost:21810/health
echo.
echo.

echo [5] 测试数据库连接：
docker exec operation-analysis-v2-backend python -c "from app.core.database import SessionLocal; db = SessionLocal(); print('✓ 数据库连接成功'); db.close()" 2>&1
echo.

echo ========================================
pause
