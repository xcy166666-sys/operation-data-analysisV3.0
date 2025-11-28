# 环境变量快速配置脚本 (PowerShell)
# 使用方法: .\scripts\setup-env.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  运营数据分析系统 - 环境变量配置" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查.env文件是否已存在
if (Test-Path ".env") {
    $overwrite = Read-Host ".env 文件已存在，是否覆盖？(y/N)"
    if ($overwrite -ne "y" -and $overwrite -ne "Y") {
        Write-Host "已取消操作" -ForegroundColor Yellow
        exit
    }
}

# 复制模板文件
Write-Host "正在创建 .env 文件..." -ForegroundColor Green
Copy-Item ".env.example" ".env" -Force

Write-Host ""
Write-Host "请配置以下必需项：" -ForegroundColor Yellow
Write-Host ""

# 生成随机密码函数
function Generate-RandomString {
    param([int]$Length = 32)
    $chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    $random = New-Object System.Random
    $result = ""
    for ($i = 0; $i -lt $Length; $i++) {
        $result += $chars[$random.Next(0, $chars.Length)]
    }
    return $result
}

# 配置数据库密码
Write-Host "1. 数据库密码配置" -ForegroundColor Cyan
$generateDbPassword = Read-Host "是否自动生成数据库密码？(Y/n)"
if ($generateDbPassword -ne "n" -and $generateDbPassword -ne "N") {
    $dbPassword = Generate-RandomString -Length 24
    Write-Host "已生成数据库密码: $dbPassword" -ForegroundColor Green
    (Get-Content ".env") -replace "POSTGRES_PASSWORD=your_password_here", "POSTGRES_PASSWORD=$dbPassword" | Set-Content ".env"
} else {
    $dbPassword = Read-Host "请输入数据库密码（至少12位）"
    (Get-Content ".env") -replace "POSTGRES_PASSWORD=your_password_here", "POSTGRES_PASSWORD=$dbPassword" | Set-Content ".env"
}

Write-Host ""

# 配置JWT密钥
Write-Host "2. JWT密钥配置" -ForegroundColor Cyan
$generateJwtSecret = Read-Host "是否自动生成JWT密钥？(Y/n)"
if ($generateJwtSecret -ne "n" -and $generateJwtSecret -ne "N") {
    $jwtSecret = Generate-RandomString -Length 64
    Write-Host "已生成JWT密钥" -ForegroundColor Green
    (Get-Content ".env") -replace "JWT_SECRET=your_jwt_secret_key_here_change_in_production", "JWT_SECRET=$jwtSecret" | Set-Content ".env"
} else {
    $jwtSecret = Read-Host "请输入JWT密钥（建议至少32位）"
    (Get-Content ".env") -replace "JWT_SECRET=your_jwt_secret_key_here_change_in_production", "JWT_SECRET=$jwtSecret" | Set-Content ".env"
}

Write-Host ""

# 配置Dify
Write-Host "3. Dify配置（可选）" -ForegroundColor Cyan
$configureDify = Read-Host "是否现在配置Dify？(y/N)"
if ($configureDify -eq "y" -or $configureDify -eq "Y") {
    $difyApiKey = Read-Host "请输入Dify API密钥"
    $difyApiUrl = Read-Host "请输入Dify API地址（默认: https://api.dify.ai/v1）"
    if ([string]::IsNullOrWhiteSpace($difyApiUrl)) {
        $difyApiUrl = "https://api.dify.ai/v1"
    }
    (Get-Content ".env") -replace "DIFY_API_KEY=your_dify_api_key_here", "DIFY_API_KEY=$difyApiKey" | Set-Content ".env"
    (Get-Content ".env") -replace "DIFY_API_URL=https://api.dify.ai/v1", "DIFY_API_URL=$difyApiUrl" | Set-Content ".env"
    Write-Host "Dify配置已保存" -ForegroundColor Green
}

Write-Host ""

# 配置CORS
Write-Host "4. CORS配置" -ForegroundColor Cyan
$corsOrigins = Read-Host "请输入允许的前端地址（多个用逗号分隔，默认: http://localhost:80）"
if ([string]::IsNullOrWhiteSpace($corsOrigins)) {
    $corsOrigins = "http://localhost:80"
}
(Get-Content ".env") -replace "CORS_ORIGINS=http://localhost:5173,http://localhost:80,http://localhost:3000", "CORS_ORIGINS=$corsOrigins" | Set-Content ".env"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  配置完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "下一步：" -ForegroundColor Yellow
Write-Host "1. 检查 .env 文件中的配置是否正确" -ForegroundColor White
Write-Host "2. 运行 docker-compose up -d 启动服务" -ForegroundColor White
Write-Host "3. 运行数据库迁移: docker-compose exec backend alembic upgrade head" -ForegroundColor White
Write-Host "4. 创建管理员用户: docker-compose exec backend python scripts/create_admin.py" -ForegroundColor White
Write-Host ""

