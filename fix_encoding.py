#!/usr/bin/env python3
"""
修复 operation.py 的编码问题
"""

# 读取文件 - 使用 latin-1
with open('backend/app/api/v1/operation.py', 'r', encoding='latin-1') as f:
    content = f.read()

# 写回文件 - 使用 utf-8
with open('backend/app/api/v1/operation.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 编码修复完成！")
