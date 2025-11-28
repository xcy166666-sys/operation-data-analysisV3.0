#!/bin/bash
# 环境变量快速配置脚本 (Bash)
# 使用方法: chmod +x scripts/setup-env.sh && ./scripts/setup-env.sh

echo "========================================"
echo "  运营数据分析系统 - 环境变量配置"
echo "========================================"
echo ""

# 检查.env文件是否已存在
if [ -f ".env" ]; then
    read -p ".env 文件已存在，是否覆盖？(y/N): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "已取消操作"
        exit 0
    fi
fi

# 复制模板文件
echo "正在创建 .env 文件..."
cp .env.example .env

echo ""
echo "请配置以下必需项："
echo ""

# 配置数据库密码
echo "1. 数据库密码配置"
read -p "是否自动生成数据库密码？(Y/n): " generate_db_password
if [ "$generate_db_password" != "n" ] && [ "$generate_db_password" != "N" ]; then
    db_password=$(openssl rand -base64 24 | tr -d "=+/" | cut -c1-24)
    echo "已生成数据库密码: $db_password"
    sed -i.bak "s/POSTGRES_PASSWORD=your_password_here/POSTGRES_PASSWORD=$db_password/" .env
    rm -f .env.bak
else
    read -p "请输入数据库密码（至少12位）: " db_password
    sed -i.bak "s/POSTGRES_PASSWORD=your_password_here/POSTGRES_PASSWORD=$db_password/" .env
    rm -f .env.bak
fi

echo ""

# 配置JWT密钥
echo "2. JWT密钥配置"
read -p "是否自动生成JWT密钥？(Y/n): " generate_jwt_secret
if [ "$generate_jwt_secret" != "n" ] && [ "$generate_jwt_secret" != "N" ]; then
    jwt_secret=$(openssl rand -hex 32)
    echo "已生成JWT密钥"
    sed -i.bak "s/JWT_SECRET=your_jwt_secret_key_here_change_in_production/JWT_SECRET=$jwt_secret/" .env
    rm -f .env.bak
else
    read -p "请输入JWT密钥（建议至少32位）: " jwt_secret
    sed -i.bak "s/JWT_SECRET=your_jwt_secret_key_here_change_in_production/JWT_SECRET=$jwt_secret/" .env
    rm -f .env.bak
fi

echo ""

# 配置Dify
echo "3. Dify配置（可选）"
read -p "是否现在配置Dify？(y/N): " configure_dify
if [ "$configure_dify" == "y" ] || [ "$configure_dify" == "Y" ]; then
    read -p "请输入Dify API密钥: " dify_api_key
    read -p "请输入Dify API地址（默认: https://api.dify.ai/v1）: " dify_api_url
    if [ -z "$dify_api_url" ]; then
        dify_api_url="https://api.dify.ai/v1"
    fi
    sed -i.bak "s/DIFY_API_KEY=your_dify_api_key_here/DIFY_API_KEY=$dify_api_key/" .env
    sed -i.bak "s|DIFY_API_URL=https://api.dify.ai/v1|DIFY_API_URL=$dify_api_url|" .env
    rm -f .env.bak
    echo "Dify配置已保存"
fi

echo ""

# 配置CORS
echo "4. CORS配置"
read -p "请输入允许的前端地址（多个用逗号分隔，默认: http://localhost:80）: " cors_origins
if [ -z "$cors_origins" ]; then
    cors_origins="http://localhost:80"
fi
sed -i.bak "s|CORS_ORIGINS=http://localhost:5173,http://localhost:80,http://localhost:3000|CORS_ORIGINS=$cors_origins|" .env
rm -f .env.bak

echo ""
echo "========================================"
echo "  配置完成！"
echo "========================================"
echo ""
echo "下一步："
echo "1. 检查 .env 文件中的配置是否正确"
echo "2. 运行 docker-compose up -d 启动服务"
echo "3. 运行数据库迁移: docker-compose exec backend alembic upgrade head"
echo "4. 创建管理员用户: docker-compose exec backend python scripts/create_admin.py"
echo ""

