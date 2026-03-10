# 检查app.py的缩进问题
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到main函数
main_start = None
for i, line in enumerate(lines, 1):
    if line.strip().startswith('def main('):
        main_start = i
        break

print(f"main函数开始于行: {main_start}")

# 检查tab4和tab5之间的代码
tab4_line = None
tab5_line = None
for i, line in enumerate(lines, 1):
    if 'with tab4:' in line:
        tab4_line = i
    if 'with tab5:' in line:
        tab5_line = i

print(f"tab4开始于行: {tab4_line}")
print(f"tab5开始于行: {tab5_line}")

# 显示tab4和tab5之间的代码
print("\n=== tab4和tab5之间的代码 ===")
for i in range(tab4_line, min(tab5_line + 10, len(lines) + 1)):
    line = lines[i-1]
    indent = len(line) - len(line.lstrip())
    print(f"行{i}: 缩进{indent} | {line.rstrip()}")
