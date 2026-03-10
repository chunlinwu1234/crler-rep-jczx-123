with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到tab4的开始和结束
tab4_start = None
tab5_start = None

for i, line in enumerate(lines, 1):
    if 'with tab4:' in line:
        tab4_start = i
    if 'with tab5:' in line:
        tab5_start = i

print(f'tab4 开始于行: {tab4_start}')
print(f'tab5 开始于行: {tab5_start}')

# 检查tab4内部的缩进结构
if tab4_start and tab5_start:
    print(f'\ntab4 内部结构 (行 {tab4_start} 到 {tab5_start-1}):')
    
    # 找到所有缩进级别变化的地方
    prev_indent = 4  # tab4本身是4个空格
    for i in range(tab4_start, min(tab5_start, len(lines) + 1)):
        line = lines[i - 1]  # 列表索引从0开始
        stripped = line.strip()
        
        # 只显示关键行（控制流语句）
        if stripped and not stripped.startswith('#'):
            indent = len(line) - len(line.lstrip())
            if stripped.startswith(('if ', 'else:', 'elif ', 'for ', 'while ', 'with ', 'def ', 'class ')):
                print(f'  行{i}: 缩进{indent} - {stripped[:60]}...')
