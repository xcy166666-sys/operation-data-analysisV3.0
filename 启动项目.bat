@echo off
chcp 65001 >nul
echo ========================================
echo 运营数据分析系统 - 启动脚本
echo ========================================
echo.

echo [1/3] 启动后端服务（Docker）...
docker-compose up -d
if %errorlevel% neq 0 (
    echo ❌ 后端启动失败！
    pause
    exit /b 1
)
echo ✅ 后端服务已启动
echo.

echo [2/3] 等待后端服务就绪...
timeout /t 15 /nobreak >nul
echo ✅ 后端服务就绪
echo.

echo [3/3] 启动前端服务...
echo 提示：前端将在新窗口中启动
echo.
start "前端服务" cmd /k "cd frontend && npm run dev"
echo ✅ 前端服务已启动
echo.

echo ========================================
echo 🎉 项目启动完成！
echo ========================================
echo.
echo 访问地址：
echo   前端：http://localhost:5173
echo   后端：http://localhost:21810
echo   API文档：http://localhost:21810/docs
echo.
echo 按任意键查看服务状态...
pause >nul

docker-compose ps

echo.
echo 按任意键退出...
pause >nul
