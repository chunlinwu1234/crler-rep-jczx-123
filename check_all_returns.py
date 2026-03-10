# 检查所有return语句的位置和上下文
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("所有return语句分析:")
print("=" * 80)

for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped.startswith('return') and not stripped.startswith('return_'):
        indent = len(line) - len(line.lstrip())
        
        # 找到上下文（前5行）
        context_start = max(0, i - 6)
        context = lines[context_start:i-1]
        
        print(f"\n行{i}: 缩进{indent} - {stripped}")
        print("上下文:")
        for j, ctx_line in enumerate(context, context_start + 1):
            ctx_stripped = ctx_line.rstrip()
            if ctx_stripped:
                print(f"  行{j}: {ctx_stripped}")
