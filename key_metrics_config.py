"""
战略分析关键指标配置
根据竞争情报分析需求筛选的核心指标
"""

# 战略分析必需指标（已根据需求调整）
STRATEGIC_ESSENTIAL_METRICS = {
    '资产负债表': [
        # 基础信息
        'ts_code', 'end_date', 'ann_date',
        # 规模指标
        'total_assets', 'total_liab', 'total_hldr_eqy_exc_min_int',
        # 资产结构
        'total_cur_assets', 'total_nca',
        'money_cap', 'trad_asset', 'notes_receiv', 'accounts_receiv', 'inventories',
        'goodwill', 'intan_assets', 'r_and_d',
        'fix_assets', 'cip', 'const_materials',
        # 负债结构
        'total_cur_liab', 'total_ncl',
        'notes_payable', 'acct_payable', 'adv_receipts',
    ],
    '利润表': [
        # 基础信息
        'ts_code', 'end_date', 'ann_date',
        # 收入成本
        'total_revenue', 'revenue',
        'total_cogs', 'oper_cost',
        # 利润指标
        'operate_profit', 'income_tax', 'n_income', 'n_income_attr_p',
        # 期间费用
        'sell_exp', 'admin_exp', 'fin_exp', 'rd_exp',
        # 其他收益
        'int_income', 'comm_income', 'other_income',
        # 减值损失
        'impair_loss_assets', 'credit_impair_loss',
    ],
    '现金流量表': [
        # 基础信息
        'ts_code', 'end_date', 'ann_date',
        # 三类现金流
        'n_cashflow_act', 'n_cashflow_inv_act', 'n_cash_flows_fnc_act',
        # 现金余额
        'c_end_bal_cash', 'c_beg_bal_cash',
        # 间接法经营现金流
        'im_net_cashflow_oper_act',
    ],
    '主营业务构成': [
        'ts_code', 'end_date', 'bz_item', 'bz_sales', 'bz_profit',
    ],
    '业绩快报': [
        'ts_code', 'end_date', 'ann_date',
        'revenue', 'operate_profit', 'total_profit', 'n_income', 'n_income_attr_p',
        'basic_eps', 'diluted_eps', 'total_assets', 'total_hldr_eqy_exc_min_int',
    ],
    '财务指标': [
        # 基础信息
        'ts_code', 'end_date', 'ann_date',
        # 每股指标
        'eps', 'dt_eps', 'total_revenue_ps', 'revenue_ps', 'capital_rese_ps',
        # 盈利能力（已去掉 profit_to_op）
        'profit_dedt', 'grossprofit_margin', 'netprofit_margin',
        # 回报率（已去掉 roe_waa, roe_dt）
        'roe', 'roa',
        # 偿债能力
        'debt_to_assets', 'debt_to_eqt', 'current_ratio', 'quick_ratio',
        # 营运能力
        'turn_days', 'inv_turn', 'ar_turn', 'ca_turn', 'fa_turn', 'ta_turn',
        # 现金流指标
        'ocfps', 'cfps', 'free_cash_flow',
        # 成长能力
        'q_sales_yoy', 'q_op_yoy', 'q_profit_yoy',
    ]
}

# 竞争情报重要指标
COMPETITIVE_INTEL_METRICS = {
    '财务指标': [
        # 同比增长率
        'basic_eps_yoy', 'dt_eps_yoy', 'cfps_yoy', 'op_yoy', 'ebt_yoy',
        'netprofit_yoy', 'tr_yoy', 'or_yoy', 'assets_yoy',
        # 季度指标
        'q_gsprofit_margin', 'q_profit_to_gr', 'q_saleexp_to_gr', 'q_adminexp_to_gr',
        # 年化指标
        'roe_yearly',
    ]
}

# 指标中文名称映射（用于展示）
METRIC_NAME_MAPPING = {
    # 资产负债表
    'total_assets': '总资产',
    'total_liab': '总负债',
    'total_hldr_eqy_exc_min_int': '归母权益',
    'total_cur_assets': '流动资产',
    'total_nca': '非流动资产',
    'money_cap': '货币资金',
    'trad_asset': '交易性金融资产',
    'notes_receiv': '应收票据',
    'accounts_receiv': '应收账款',
    'inventories': '存货',
    'goodwill': '商誉',
    'intan_assets': '无形资产',
    'r_and_d': '研发支出',
    'fix_assets': '固定资产',
    'cip': '在建工程',
    'const_materials': '工程物资',
    'total_cur_liab': '流动负债',
    'total_ncl': '非流动负债',
    'notes_payable': '应付票据',
    'acct_payable': '应付账款',
    'adv_receipts': '预收款项',
    
    # 利润表
    'total_revenue': '营业总收入',
    'revenue': '营业收入',
    'total_cogs': '营业总成本',
    'oper_cost': '营业成本',
    'operate_profit': '营业利润',
    'income_tax': '所得税',
    'n_income': '净利润',
    'n_income_attr_p': '归母净利润',
    'sell_exp': '销售费用',
    'admin_exp': '管理费用',
    'fin_exp': '财务费用',
    'rd_exp': '研发费用',
    'int_income': '利息收入',
    'comm_income': '手续费收入',
    'other_income': '其他收益',
    'impair_loss_assets': '资产减值损失',
    'credit_impair_loss': '信用减值损失',
    
    # 现金流量表
    'n_cashflow_act': '经营活动现金流净额',
    'n_cashflow_inv_act': '投资活动现金流净额',
    'n_cash_flows_fnc_act': '筹资活动现金流净额',
    'c_end_bal_cash': '期末现金余额',
    'c_beg_bal_cash': '期初现金余额',
    'im_net_cashflow_oper_act': '间接法经营现金流',
    
    # 主营业务构成
    'bz_item': '主营业务项目',
    'bz_sales': '主营业务收入',
    'bz_profit': '主营业务利润',
    
    # 业绩快报
    'total_profit': '利润总额',
    'basic_eps': '基本每股收益',
    'diluted_eps': '稀释每股收益',
    
    # 财务指标
    'eps': '基本每股收益',
    'dt_eps': '稀释每股收益',
    'total_revenue_ps': '每股营业总收入',
    'revenue_ps': '每股营业收入',
    'capital_rese_ps': '每股资本公积',
    'profit_dedt': '扣非净利润',
    'grossprofit_margin': '销售毛利率',
    'netprofit_margin': '销售净利率',
    'roe': '净资产收益率',
    'roa': '总资产报酬率',
    'debt_to_assets': '资产负债率',
    'debt_to_eqt': '产权比率',
    'current_ratio': '流动比率',
    'quick_ratio': '速动比率',
    'turn_days': '营业周期',
    'inv_turn': '存货周转率',
    'ar_turn': '应收账款周转率',
    'ca_turn': '流动资产周转率',
    'fa_turn': '固定资产周转率',
    'ta_turn': '总资产周转率',
    'ocfps': '每股经营现金流',
    'cfps': '每股现金流',
    'free_cash_flow': '自由现金流',
    'q_sales_yoy': '营收同比增长率(单季)',
    'q_op_yoy': '营业利润同比增长率(单季)',
    'q_profit_yoy': '净利润同比增长率(单季)',
}

# 指标英文名称映射（用于中英文对照）
METRIC_NAME_MAPPING_EN = {
    # Balance Sheet
    'total_assets': 'Total Assets',
    'total_liab': 'Total Liabilities',
    'total_hldr_eqy_exc_min_int': 'Equity Attributable to Parent',
    'total_cur_assets': 'Current Assets',
    'total_nca': 'Non-current Assets',
    'money_cap': 'Cash and Cash Equivalents',
    'trad_asset': 'Financial Assets at Fair Value',
    'notes_receiv': 'Notes Receivable',
    'accounts_receiv': 'Accounts Receivable',
    'inventories': 'Inventories',
    'goodwill': 'Goodwill',
    'intan_assets': 'Intangible Assets',
    'r_and_d': 'R&D Expenditure',
    'fix_assets': 'Fixed Assets',
    'cip': 'Construction in Progress',
    'const_materials': 'Construction Materials',
    'total_cur_liab': 'Current Liabilities',
    'total_ncl': 'Non-current Liabilities',
    'notes_payable': 'Notes Payable',
    'acct_payable': 'Accounts Payable',
    'adv_receipts': 'Advances from Customers',
    
    # Income Statement
    'total_revenue': 'Total Revenue',
    'revenue': 'Operating Revenue',
    'total_cogs': 'Total Cost of Revenue',
    'oper_cost': 'Operating Cost',
    'operate_profit': 'Operating Profit',
    'income_tax': 'Income Tax',
    'n_income': 'Net Income',
    'n_income_attr_p': 'Net Income Attributable to Parent',
    'sell_exp': 'Selling Expenses',
    'admin_exp': 'Administrative Expenses',
    'fin_exp': 'Financial Expenses',
    'rd_exp': 'R&D Expenses',
    'int_income': 'Interest Income',
    'comm_income': 'Commission Income',
    'other_income': 'Other Income',
    'impair_loss_assets': 'Impairment Loss on Assets',
    'credit_impair_loss': 'Credit Impairment Loss',
    
    # Cash Flow Statement
    'n_cashflow_act': 'Net Cash Flow from Operating Activities',
    'n_cashflow_inv_act': 'Net Cash Flow from Investing Activities',
    'n_cash_flows_fnc_act': 'Net Cash Flow from Financing Activities',
    'c_end_bal_cash': 'Cash at End of Period',
    'c_beg_bal_cash': 'Cash at Beginning of Period',
    'im_net_cashflow_oper_act': 'Indirect Method Operating Cash Flow',
    
    # Business Segments
    'bz_item': 'Business Segment',
    'bz_sales': 'Segment Revenue',
    'bz_profit': 'Segment Profit',
    
    # Performance Express
    'total_profit': 'Total Profit',
    'basic_eps': 'Basic EPS',
    'diluted_eps': 'Diluted EPS',
    
    # Financial Ratios
    'eps': 'Basic EPS',
    'dt_eps': 'Diluted EPS',
    'total_revenue_ps': 'Total Revenue per Share',
    'revenue_ps': 'Revenue per Share',
    'capital_rese_ps': 'Capital Reserve per Share',
    'profit_dedt': 'Net Profit Excluding Non-recurring Items',
    'grossprofit_margin': 'Gross Profit Margin',
    'netprofit_margin': 'Net Profit Margin',
    'roe': 'Return on Equity (ROE)',
    'roa': 'Return on Assets (ROA)',
    'debt_to_assets': 'Debt-to-Assets Ratio',
    'debt_to_eqt': 'Debt-to-Equity Ratio',
    'current_ratio': 'Current Ratio',
    'quick_ratio': 'Quick Ratio',
    'turn_days': 'Operating Cycle',
    'inv_turn': 'Inventory Turnover',
    'ar_turn': 'Accounts Receivable Turnover',
    'ca_turn': 'Current Assets Turnover',
    'fa_turn': 'Fixed Assets Turnover',
    'ta_turn': 'Total Assets Turnover',
    'ocfps': 'Operating Cash Flow per Share',
    'cfps': 'Cash Flow per Share',
    'free_cash_flow': 'Free Cash Flow',
    'q_sales_yoy': 'Revenue YoY Growth (Quarterly)',
    'q_op_yoy': 'Operating Profit YoY Growth (Quarterly)',
    'q_profit_yoy': 'Net Profit YoY Growth (Quarterly)',
}


def get_metric_name_cn(metric_code: str) -> str:
    """获取指标中文名称"""
    return METRIC_NAME_MAPPING.get(metric_code, metric_code)


def get_metric_name_en(metric_code: str) -> str:
    """获取指标英文名称"""
    return METRIC_NAME_MAPPING_EN.get(metric_code, metric_code)


def get_all_strategic_metrics() -> dict:
    """获取所有战略分析指标"""
    return STRATEGIC_ESSENTIAL_METRICS


def get_all_competitive_metrics() -> dict:
    """获取所有竞争情报指标"""
    return COMPETITIVE_INTEL_METRICS


if __name__ == "__main__":
    # 统计指标数量
    total_strategic = sum(len(v) for v in STRATEGIC_ESSENTIAL_METRICS.values())
    total_competitive = sum(len(v) for v in COMPETITIVE_INTEL_METRICS.values())
    
    print("=" * 60)
    print("战略分析关键指标配置")
    print("=" * 60)
    print(f"\n战略分析必需指标: {total_strategic} 个")
    print(f"竞争情报重要指标: {total_competitive} 个")
    print(f"总计: {total_strategic + total_competitive} 个")
    
    print("\n【各报表指标分布】")
    for sheet, metrics in STRATEGIC_ESSENTIAL_METRICS.items():
        print(f"  {sheet}: {len(metrics)} 个")
