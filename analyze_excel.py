"""
分析tushare财务数据结构Excel文件
"""
import pandas as pd
import json

# 读取Excel文件
excel_file = r'd:\project\CIMS\tushare财务数据结构.xlsx'

# 获取所有sheet名称
xl = pd.ExcelFile(excel_file)
print("=" * 80)
print("Excel文件包含以下工作表：")
print("=" * 80)
for i, sheet_name in enumerate(xl.sheet_names, 1):
    print(f"{i}. {sheet_name}")

print("\n" + "=" * 80)
print("各工作表结构分析：")
print("=" * 80)

# 分析每个sheet的结构
all_structure = {}

for sheet_name in xl.sheet_names:
    print(f"\n{'='*60}")
    print(f"工作表: {sheet_name}")
    print('='*60)
    
    # 读取sheet
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    # 基本信息
    print(f"行数: {len(df)}")
    print(f"列数: {len(df.columns)}")
    print(f"\n列名:")
    
    # 显示列信息
    for col in df.columns:
        print(f"  - {col}")
    
    # 显示前几行数据
    print(f"\n前5行数据预览:")
    print(df.head().to_string())
    
    # 保存结构信息
    all_structure[sheet_name] = {
        'columns': list(df.columns),
        'row_count': len(df),
        'sample_data': df.head(3).to_dict('records') if len(df) > 0 else []
    }

# 保存结构分析结果
with open(r'd:\project\CIMS\excel_structure.json', 'w', encoding='utf-8') as f:
    json.dump(all_structure, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 80)
print("结构分析已保存到 excel_structure.json")
print("=" * 80)
