#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量自动配置脚本
使用方法: python scripts/setup_env.py
"""
import os
import secrets
import string
from pathlib import Path

def generate_random_string(length=32):
    """生成随机字符串"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def main():
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("=" * 50)
    print("  运营数据分析系统 - 环境变量自动配置")
    print("=" * 50)
    print()
    
    # 检查.env.example文件
    env_example = project_root / ".env.example"
    if not env_example.exists():
        print("[ERROR] 错误: .env.example 文件不存在！")
        print("请先确保项目文件完整。")
        return 1
    
    # 检查.env文件是否已存在
    env_file = project_root / ".env"
    if env_file.exists():
        print("[WARN] 警告: .env 文件已存在")
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = project_root / f".env.backup.{timestamp}"
        import shutil
        shutil.copy2(env_file, backup)
        print(f"已备份现有配置到: {backup.name}")
        print()
    
    # 读取模板文件
    print("正在创建 .env 文件...")
    content = env_example.read_text(encoding='utf-8')
    
    # 生成随机密码和密钥
    db_password = generate_random_string(24)
    jwt_secret = generate_random_string(64)
    
    print("正在生成随机密码和密钥...")
    
    # 替换配置项
    content = content.replace(
        "POSTGRES_PASSWORD=your_password_here",
        f"POSTGRES_PASSWORD={db_password}"
    )
    content = content.replace(
        "JWT_SECRET=your_jwt_secret_key_here_change_in_production",
        f"JWT_SECRET={jwt_secret}"
    )
    
    # 保存.env文件
    env_file.write_text(content, encoding='utf-8')
    
    print()
    print("=" * 50)
    print("  配置完成！")
    print("=" * 50)
    print()
    print("已自动生成以下配置：")
    print(f"  [OK] 数据库密码: {db_password}")
    print(f"  [OK] JWT密钥: {jwt_secret}")
    print()
    print("重要提示：")
    print("  1. 请妥善保管生成的密码和密钥")
    print("  2. 如需配置Dify，请手动编辑 .env 文件")
    print("  3. 生产环境请确保 DEBUG=false")
    print()
    print("下一步：")
    print("  1. 检查 .env 文件中的配置")
    print("  2. 运行: docker-compose up -d")
    print("  3. 运行: docker-compose exec backend alembic upgrade head")
    print("  4. 运行: docker-compose exec backend python scripts/create_admin.py")
    print()
    
    return 0

if __name__ == "__main__":
    exit(main())

