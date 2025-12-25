import ast
import sys

# 读取文件内容
file_path = "c:\\Users\\chunyu.xing\\Desktop\\Coding\\operation-data-analysis_V3.0\\backend\\app\\api\\v1\\operation.py"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

try:
    # 解析为抽象语法树
    tree = ast.parse(content)
    print("文件语法正确！")
except SyntaxError as e:
    print(f"语法错误: {e}")
    print(f"错误位置: 行 {e.lineno}, 列 {e.offset}")
    # 打印错误位置附近的代码
    lines = content.splitlines()
    start = max(0, e.lineno - 5)
    end = min(len(lines), e.lineno + 5)
    for i in range(start, end):
        line_num = i + 1
        marker = "---> " if line_num == e.lineno else "     "
        print(f"{marker}{line_num:3}: {lines[i]}")
        if line_num == e.lineno:
            print(f"     {' ' * (e.offset)}^")
    sys.exit(1)
