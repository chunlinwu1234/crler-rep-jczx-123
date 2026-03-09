"""
数据库架构定义
支持多市场（A股、港股、美股、印度、瑞士、日本）的财务数据存储
"""

# 数据库表结构定义
DATABASE_SCHEMA = {
    # 1. 公司信息表（支持多市场）
    "companies": """
        CREATE TABLE IF NOT EXISTS companies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ts_code VARCHAR(20) COMMENT 'tushare代码',
            symbol VARCHAR(20) NOT NULL COMMENT '股票代码',
            name VARCHAR(100) COMMENT '中文名称',
            name_en VARCHAR(100) COMMENT '英文名称',
            market VARCHAR(20) NOT NULL COMMENT '市场类型(a_share/hk_stock/us_stock/india/swiss/japan)',
            exchange VARCHAR(20) COMMENT '交易所代码',
            industry VARCHAR(50) COMMENT '行业分类',
            industry_en VARCHAR(50) COMMENT '行业分类(英文)',
            area VARCHAR(50) COMMENT '地区',
            list_date DATE COMMENT '上市日期',
            currency VARCHAR(10) COMMENT '报告货币(CNY/HKD/USD/INR/CHF/JPY)',
            is_active BOOLEAN DEFAULT TRUE COMMENT '是否活跃',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_market_symbol (market, symbol),
            INDEX idx_industry (industry),
            INDEX idx_market (market)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公司信息表'
    """,
    
    # 2. 财务报表核心表（标准化字段，支持多市场）
    "financial_reports": """
        CREATE TABLE IF NOT EXISTS financial_reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_id INT NOT NULL COMMENT '公司ID',
            
            -- 基础信息
            report_date DATE NOT NULL COMMENT '报告期',
            report_type VARCHAR(20) COMMENT '报告类型(年报/半年报/季报)',
            report_type_en VARCHAR(50) COMMENT '报告类型(英文)',
            ann_date DATE COMMENT '公告日期',
            fiscal_year INT COMMENT '会计年度',
            fiscal_period INT COMMENT '会计期间(1-4季度)',
            
            -- 资产负债表核心
            total_assets DECIMAL(20,2) COMMENT '总资产',
            total_assets_en VARCHAR(100) COMMENT '总资产(英文科目名)',
            total_liab DECIMAL(20,2) COMMENT '总负债',
            total_liab_en VARCHAR(100) COMMENT '总负债(英文科目名)',
            total_equity DECIMAL(20,2) COMMENT '股东权益',
            total_equity_en VARCHAR(100) COMMENT '股东权益(英文科目名)',
            total_cur_assets DECIMAL(20,2) COMMENT '流动资产',
            total_nca DECIMAL(20,2) COMMENT '非流动资产',
            money_cap DECIMAL(20,2) COMMENT '货币资金',
            accounts_receiv DECIMAL(20,2) COMMENT '应收账款',
            inventories DECIMAL(20,2) COMMENT '存货',
            fix_assets DECIMAL(20,2) COMMENT '固定资产',
            cip DECIMAL(20,2) COMMENT '在建工程',
            intan_assets DECIMAL(20,2) COMMENT '无形资产',
            r_and_d DECIMAL(20,2) COMMENT '研发支出',
            goodwill DECIMAL(20,2) COMMENT '商誉',
            total_cur_liab DECIMAL(20,2) COMMENT '流动负债',
            total_ncl DECIMAL(20,2) COMMENT '非流动负债',
            
            -- 利润表核心
            total_revenue DECIMAL(20,2) COMMENT '营业总收入',
            total_revenue_en VARCHAR(100) COMMENT '营业总收入(英文科目名)',
            revenue DECIMAL(20,2) COMMENT '营业收入',
            total_cogs DECIMAL(20,2) COMMENT '营业总成本',
            oper_cost DECIMAL(20,2) COMMENT '营业成本',
            operate_profit DECIMAL(20,2) COMMENT '营业利润',
            operate_profit_en VARCHAR(100) COMMENT '营业利润(英文科目名)',
            n_income DECIMAL(20,2) COMMENT '净利润',
            n_income_en VARCHAR(100) COMMENT '净利润(英文科目名)',
            n_income_attr_p DECIMAL(20,2) COMMENT '归母净利润',
            n_income_attr_p_en VARCHAR(100) COMMENT '归母净利润(英文科目名)',
            sell_exp DECIMAL(20,2) COMMENT '销售费用',
            admin_exp DECIMAL(20,2) COMMENT '管理费用',
            fin_exp DECIMAL(20,2) COMMENT '财务费用',
            rd_exp DECIMAL(20,2) COMMENT '研发费用',
            
            -- 现金流量表核心
            n_cashflow_act DECIMAL(20,2) COMMENT '经营活动现金流净额',
            n_cashflow_act_en VARCHAR(100) COMMENT '经营活动现金流净额(英文科目名)',
            n_cashflow_inv_act DECIMAL(20,2) COMMENT '投资活动现金流净额',
            n_cashflow_inv_act_en VARCHAR(100) COMMENT '投资活动现金流净额(英文科目名)',
            n_cash_flows_fnc_act DECIMAL(20,2) COMMENT '筹资活动现金流净额',
            n_cash_flows_fnc_act_en VARCHAR(100) COMMENT '筹资活动现金流净额(英文科目名)',
            
            -- 财务指标核心
            eps DECIMAL(10,4) COMMENT '基本每股收益',
            roe DECIMAL(8,4) COMMENT '净资产收益率ROE(%)',
            roa DECIMAL(8,4) COMMENT '总资产报酬率ROA(%)',
            grossprofit_margin DECIMAL(8,4) COMMENT '销售毛利率(%)',
            netprofit_margin DECIMAL(8,4) COMMENT '销售净利率(%)',
            debt_to_assets DECIMAL(8,4) COMMENT '资产负债率(%)',
            current_ratio DECIMAL(8,4) COMMENT '流动比率',
            
            -- 扩展字段（JSON存储其他指标）
            extended_data JSON COMMENT '扩展指标数据(中英文对照)',
            
            -- 元数据
            source VARCHAR(20) COMMENT '数据来源(mysql_import/excel_import/ai_extract)',
            data_quality_score DECIMAL(3,2) COMMENT '数据质量评分(0-1)',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            
            UNIQUE KEY uk_company_report (company_id, report_date, report_type),
            INDEX idx_report_date (report_date),
            INDEX idx_fiscal_year (fiscal_year)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务报表核心表'
    """,
    
    # 3. 市场扩展字段配置表
    "market_field_mapping": """
        CREATE TABLE IF NOT EXISTS market_field_mapping (
            id INT AUTO_INCREMENT PRIMARY KEY,
            market VARCHAR(20) NOT NULL COMMENT '市场类型',
            local_field_name VARCHAR(100) NOT NULL COMMENT '本地字段名',
            local_field_name_en VARCHAR(100) COMMENT '本地字段英文名',
            standard_field_name VARCHAR(100) COMMENT '标准字段名',
            field_category VARCHAR(50) COMMENT '字段类别(资产负债表/利润表/现金流量表)',
            field_type VARCHAR(20) COMMENT '字段类型(amount/ratio/percentage/count)',
            description TEXT COMMENT '字段说明',
            description_en TEXT COMMENT '字段说明(英文)',
            is_key_metric BOOLEAN DEFAULT FALSE COMMENT '是否关键指标',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_market_field (market, local_field_name),
            INDEX idx_standard_field (standard_field_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='市场字段映射配置表'
    """,
    
    # 4. 数据源配置表
    "data_sources": """
        CREATE TABLE IF NOT EXISTS data_sources (
            id INT AUTO_INCREMENT PRIMARY KEY,
            source_name VARCHAR(50) NOT NULL COMMENT '数据源名称',
            source_type VARCHAR(20) NOT NULL COMMENT '类型(mysql/excel/api)',
            
            -- MySQL连接配置
            db_host VARCHAR(100) COMMENT '数据库主机',
            db_port INT DEFAULT 3306 COMMENT '数据库端口',
            db_name VARCHAR(100) COMMENT '数据库名',
            db_username VARCHAR(100) COMMENT '用户名',
            db_password VARCHAR(255) COMMENT '密码(加密存储)',
            
            -- Excel配置
            excel_path VARCHAR(500) COMMENT 'Excel文件路径',
            excel_sheet_mapping JSON COMMENT 'Excel工作表映射配置',
            
            -- 通用配置
            market VARCHAR(20) COMMENT '适用市场',
            table_mapping JSON COMMENT '表映射配置',
            field_mapping JSON COMMENT '字段映射配置',
            sync_schedule VARCHAR(50) COMMENT '同步频率(weekly/monthly/manual)',
            is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
            last_sync_at TIMESTAMP NULL COMMENT '上次同步时间',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_source_type (source_type),
            INDEX idx_market (market)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据源配置表'
    """,
    
    # 5. 数据导入日志表
    "import_logs": """
        CREATE TABLE IF NOT EXISTS import_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_source_id (source_id),
            INDEX idx_status (status),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据导入日志表'
    """,
    
    # 6. AI提取文档记录表
    "ai_extracted_documents": """
        CREATE TABLE IF NOT EXISTS ai_extracted_documents (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_id INT COMMENT '公司ID',
            file_name VARCHAR(255) COMMENT '文件名',
            file_path VARCHAR(500) COMMENT '文件路径',
            file_type VARCHAR(20) COMMENT '文件类型(pdf/word/excel)',
            doc_language VARCHAR(10) COMMENT '文档语言(zh/en/ja等)',
            doc_language_confidence DECIMAL(3,2) COMMENT '语言识别置信度',
            report_date DATE COMMENT '报告期',
            report_type VARCHAR(20) COMMENT '报告类型',
            
            -- 提取状态
            extraction_status VARCHAR(20) COMMENT '提取状态(pending/processing/completed/failed)',
            extracted_at TIMESTAMP NULL COMMENT '提取完成时间',
            
            -- 提取结果
            extracted_data JSON COMMENT '提取的数据(中英文对照)',
            raw_text TEXT COMMENT '原始文本内容',
            
            -- 校验状态
            is_verified BOOLEAN DEFAULT FALSE COMMENT '是否人工校验',
            verified_by VARCHAR(50) COMMENT '校验人',
            verified_at TIMESTAMP NULL COMMENT '校验时间',
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_company_id (company_id),
            INDEX idx_extraction_status (extraction_status),
            INDEX idx_report_date (report_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI提取文档记录表'
    """,
}


# 关键指标配置（更新后的指标集）
KEY_METRICS_CONFIG = {
    "每股指标": {
        "fields": ["eps", "dt_eps", "total_revenue_ps", "revenue_ps", "capital_rese_ps"],
        "description": "每股指标",
        "description_en": "Per Share Indicators"
    },
    "盈利能力": {
        "fields": ["profit_dedt", "grossprofit_margin", "netprofit_margin"],
        "description": "盈利能力",
        "description_en": "Profitability",
        "removed_fields": ["profit_to_op"]  # 已移除
    },
    "回报率": {
        "fields": ["roe", "roa"],
        "description": "回报率",
        "description_en": "Return Ratios",
        "removed_fields": ["roe_waa", "roe_dt"]  # 已移除
    },
    "偿债能力": {
        "fields": ["debt_to_assets", "debt_to_eqt", "current_ratio", "quick_ratio"],
        "description": "偿债能力",
        "description_en": "Solvency"
    },
    "营运能力": {
        "fields": ["turn_days", "inv_turn", "ar_turn", "ca_turn", "fa_turn"],
        "description": "营运能力",
        "description_en": "Operational Capability"
    },
    "现金流指标": {
        "fields": ["ocfps", "cfps", "free_cash_flow"],
        "description": "现金流指标",
        "description_en": "Cash Flow Indicators"
    },
    "成长能力": {
        "fields": ["q_sales_yoy", "q_op_yoy", "q_profit_yoy"],
        "description": "成长能力",
        "description_en": "Growth Capability"
    }
}


def get_all_table_schemas() -> dict:
    """获取所有表结构定义"""
    return DATABASE_SCHEMA


def get_table_schema(table_name: str) -> str:
    """获取指定表的创建SQL"""
    return DATABASE_SCHEMA.get(table_name, "")


def get_key_metrics() -> dict:
    """获取关键指标配置"""
    return KEY_METRICS_CONFIG
