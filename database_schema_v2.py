"""
CIMS 数据库架构 V2.0
支持多市场（A股、港股、美股、印度、瑞士、日本）
支持MySQL和Excel数据导入
支持中英文对照
"""

import pymysql
from typing import Dict, List, Optional
from datetime import datetime


class DatabaseSchemaV2:
    """数据库架构管理器 V2"""
    
    # 市场类型定义
    MARKETS = {
        'CN': {'name': 'A股', 'name_en': 'China A-Share', 'currency': 'CNY', 'priority': 1},
        'HK': {'name': '港股', 'name_en': 'Hong Kong', 'currency': 'HKD', 'priority': 2},
        'US': {'name': '美股', 'name_en': 'US Stocks', 'currency': 'USD', 'priority': 3},
        'IN': {'name': '印度', 'name_en': 'India', 'currency': 'INR', 'priority': 4},
        'CH': {'name': '瑞士', 'name_en': 'Switzerland', 'currency': 'CHF', 'priority': 5},
        'JP': {'name': '日本', 'name_en': 'Japan', 'currency': 'JPY', 'priority': 6},
    }
    
    # 战略分析关键指标集（调整后：90个字段）
    CORE_METRICS = {
        # 基础信息（6个）
        'base_info': [
            {'field': 'ts_code', 'name_cn': 'TS代码', 'name_en': 'TS Code', 'type': 'VARCHAR(20)', 'required': True},
            {'field': 'symbol', 'name_cn': '股票代码', 'name_en': 'Stock Symbol', 'type': 'VARCHAR(20)', 'required': True},
            {'field': 'ann_date', 'name_cn': '公告日期', 'name_en': 'Announcement Date', 'type': 'DATE', 'required': True},
            {'field': 'f_ann_date', 'name_cn': '实际公告日期', 'name_en': 'Actual Announcement Date', 'type': 'DATE', 'required': False},
            {'field': 'end_date', 'name_cn': '报告期', 'name_en': 'Report Period', 'type': 'DATE', 'required': True},
            {'field': 'report_type', 'name_cn': '报告类型', 'name_en': 'Report Type', 'type': 'VARCHAR(20)', 'required': True},
        ],
        
        # 资产负债表核心（21个）
        'balance_sheet': [
            {'field': 'total_assets', 'name_cn': '总资产', 'name_en': 'Total Assets', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'total_liab', 'name_cn': '总负债', 'name_en': 'Total Liabilities', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'total_hldr_eqy_exc_min_int', 'name_cn': '归母权益', 'name_en': "Parent Company's Equity", 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'total_cur_assets', 'name_cn': '流动资产', 'name_en': 'Current Assets', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'total_nca', 'name_cn': '非流动资产', 'name_en': 'Non-Current Assets', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'total_cur_liab', 'name_cn': '流动负债', 'name_en': 'Current Liabilities', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'total_ncl', 'name_cn': '非流动负债', 'name_en': 'Non-Current Liabilities', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'money_cap', 'name_cn': '货币资金', 'name_en': 'Cash and Cash Equivalents', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'trad_asset', 'name_cn': '交易性金融资产', 'name_en': 'Trading Financial Assets', 'type': 'DECIMAL(20,2)', 'required': False},
            {'field': 'notes_receiv', 'name_cn': '应收票据', 'name_en': 'Notes Receivable', 'type': 'DECIMAL(20,2)', 'required': False},
            {'field': 'accounts_receiv', 'name_cn': '应收账款', 'name_en': 'Accounts Receivable', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'inventories', 'name_cn': '存货', 'name_en': 'Inventories', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'fix_assets', 'name_cn': '固定资产', 'name_en': 'Fixed Assets', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'cip', 'name_cn': '在建工程', 'name_en': 'Construction in Progress', 'type': 'DECIMAL(20,2)', 'required': False},
            {'field': 'intan_assets', 'name_cn': '无形资产', 'name_en': 'Intangible Assets', 'type': 'DECIMAL(20,2)', 'required': False},
            {'field': 'r_and_d', 'name_cn': '研发支出', 'name_en': 'R&D Expenditure', 'type': 'DECIMAL(20,2)', 'required': False},
            {'field': 'goodwill', 'name_cn': '商誉', 'name_en': 'Goodwill', 'type': 'DECIMAL(20,2)', 'required': False},
            {'field': 'notes_payable', 'name_cn': '应付票据', 'name_en': 'Notes Payable', 'type': 'DECIMAL(20,2)', 'required': False},
            {'field': 'acct_payable', 'name_cn': '应付账款', 'name_en': 'Accounts Payable', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'adv_receipts', 'name_cn': '预收款项', 'name_en': 'Advances from Customers', 'type': 'DECIMAL(20,2)', 'required': False},
        ],
        
        # 利润表核心（14个）
        'income_statement': [
            {'field': 'total_revenue', 'name_cn': '营业总收入', 'name_en': 'Total Revenue', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'revenue', 'name_cn': '营业收入', 'name_en': 'Operating Revenue', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'total_cogs', 'name_cn': '营业总成本', 'name_en': 'Total Operating Costs', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'oper_cost', 'name_cn': '营业成本', 'name_en': 'Operating Costs', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'operate_profit', 'name_cn': '营业利润', 'name_en': 'Operating Profit', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'income_tax', 'name_cn': '所得税', 'name_en': 'Income Tax', 'type': 'DECIMAL(20,2)', 'required': False},
            {'field': 'n_income', 'name_cn': '净利润', 'name_en': 'Net Income', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'n_income_attr_p', 'name_cn': '归母净利润', 'name_en': "Parent Company's Net Income", 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'sell_exp', 'name_cn': '销售费用', 'name_en': 'Selling Expenses', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'admin_exp', 'name_cn': '管理费用', 'name_en': 'Administrative Expenses', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'fin_exp', 'name_cn': '财务费用', 'name_en': 'Financial Expenses', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'rd_exp', 'name_cn': '研发费用', 'name_en': 'R&D Expenses', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'int_income', 'name_cn': '利息收入', 'name_en': 'Interest Income', 'type': 'DECIMAL(20,2)', 'required': False},
            {'field': 'comm_income', 'name_cn': '手续费收入', 'name_en': 'Commission Income', 'type': 'DECIMAL(20,2)', 'required': False},
        ],
        
        # 现金流量表核心（4个）
        'cash_flow': [
            {'field': 'n_cashflow_act', 'name_cn': '经营现金流净额', 'name_en': 'Net Cash Flow from Operating Activities', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'n_cashflow_inv_act', 'name_cn': '投资现金流净额', 'name_en': 'Net Cash Flow from Investing Activities', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'n_cash_flows_fnc_act', 'name_cn': '筹资现金流净额', 'name_en': 'Net Cash Flow from Financing Activities', 'type': 'DECIMAL(20,2)', 'required': True},
            {'field': 'im_net_cashflow_oper_act', 'name_cn': '间接法经营现金流', 'name_en': 'Indirect Method Operating Cash Flow', 'type': 'DECIMAL(20,2)', 'required': False},
        ],
        
        # 财务指标核心（21个，已调整）
        'financial_indicators': [
            # 每股指标（5个）
            {'field': 'eps', 'name_cn': '基本每股收益', 'name_en': 'Basic EPS', 'type': 'DECIMAL(10,4)', 'required': True},
            {'field': 'dt_eps', 'name_cn': '稀释每股收益', 'name_en': 'Diluted EPS', 'type': 'DECIMAL(10,4)', 'required': False},
            {'field': 'total_revenue_ps', 'name_cn': '每股营业总收入', 'name_en': 'Total Revenue Per Share', 'type': 'DECIMAL(10,4)', 'required': False},
            {'field': 'revenue_ps', 'name_cn': '每股营业收入', 'name_en': 'Revenue Per Share', 'type': 'DECIMAL(10,4)', 'required': False},
            {'field': 'ocfps', 'name_cn': '每股经营现金流', 'name_en': 'Operating Cash Flow Per Share', 'type': 'DECIMAL(10,4)', 'required': True},
            
            # 盈利能力（2个，已删除profit_to_op）
            {'field': 'grossprofit_margin', 'name_cn': '销售毛利率', 'name_en': 'Gross Profit Margin', 'type': 'DECIMAL(8,4)', 'required': True},
            {'field': 'netprofit_margin', 'name_cn': '销售净利率', 'name_en': 'Net Profit Margin', 'type': 'DECIMAL(8,4)', 'required': True},
            
            # 回报率（2个，已删除roe_waa和roe_dt）
            {'field': 'roe', 'name_cn': '净资产收益率', 'name_en': 'Return on Equity (ROE)', 'type': 'DECIMAL(8,4)', 'required': True},
            {'field': 'roa', 'name_cn': '总资产报酬率', 'name_en': 'Return on Assets (ROA)', 'type': 'DECIMAL(8,4)', 'required': True},
            
            # 偿债能力（4个）
            {'field': 'debt_to_assets', 'name_cn': '资产负债率', 'name_en': 'Debt to Assets Ratio', 'type': 'DECIMAL(8,4)', 'required': True},
            {'field': 'debt_to_eqt', 'name_cn': '产权比率', 'name_en': 'Debt to Equity Ratio', 'type': 'DECIMAL(8,4)', 'required': False},
            {'field': 'current_ratio', 'name_cn': '流动比率', 'name_en': 'Current Ratio', 'type': 'DECIMAL(8,4)', 'required': True},
            {'field': 'quick_ratio', 'name_cn': '速动比率', 'name_en': 'Quick Ratio', 'type': 'DECIMAL(8,4)', 'required': True},
            
            # 营运能力（5个）
            {'field': 'turn_days', 'name_cn': '营业周期', 'name_en': 'Operating Cycle', 'type': 'DECIMAL(8,2)', 'required': False},
            {'field': 'inv_turn', 'name_cn': '存货周转率', 'name_en': 'Inventory Turnover', 'type': 'DECIMAL(8,4)', 'required': True},
            {'field': 'ar_turn', 'name_cn': '应收账款周转率', 'name_en': 'Accounts Receivable Turnover', 'type': 'DECIMAL(8,4)', 'required': True},
            {'field': 'ca_turn', 'name_cn': '流动资产周转率', 'name_en': 'Current Assets Turnover', 'type': 'DECIMAL(8,4)', 'required': False},
            {'field': 'fa_turn', 'name_cn': '固定资产周转率', 'name_en': 'Fixed Assets Turnover', 'type': 'DECIMAL(8,4)', 'required': False},
            
            # 成长能力（3个）
            {'field': 'q_sales_yoy', 'name_cn': '营收同比增长', 'name_en': 'Revenue YoY Growth', 'type': 'DECIMAL(8,4)', 'required': True},
            {'field': 'q_op_yoy', 'name_cn': '营业利润同比增长', 'name_en': 'Operating Profit YoY Growth', 'type': 'DECIMAL(8,4)', 'required': True},
            {'field': 'q_profit_yoy', 'name_cn': '净利润同比增长', 'name_en': 'Net Profit YoY Growth', 'type': 'DECIMAL(8,4)', 'required': True},
        ],
    }
    
    @classmethod
    def get_all_core_fields(cls) -> List[Dict]:
        """获取所有核心字段定义"""
        all_fields = []
        for category, fields in cls.CORE_METRICS.items():
            for field in fields:
                field['category'] = category
                all_fields.append(field)
        return all_fields
    
    @classmethod
    def get_field_by_name(cls, field_name: str) -> Optional[Dict]:
        """根据字段名获取字段定义"""
        for category, fields in cls.CORE_METRICS.items():
            for field in fields:
                if field['field'] == field_name:
                    field['category'] = category
                    return field
        return None
    
    @classmethod
    def generate_create_table_sql(cls) -> str:
        """生成建表SQL"""
        sql_parts = []
        
        # 1. 公司信息表
        sql_parts.append("""
-- 1. 公司信息表（支持多市场）
CREATE TABLE IF NOT EXISTS companies (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    ts_code VARCHAR(20) NOT NULL COMMENT 'TS代码',
    symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
    name VARCHAR(100) COMMENT '中文名称',
    name_en VARCHAR(100) COMMENT '英文名称',
    market VARCHAR(10) NOT NULL COMMENT '市场代码(CN/HK/US/IN/CH/JP)',
    exchange VARCHAR(20) COMMENT '交易所',
    industry VARCHAR(50) COMMENT '行业',
    industry_en VARCHAR(50) COMMENT '行业英文',
    area VARCHAR(50) COMMENT '地区',
    list_date DATE COMMENT '上市日期',
    currency VARCHAR(10) COMMENT '货币',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否活跃',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_market_symbol (market, symbol),
    INDEX idx_industry (industry),
    INDEX idx_market (market)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公司信息表';
""")
        
        # 2. 财务报表核心表
        fields_sql = []
        for field in cls.get_all_core_fields():
            nullable = 'NOT NULL' if field.get('required') else 'NULL'
            # 转义单引号
            name_cn = field['name_cn'].replace("'", "\\'")
            name_en = field['name_en'].replace("'", "\\'")
            fields_sql.append(f"    {field['field']} {field['type']} {nullable} COMMENT '{name_cn}({name_en})'")
        
        sql_parts.append(f"""
-- 2. 财务报表核心表
CREATE TABLE IF NOT EXISTS financial_reports (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id INT NOT NULL COMMENT '公司ID',
{','.join(fields_sql)},
    extended_data JSON NULL COMMENT '扩展指标数据(JSON格式)',
    source VARCHAR(20) DEFAULT 'import' COMMENT '数据来源(import/excel/ai_extract)',
    data_quality_score DECIMAL(3,2) DEFAULT 1.00 COMMENT '数据质量评分(0-1)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    UNIQUE KEY uk_company_report (company_id, end_date, report_type),
    INDEX idx_report_date (end_date),
    INDEX idx_report_type (report_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务报表核心表';
""")
        
        # 3. 市场字段映射表
        sql_parts.append("""
-- 3. 市场字段映射表
CREATE TABLE IF NOT EXISTS market_field_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    market VARCHAR(10) NOT NULL COMMENT '市场代码',
    local_field_name VARCHAR(100) NOT NULL COMMENT '本地字段名',
    local_field_name_en VARCHAR(100) COMMENT '本地字段英文名',
    standard_field_name VARCHAR(100) NOT NULL COMMENT '标准字段名',
    field_category VARCHAR(50) COMMENT '字段类别',
    data_type VARCHAR(20) COMMENT '数据类型',
    description TEXT COMMENT '字段说明',
    description_en TEXT COMMENT '字段英文说明',
    is_required BOOLEAN DEFAULT FALSE COMMENT '是否必填',
    mapping_rule TEXT COMMENT '映射规则',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    UNIQUE KEY uk_market_field (market, local_field_name),
    INDEX idx_standard_field (standard_field_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='市场字段映射表';
""")
        
        # 4. 数据源配置表
        sql_parts.append("""
-- 4. 数据源配置表
CREATE TABLE IF NOT EXISTS data_sources (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    source_name VARCHAR(50) NOT NULL COMMENT '数据源名称',
    source_type VARCHAR(20) NOT NULL COMMENT '类型(mysql/excel/api)',
    host VARCHAR(100) COMMENT '主机(MySQL)',
    port INT COMMENT '端口(MySQL)',
    database_name VARCHAR(100) COMMENT '数据库名(MySQL)',
    username VARCHAR(100) COMMENT '用户名(MySQL)',
    password VARCHAR(100) COMMENT '密码(MySQL,加密存储)',
    file_path VARCHAR(500) COMMENT '文件路径(Excel)',
    table_mapping JSON COMMENT '表映射配置',
    field_mapping JSON COMMENT '字段映射配置',
    sync_schedule VARCHAR(20) COMMENT '同步频率(weekly/monthly/manual)',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    last_sync_at TIMESTAMP NULL COMMENT '上次同步时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_source_type (source_type),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据源配置表';
""")
        
        # 5. 数据导入日志表
        sql_parts.append("""
-- 5. 数据导入日志表
CREATE TABLE IF NOT EXISTS import_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    source_id INT NOT NULL COMMENT '数据源ID',
    import_type VARCHAR(20) COMMENT '导入类型(full/incremental)',
    start_time TIMESTAMP COMMENT '开始时间',
    end_time TIMESTAMP NULL COMMENT '结束时间',
    records_count INT DEFAULT 0 COMMENT '总记录数',
    success_count INT DEFAULT 0 COMMENT '成功数',
    failed_count INT DEFAULT 0 COMMENT '失败数',
    status VARCHAR(20) COMMENT '状态(running/success/failed)',
    error_message TEXT COMMENT '错误信息',
    details JSON COMMENT '详细日志',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (source_id) REFERENCES data_sources(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据导入日志表';
""")
        
        # 6. AI提取文档记录表
        sql_parts.append("""
-- 6. AI提取文档记录表
CREATE TABLE IF NOT EXISTS ai_extraction_logs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    company_id INT COMMENT '公司ID',
    document_name VARCHAR(255) COMMENT '文档名称',
    document_path VARCHAR(500) COMMENT '文档路径',
    document_type VARCHAR(50) COMMENT '文档类型(pdf/word/excel)',
    language VARCHAR(10) COMMENT '文档语言(zh/en)',
    extraction_status VARCHAR(20) COMMENT '提取状态',
    extracted_data JSON COMMENT '提取的数据',
    confidence_score DECIMAL(3,2) COMMENT '置信度',
    processing_time INT COMMENT '处理时间(秒)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
    INDEX idx_extraction_status (extraction_status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI提取文档记录表';
""")
        
        return '\n'.join(sql_parts)


# 生成A股字段映射配置（tushare -> 标准字段）
def generate_a_share_mapping() -> List[Dict]:
    """生成A股字段映射配置"""
    mappings = []
    
    # 基础信息映射
    base_mappings = [
        {'local': 'ts_code', 'standard': 'ts_code'},
        {'local': 'ann_date', 'standard': 'ann_date'},
        {'local': 'f_ann_date', 'standard': 'f_ann_date'},
        {'local': 'end_date', 'standard': 'end_date'},
    ]
    
    # 资产负债表映射
    balance_mappings = [
        {'local': 'total_assets', 'standard': 'total_assets'},
        {'local': 'total_liab', 'standard': 'total_liab'},
        {'local': 'total_hldr_eqy_exc_min_int', 'standard': 'total_hldr_eqy_exc_min_int'},
        {'local': 'total_cur_assets', 'standard': 'total_cur_assets'},
        {'local': 'total_nca', 'standard': 'total_nca'},
        {'local': 'total_cur_liab', 'standard': 'total_cur_liab'},
        {'local': 'total_ncl', 'standard': 'total_ncl'},
        {'local': 'money_cap', 'standard': 'money_cap'},
        {'local': 'trad_asset', 'standard': 'trad_asset'},
        {'local': 'notes_receiv', 'standard': 'notes_receiv'},
        {'local': 'accounts_receiv', 'standard': 'accounts_receiv'},
        {'local': 'inventories', 'standard': 'inventories'},
        {'local': 'fix_assets', 'standard': 'fix_assets'},
        {'local': 'cip', 'standard': 'cip'},
        {'local': 'intan_assets', 'standard': 'intan_assets'},
        {'local': 'r_and_d', 'standard': 'r_and_d'},
        {'local': 'goodwill', 'standard': 'goodwill'},
        {'local': 'notes_payable', 'standard': 'notes_payable'},
        {'local': 'acct_payable', 'standard': 'acct_payable'},
        {'local': 'adv_receipts', 'standard': 'adv_receipts'},
    ]
    
    # 利润表映射
    income_mappings = [
        {'local': 'total_revenue', 'standard': 'total_revenue'},
        {'local': 'revenue', 'standard': 'revenue'},
        {'local': 'total_cogs', 'standard': 'total_cogs'},
        {'local': 'oper_cost', 'standard': 'oper_cost'},
        {'local': 'operate_profit', 'standard': 'operate_profit'},
        {'local': 'income_tax', 'standard': 'income_tax'},
        {'local': 'n_income', 'standard': 'n_income'},
        {'local': 'n_income_attr_p', 'standard': 'n_income_attr_p'},
        {'local': 'sell_exp', 'standard': 'sell_exp'},
        {'local': 'admin_exp', 'standard': 'admin_exp'},
        {'local': 'fin_exp', 'standard': 'fin_exp'},
        {'local': 'rd_exp', 'standard': 'rd_exp'},
        {'local': 'int_income', 'standard': 'int_income'},
        {'local': 'comm_income', 'standard': 'comm_income'},
    ]
    
    # 现金流量表映射
    cashflow_mappings = [
        {'local': 'n_cashflow_act', 'standard': 'n_cashflow_act'},
        {'local': 'n_cashflow_inv_act', 'standard': 'n_cashflow_inv_act'},
        {'local': 'n_cash_flows_fnc_act', 'standard': 'n_cash_flows_fnc_act'},
    ]
    
    # 财务指标映射
    indicator_mappings = [
        {'local': 'eps', 'standard': 'eps'},
        {'local': 'dt_eps', 'standard': 'dt_eps'},
        {'local': 'total_revenue_ps', 'standard': 'total_revenue_ps'},
        {'local': 'revenue_ps', 'standard': 'revenue_ps'},
        {'local': 'ocfps', 'standard': 'ocfps'},
        {'local': 'grossprofit_margin', 'standard': 'grossprofit_margin'},
        {'local': 'netprofit_margin', 'standard': 'netprofit_margin'},
        {'local': 'roe', 'standard': 'roe'},
        {'local': 'roa', 'standard': 'roa'},
        {'local': 'debt_to_assets', 'standard': 'debt_to_assets'},
        {'local': 'debt_to_eqt', 'standard': 'debt_to_eqt'},
        {'local': 'current_ratio', 'standard': 'current_ratio'},
        {'local': 'quick_ratio', 'standard': 'quick_ratio'},
        {'local': 'turn_days', 'standard': 'turn_days'},
        {'local': 'inv_turn', 'standard': 'inv_turn'},
        {'local': 'ar_turn', 'standard': 'ar_turn'},
        {'local': 'ca_turn', 'standard': 'ca_turn'},
        {'local': 'fa_turn', 'standard': 'fa_turn'},
        {'local': 'q_sales_yoy', 'standard': 'q_sales_yoy'},
        {'local': 'q_op_yoy', 'standard': 'q_op_yoy'},
        {'local': 'q_profit_yoy', 'standard': 'q_profit_yoy'},
    ]
    
    all_mappings = (base_mappings + balance_mappings + income_mappings + 
                   cashflow_mappings + indicator_mappings)
    
    for mapping in all_mappings:
        field_def = DatabaseSchemaV2.get_field_by_name(mapping['standard'])
        if field_def:
            mappings.append({
                'market': 'CN',
                'local_field_name': mapping['local'],
                'local_field_name_en': mapping['local'],
                'standard_field_name': mapping['standard'],
                'field_category': field_def.get('category', ''),
                'data_type': field_def.get('type', ''),
                'description': field_def.get('name_cn', ''),
                'description_en': field_def.get('name_en', ''),
                'is_required': field_def.get('required', False),
            })
    
    return mappings


if __name__ == "__main__":
    # 打印建表SQL
    print(DatabaseSchemaV2.generate_create_table_sql())
    
    print("\n\n" + "="*80)
    print("A股字段映射配置")
    print("="*80)
    
    mappings = generate_a_share_mapping()
    print(f"共 {len(mappings)} 个字段映射")
    
    for m in mappings[:5]:
        print(f"\n{m['local_field_name']} -> {m['standard_field_name']}")
        print(f"  中文: {m['description']}")
        print(f"  英文: {m['description_en']}")
