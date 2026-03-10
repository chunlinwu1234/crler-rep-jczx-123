# 检查app.py的结构
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到所有with语句
with_statements = []
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped.startswith('with '):
        indent = len(line) - len(line.lstrip())
        with_statements.append((i, indent, stripped))

print("所有with语句:")
print("=" * 80)

for line_num, indent, content in with_statements:
    print(f"  行{line_num}: 缩进{indent} - {content}")

# 找到main函数的结束
main_start = None
main_end = None
for i, line in enumerate(lines, 1):
    if line.strip().startswith('def main('):
        main_start = i
    if main_start and line.strip() == 'if __name__ == "__main__":':
        main_end = i
        break

print(f"\nmain函数: 行{main_start} 到 行{main_end-1}")

# 检查tab相关的with语句
tab_related = []
for line_num, indent, content in with_statements:
    if 'tab' in content:
        tab_related.append((line_num, indent, content))

print("\nTab相关的with语句:")
for line_num, indent, content in tab_related:
    print(f"  行{line_num}: 缩进{indent} - {content}")
