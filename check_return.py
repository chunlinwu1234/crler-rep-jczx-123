with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到所有return语句和tab的位置
returns = []
tabs = []

for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped == 'return' or stripped.startswith('return '):
        indent = len(line) - len(line.lstrip())
        returns.append((i, indent, stripped))
    if 'with tab' in line and ':' in line:
        indent = len(line) - len(line.lstrip())
        tabs.append((i, indent, stripped))

print("Return语句位置:")
for line_num, indent, content in returns:
    print(f'  行{line_num}: 缩进{indent} - {content}')

print("\nTab位置:")
for line_num, indent, content in tabs:
    print(f'  行{line_num}: 缩进{indent} - {content}')

# 检查每个return属于哪个tab
print("\nReturn所属Tab分析:")
for ret_line, ret_indent, ret_content in returns:
    # 找到这个return所属的tab
    parent_tab = None
    for tab_line, tab_indent, tab_content in tabs:
        if tab_line < ret_line and tab_indent < ret_indent:
            parent_tab = (tab_line, tab_indent, tab_content)
    if parent_tab:
        print(f'  行{ret_line}的return属于: 行{parent_tab[0]} {parent_tab[2]}')
    else:
        print(f'  行{ret_line}的return: 无父级tab')
