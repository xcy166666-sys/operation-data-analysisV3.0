#!/usr/bin/env python3
"""
修复 operation.py 中的 Path 导入问题
将文件路径相关的 Path 改为 FilePath
"""
import re

# 读取文件 - 尝试多种编码
encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
content = None

for encoding in encodings:
    try:
        with open('backend/app/api/v1/operation.py', 'r', encoding=encoding) as f:
            content = f.read()
        print(f"✅ 使用 {encoding} 编码读取成功")
        break
    except UnicodeDecodeError:
        continue

if content is None:
    print("❌ 无法读取文件")
    exit(1)

# 替换文件路径相关的 Path( 为 FilePath(
# 但保留 FastAPI 参数中的 Path(
patterns = [
    (r'file_ext = Path\(file\.filename\)', r'file_ext = FilePath(file.filename)'),
    (r'upload_dir = Path\(f"uploads/', r'upload_dir = FilePath(f"uploads/'),
    (r'batch_dir = Path\(f"uploads/', r'batch_dir = FilePath(f"uploads/'),
    (r'split_path = Path\(sheet_info\["split_file_path"\]\)', r'split_path = FilePath(sheet_info["split_file_path"])'),
    (r'file_name_without_ext = Path\(file\.filename\)', r'file_name_without_ext = FilePath(file.filename)'),
    (r'file_name_without_ext = Path\(user_message\["file_name"\]\)', r'file_name_without_ext = FilePath(user_message["file_name"])'),
    (r'file_path = Path\(settings\.UPLOAD_DIR\)', r'file_path = FilePath(settings.UPLOAD_DIR)'),
]

count = 0
for pattern, replacement in patterns:
    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        count += re.subn(pattern, replacement, content)[1]
        content = new_content

# 写回文件
with open('backend/app/api/v1/operation.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ 修复完成！共替换 {count} 处")
print("已将文件路径相关的 Path 改为 FilePath")
