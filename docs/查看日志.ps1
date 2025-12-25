# 查看后端日志脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  运营数据分析系统 - 日志查看工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 日志位置说明
Write-Host "日志位置：" -ForegroundColor Yellow
Write-Host "1. Docker容器日志（实时查看）" -ForegroundColor White
Write-Host "   - 命令: docker-compose logs backend -f" -ForegroundColor Gray
Write-Host "   - 命令: docker-compose logs backend --tail 100" -ForegroundColor Gray
Write-Host ""

Write-Host "2. Docker Volume（持久化存储）" -ForegroundColor White
Write-Host "   - Volume名称: operation-data-analysis_v20_backend_logs_v2" -ForegroundColor Gray
Write-Host "   - 容器内路径: /var/log/operation-analysis/" -ForegroundColor Gray
Write-Host "   - 主机路径: C:\ProgramData\docker\volumes\operation-data-analysis_v20_backend_logs_v2\_data" -ForegroundColor Gray
Write-Host ""

Write-Host "3. 本地保存的日志文件" -ForegroundColor White
Write-Host "   - backend_recent_logs.txt（最近100条日志）" -ForegroundColor Gray
Write-Host ""

# 选项菜单
Write-Host "请选择操作：" -ForegroundColor Yellow
Write-Host "1. 查看最近100条日志" -ForegroundColor White
Write-Host "2. 实时查看日志（按Ctrl+C退出）" -ForegroundColor White
Write-Host "3. 查看包含'报告生成'的日志" -ForegroundColor White
Write-Host "4. 查看包含'Dify'的日志" -ForegroundColor White
Write-Host "5. 查看包含'图表'的日志" -ForegroundColor White
Write-Host "6. 查看所有错误日志" -ForegroundColor White
Write-Host "7. 保存日志到文件" -ForegroundColor White
Write-Host ""

$choice = Read-Host "请输入选项 (1-7)"

switch ($choice) {
    "1" {
        Write-Host "`n正在获取最近100条日志..." -ForegroundColor Green
        docker-compose logs backend --tail 100
    }
    "2" {
        Write-Host "`n开始实时查看日志（按Ctrl+C退出）..." -ForegroundColor Green
        docker-compose logs backend -f
    }
    "3" {
        Write-Host "`n正在查找报告生成相关日志..." -ForegroundColor Green
        docker-compose logs backend --tail 500 | Select-String -Pattern "报告生成|generate_report|text_length"
    }
    "4" {
        Write-Host "`n正在查找Dify相关日志..." -ForegroundColor Green
        docker-compose logs backend --tail 500 | Select-String -Pattern "Dify|dify|文字生成"
    }
    "5" {
        Write-Host "`n正在查找图表相关日志..." -ForegroundColor Green
        docker-compose logs backend --tail 500 | Select-String -Pattern "图表|chart|Chart|Bailian"
    }
    "6" {
        Write-Host "`n正在查找错误日志..." -ForegroundColor Green
        docker-compose logs backend --tail 500 | Select-String -Pattern "error|Error|ERROR|失败|异常"
    }
    "7" {
        $filename = "backend_logs_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
        Write-Host "`n正在保存日志到 $filename ..." -ForegroundColor Green
        docker-compose logs backend --tail 1000 > $filename 2>&1
        Write-Host "✅ 日志已保存到: $filename" -ForegroundColor Green
        Write-Host "文件大小: $((Get-Item $filename).Length) bytes" -ForegroundColor Gray
    }
    default {
        Write-Host "无效选项" -ForegroundColor Red
    }
}

Write-Host "`n按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

