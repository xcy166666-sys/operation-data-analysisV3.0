# 环境变量自动配置脚本 (PowerShell) - 非交互式版本
# 使用方法: .\scripts\setup-env-auto.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  运营数据分析系统 - 环境变量自动配置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查.env.example文件是否存在
if (-not (Test-Path ".env.example")) {
    Write-Host "错误: .env.example 文件不存在！" -ForegroundColor Red
    Write-Host "请先确保项目文件完整。" -ForegroundColor Red
    exit 1
}

# 检查.env文件是否已存在
if (Test-Path ".env") {
    Write-Host "警告: .env 文件已存在" -ForegroundColor Yellow
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backup = ".env.backup.$timestamp"
    Copy-Item ".env" $backup
    Write-Host "已备份现有配置到: $backup" -ForegroundColor Yellow
    Write-Host ""
}

# 生成随机密码函数
function Generate-RandomString {
    param([int]$Length = 32)
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    $random = New-Object System.Random
    $result = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $result += $chars[$random.Next(0, $chars.Length)]
    }
    return $result
}

# 复制模板文件
Write-Host "正在创建 .env 文件..." -ForegroundColor Green
Copy-Item ".env.example" ".env" -Force

# 读取.env文件内容
$envContent = Get-Content ".env" -Raw

# 生成随机密码和密钥
$dbPassword = Generate-RandomString -Length 24
$jwtSecret = Generate-RandomString -Length 64
$sessionSecret = Generate-RandomString -Length 64

Write-Host ""
Write-Host "正在生成随机密码和密钥..." -ForegroundColor Green

# 替换配置项
$envContent = $envContent -replace "POSTGRES_PASSWORD=your_password_here", "POSTGRES_PASSWORD=$dbPassword"
$envContent = $envContent -replace "JWT_SECRET=your_jwt_secret_key_here_change_in_production", "JWT_SECRET=$jwtSecret"

# 保存配置
$envContent | Out-File -FilePath ".env" -Encoding UTF8 -NoNewline

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "已自动生成以下配置：" -ForegroundColor Cyan
Write-Host "  ✓ 数据库密码: $dbPassword" -ForegroundColor White
Write-Host "  ✓ JWT密钥: $jwtSecret" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  重要提示：" -ForegroundColor Yellow
Write-Host "  1. 请妥善保管生成的密码和密钥" -ForegroundColor White
Write-Host "  2. 如需配置Dify，请手动编辑 .env 文件" -ForegroundColor White
Write-Host "  3. 生产环境请确保 DEBUG=false" -ForegroundColor White
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "  1. 检查 .env 文件中的配置" -ForegroundColor White
Write-Host "  2. 运行: docker-compose up -d" -ForegroundColor White
Write-Host "  3. 运行: docker-compose exec backend alembic upgrade head" -ForegroundColor White
Write-Host "  4. 运行: docker-compose exec backend python scripts/create_admin.py" -ForegroundColor White
Write-Host ""
