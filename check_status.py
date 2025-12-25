"""检查项目配置状态"""
import sys
import os

# 检查环境变量
print("=" * 50)
print("项目运行状态检查")
print("=" * 50)

# 检查Docker服务
print("\n1. Docker服务状态:")
os.system("docker-compose ps")

# 检查后端日志
print("\n2. 后端服务日志（最后10行）:")
os.system("docker-compose logs backend --tail 10")

print("\n" + "=" * 50)
print("检查完成！")
print("=" * 50)


