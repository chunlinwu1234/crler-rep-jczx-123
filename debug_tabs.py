# 检查app.py中的tab结构
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# 找到main函数
def find_function_bounds(lines, func_name):
    start = None
    indent_level = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f'def {func_name}('):
            start = i
            indent_level = len(line) - len(line.lstrip())
            break
    
    if start is None:
        return None, None
    
    # 找到函数结束
    end = start + 1
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.strip() == '':
            end = i
            continue
        current_indent = len(line) - len(line.lstrip())
        if current_indent <= indent_level and line.strip():
            end = i
            break
        end = i
    
    return start, end

main_start, main_end = find_function_bounds(lines, 'main')
print(f"main函数: 行{main_start+1} 到 行{main_end+1}")

# 分析main函数内部的结构
if main_start and main_end:
    main_lines = lines[main_start:main_end+1]
    base_indent = len(lines[main_start]) - len(lines[main_start].lstrip())
    
    print(f"\nmain函数基础缩进: {base_indent}")
    print("\n主要结构:")
    
    for i, line in enumerate(main_lines, main_start+1):
        stripped = line.strip()
        if not stripped:
            continue
        indent = len(line) - len(line.lstrip()) - base_indent
        
        # 显示关键结构
        if stripped.startswith(('with tab', 'tab1, tab2', 'def ', 'if ', 'for ', 'while ')):
            print(f"  行{i}: 缩进{indent} - {stripped[:60]}")
        elif 'return' in stripped and stripped.startswith('return'):
            print(f"  行{i}: 缩进{indent} - [RETURN] {stripped[:40]}")
