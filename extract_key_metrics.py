"""
提取战略分析关键指标
"""
import pandas as pd
import json

excel_file = r'd:\project\CIMS\tushare财务数据结构.xlsx'

# 读取所有sheet
xl = pd.ExcelFile(excel_file)

# 定义战略分析关键指标筛选规则
key_metrics_rules = {
    '资产负债表': {
        '战略分析必需': [
            'ts_code', 'end_date', 'ann_date',  # 基础信息
            'total_assets', 'total_liab', 'total_hldr_eqy_exc_min_int',  # 资产负债权益
            'total_cur_assets', 'total_nca',  # 流动/非流动资产
            'total_cur_liab', 'total_ncl',  # 流动/非流动负债
            'money_cap', 'trad_asset', 'notes_receiv', 'accounts_receiv', 'inventories',  # 关键资产
            'goodwill', 'intan_assets', 'r_and_d',  # 无形资产、研发
            'fix_assets', 'cip', 'const_materials',  # 固定资产、在建工程
            'notes_payable', 'acct_payable', 'adv_receipts',  # 关键负债
        ],
        '竞争情报重要': [
            'oth_cur_assets', 'oth_cur_liab',  # 其他项目
            'defer_tax_assets', 'defer_tax_liab',  # 递延税
            'total_hldr_eqy_inc_min_int', 'minority_int',  # 权益明细
        ]
    },
    '利润表': {
        '战略分析必需': [
            'ts_code', 'end_date', 'ann_date',  # 基础信息
            'total_revenue', 'revenue',  # 营业收入
            'total_cogs', 'oper_cost',  # 营业成本
            'operate_profit', 'income_tax', 'n_income', 'n_income_attr_p',  # 利润
            'sell_exp', 'admin_exp', 'fin_exp', 'rd_exp',  # 期间费用
            'int_income', 'comm_income', 'other_income',  # 其他收益
            'impair_loss_assets', 'credit_impair_loss',  # 减值损失
        ],
        '竞争情报重要': [
            'prem_income', 'comm_exp', 'prem_refund',  # 保险相关
            'undist_profit', 'distable_profit',  # 利润分配
        ]
    },
    '现金流量表': {
        '战略分析必需': [
            'ts_code', 'end_date', 'ann_date',  # 基础信息
            'n_cashflow_act', 'n_cashflow_inv_act', 'n_cash_flows_fnc_act',  # 三类现金流
            'c_end_bal_cash', 'c_beg_bal_cash',  # 现金余额
            'im_net_cashflow_oper_act',  # 间接法经营现金流
        ],
        '竞争情报重要': [
            'proc_sell_invest', 'invest_pay_cash',  # 投资活动明细
            'c_paid_to_for_empl', 'c_paid_for_taxes',  # 支付给职工的现金、税费
        ]
    },
    '主营业务构成': {
        '战略分析必需': [
            'ts_code', 'end_date', 'bz_item', 'bz_sales', 'bz_profit',  # 主营业务
        ]
    },
    '业绩快报': {
        '战略分析必需': [
            'ts_code', 'end_date', 'ann_date',
            'revenue', 'operate_profit', 'total_profit', 'n_income', 'n_income_attr_p',
            'basic_eps', 'diluted_eps', 'total_assets', 'total_hldr_eqy_exc_min_int',
        ]
    },
    '财务指标': {
        '战略分析必需': [
            'ts_code', 'end_date', 'ann_date',
            'eps', 'dt_eps', 'total_revenue_ps', 'revenue_ps', 'capital_rese_ps',  # 每股指标
            'profit_dedt', 'grossprofit_margin', 'netprofit_margin',  # 盈利能力
            'roe', 'roa',  # 回报率
            'debt_to_assets', 'debt_to_eqt', 'current_ratio', 'quick_ratio',  # 偿债能力
            'turn_days', 'inv_turn', 'ar_turn', 'ca_turn', 'fa_turn', 'ta_turn',  # 营运能力
            'ocfps', 'cfps', 'free_cash_flow',  # 现金流指标
            'q_sales_yoy', 'q_op_yoy', 'q_profit_yoy',  # 成长能力
        ],
        '竞争情报重要': [
            'basic_eps_yoy', 'dt_eps_yoy', 'cfps_yoy', 'op_yoy', 'ebt_yoy', 'netprofit_yoy',  # 同比增长
            'tr_yoy', 'or_yoy', 'eq_yoy', 'assets_yoy',  # 同比增长
            'q_gsprofit_margin', 'q_profit_to_gr', 'q_saleexp_to_gr', 'q_adminexp_to_gr',  # 季度指标
            'roe_yearly', 'np_yoy', 'sales_yoy', 'op_yoy',  # 年度同比
        ]
    }
}

# 提取所有字段
all_metrics = {}
key_metrics_summary = {}

for sheet_name in xl.sheet_names:
    df = pd.read_excel(excel_file, sheet_name=sheet_name)
    
    print(f"\n{'='*80}")
    print(f"工作表: {sheet_name} ({len(df)}个字段)")
    print('='*80)
    
    # 所有字段
    all_fields = df['名称'].tolist()
    all_metrics[sheet_name] = all_fields
    
    # 筛选关键指标
    rules = key_metrics_rules.get(sheet_name, {})
    strategic_essential = rules.get('战略分析必需', [])
    competitive_intel = rules.get('竞争情报重要', [])
    
    # 匹配实际存在的字段
    existing_essential = [f for f in strategic_essential if f in all_fields]
    existing_competitive = [f for f in competitive_intel if f in all_fields]
    
    key_metrics_summary[sheet_name] = {
        'total_fields': len(all_fields),
        'strategic_essential': existing_essential,
        'competitive_intel': existing_competitive,
        'strategic_essential_count': len(existing_essential),
        'competitive_intel_count': len(existing_competitive)
    }
    
    print(f"\n【战略分析必需】({len(existing_essential)}个):")
    for i, field in enumerate(existing_essential, 1):
        desc = df[df['名称']==field]['描述'].values[0] if len(df[df['名称']==field]) > 0 else ''
        print(f"  {i:2d}. {field:30s} - {desc}")
    
    if existing_competitive:
        print(f"\n【竞争情报重要】({len(existing_competitive)}个):")
        for i, field in enumerate(existing_competitive, 1):
            desc = df[df['名称']==field]['描述'].values[0] if len(df[df['名称']==field]) > 0 else ''
            print(f"  {i:2d}. {field:30s} - {desc}")

# 保存分析结果
with open(r'd:\project\CIMS\key_metrics_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(key_metrics_summary, f, ensure_ascii=False, indent=2)

# 生成数据库字段映射
print("\n" + "="*80)
print("数据库字段映射建议")
print("="*80)

db_mapping = {
    '基础信息字段': ['ts_code', 'ann_date', 'f_ann_date', 'end_date', 'report_type', 'comp_type'],
    '资产负债表核心': key_metrics_summary.get('资产负债表', {}).get('strategic_essential', []),
    '利润表核心': key_metrics_summary.get('利润表', {}).get('strategic_essential', []),
    '现金流量表核心': key_metrics_summary.get('现金流量表', {}).get('strategic_essential', []),
    '财务指标核心': key_metrics_summary.get('财务指标', {}).get('strategic_essential', []),
}

for category, fields in db_mapping.items():
    print(f"\n【{category}】({len(fields)}个)")
    for field in fields:
        print(f"  - {field}")

# 统计信息
total_essential = sum(s['strategic_essential_count'] for s in key_metrics_summary.values())
total_competitive = sum(s['competitive_intel_count'] for s in key_metrics_summary.values())
total_all = sum(s['total_fields'] for s in key_metrics_summary.values())

print("\n" + "="*80)
print("统计汇总")
print("="*80)
print(f"总字段数: {total_all}")
print(f"战略分析必需: {total_essential} ({total_essential/total_all*100:.1f}%)")
print(f"竞争情报重要: {total_competitive} ({total_competitive/total_all*100:.1f}%)")
print(f"建议忽略: {total_all - total_essential - total_competitive} ({(total_all - total_essential - total_competitive)/total_all*100:.1f}%)")
