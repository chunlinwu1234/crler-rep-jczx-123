"""
数据导入模块
支持从MySQL数据库和Excel文件导入财务数据
"""

import os
import re
import json
import pandas as pd
import pymysql
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from database_v2 import DatabaseManagerV2, DataRepositoryV2, DBConfig
from market_config import MarketType, get_market_config


@dataclass
class ImportConfig:
    """导入配置"""
    source_type: str  # mysql 或 excel
    market: str  # 市场类型
    
    # MySQL配置
    db_host: str = None
    db_port: int = 3306
    db_name: str = None
    db_username: str = None
    db_password: str = None
    
    # Excel配置
    excel_path: str = None
    excel_sheets: Dict[str, str] = None  # {sheet_name: table_name}
    
    # 字段映射
    field_mapping: Dict[str, str] = None  # {source_field: target_field}


class MySQLImporter:
    """MySQL数据导入器"""
    
    def __init__(self, config: ImportConfig):
        self.config = config
        self.source_conn = None
    
    def test_connection(self) -> Tuple[bool, str]:
        """测试MySQL连接"""
        try:
            conn = pymysql.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                user=self.config.db_username,
                password=self.config.db_password,
                database=self.config.db_name,
                charset='utf8mb4'
            )
            conn.close()
            return True, "连接成功"
        except Exception as e:
            return False, str(e)
    
    def get_source_connection(self):
        """获取源数据库连接"""
        if self.source_conn is None or not self.source_conn.open:
            self.source_conn = pymysql.connect(
                host=self.config.db_host,
                port=self.config.db_port,
                user=self.config.db_username,
                password=self.config.db_password,
                database=self.config.db_name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        return self.source_conn
    
    def get_table_schema(self, table_name: str) -> List[Dict]:
        """获取源表结构"""
        conn = self.get_source_connection()
        with conn.cursor() as cursor:
            cursor.execute(f"DESCRIBE {table_name}")
            return cursor.fetchall()
    
    def get_table_list(self) -> List[str]:
        """获取源数据库表列表"""
        conn = self.get_source_connection()
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            return [list(t.values())[0] for t in tables]
    
    def import_data(self, source_table: str, target_repo: DataRepositoryV2,
                   field_mapping: Dict[str, str], 
                   batch_size: int = 1000,
                   progress_callback=None) -> Dict:
        """
        从MySQL导入数据
        
        Args:
            source_table: 源表名
            target_repo: 目标数据仓库
            field_mapping: 字段映射
            batch_size: 批量大小
            progress_callback: 进度回调函数
            
        Returns:
            导入结果统计
        """
        conn = self.get_source_connection()
        
        # 获取总记录数
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) as total FROM {source_table}")
            total_records = cursor.fetchone()['total']
        
        # 分批导入
        imported_count = 0
        failed_count = 0
        errors = []
        
        offset = 0
        while offset < total_records:
            with conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {source_table} LIMIT %s OFFSET %s", 
                             (batch_size, offset))
                rows = cursor.fetchall()
                
                if not rows:
                    break
                
                for row in rows:
                    try:
                        # 字段映射转换
                        mapped_data = self._map_fields(row, field_mapping)
                        
                        # 获取或创建公司
                        company_id = self._get_or_create_company(
                            target_repo, mapped_data, self.config.market
                        )
                        
                        # 保存财务数据
                        mapped_data['company_id'] = company_id
                        mapped_data['source'] = 'mysql_import'
                        target_repo.save_financial_report(company_id, mapped_data)
                        
                        imported_count += 1
                        
                    except Exception as e:
                        failed_count += 1
                        errors.append({
                            'row': row,
                            'error': str(e)
                        })
                
                offset += batch_size
                
                if progress_callback:
                    progress_callback(imported_count, total_records)
        
        conn.close()
        
        return {
            'total': total_records,
            'imported': imported_count,
            'failed': failed_count,
            'errors': errors[:10]  # 只返回前10个错误
        }
    
    def _map_fields(self, row: Dict, mapping: Dict[str, str]) -> Dict:
        """字段映射转换"""
        result = {}
        for source_field, target_field in mapping.items():
            if source_field in row:
                result[target_field] = row[source_field]
        return result
    
    def _get_or_create_company(self, repo: DataRepositoryV2, 
                               data: Dict, market: str) -> int:
        """获取或创建公司记录"""
        # 从数据中提取公司信息
        symbol = data.get('ts_code', '').split('.')[0] if 'ts_code' in data else data.get('symbol')
        name = data.get('name', '未知公司')
        
        company = repo.get_company(symbol=symbol, market=market)
        if company:
            return company['id']
        
        return repo.create_company(
            symbol=symbol,
            name=name,
            market=market
        )


class ExcelImporter:
    """Excel数据导入器"""
    
    def __init__(self, config: ImportConfig):
        self.config = config
    
    def validate_file(self) -> Tuple[bool, str]:
        """验证Excel文件"""
        if not os.path.exists(self.config.excel_path):
            return False, f"文件不存在: {self.config.excel_path}"
        
        try:
            xl = pd.ExcelFile(self.config.excel_path)
            return True, f"有效文件，包含工作表: {', '.join(xl.sheet_names)}"
        except Exception as e:
            return False, str(e)
    
    def get_sheet_list(self) -> List[str]:
        """获取Excel工作表列表"""
        xl = pd.ExcelFile(self.config.excel_path)
        return xl.sheet_names
    
    def preview_data(self, sheet_name: str, rows: int = 10) -> pd.DataFrame:
        """预览数据"""
        df = pd.read_excel(self.config.excel_path, sheet_name=sheet_name, nrows=rows)
        return df
    
    def import_data(self, sheet_name: str, target_repo: DataRepositoryV2,
                   field_mapping: Dict[str, str],
                   progress_callback=None) -> Dict:
        """
        从Excel导入数据
        
        Args:
            sheet_name: 工作表名
            target_repo: 目标数据仓库
            field_mapping: 字段映射
            progress_callback: 进度回调函数
            
        Returns:
            导入结果统计
        """
        # 读取Excel
        df = pd.read_excel(self.config.excel_path, sheet_name=sheet_name)
        
        total_records = len(df)
        imported_count = 0
        failed_count = 0
        errors = []
        
        for idx, row in df.iterrows():
            try:
                # 转换为字典
                row_dict = row.to_dict()
                
                # 字段映射转换
                mapped_data = self._map_fields(row_dict, field_mapping)
                
                # 处理NaN值
                mapped_data = {k: v if pd.notna(v) else None 
                             for k, v in mapped_data.items()}
                
                # 获取或创建公司
                company_id = self._get_or_create_company(
                    target_repo, mapped_data, self.config.market
                )
                
                # 保存财务数据
                mapped_data['company_id'] = company_id
                mapped_data['source'] = 'excel_import'
                target_repo.save_financial_report(company_id, mapped_data)
                
                imported_count += 1
                
                if progress_callback and idx % 10 == 0:
                    progress_callback(imported_count, total_records)
                    
            except Exception as e:
                failed_count += 1
                errors.append({
                    'row_idx': idx,
                    'row_data': row.to_dict(),
                    'error': str(e)
                })
        
        return {
            'total': total_records,
            'imported': imported_count,
            'failed': failed_count,
            'errors': errors[:10]
        }
    
    def _map_fields(self, row: Dict, mapping: Dict[str, str]) -> Dict:
        """字段映射转换"""
        result = {}
        for source_field, target_field in mapping.items():
            if source_field in row:
                result[target_field] = row[source_field]
        return result
    
    def _get_or_create_company(self, repo: DataRepositoryV2, 
                               data: Dict, market: str) -> int:
        """获取或创建公司记录"""
        symbol = data.get('ts_code', '').split('.')[0] if 'ts_code' in data else data.get('symbol')
        name = data.get('name', '未知公司')
        
        company = repo.get_company(symbol=symbol, market=market)
        if company:
            return company['id']
        
        return repo.create_company(
            symbol=symbol,
            name=name,
            market=market
        )


class DataImporter:
    """数据导入主类"""
    
    def __init__(self, db_manager: DatabaseManagerV2):
        self.db_manager = db_manager
        self.repo = DataRepositoryV2(db_manager)
    
    def create_importer(self, config: ImportConfig):
        """创建导入器"""
        if config.source_type == 'mysql':
            return MySQLImporter(config)
        elif config.source_type == 'excel':
            return ExcelImporter(config)
        else:
            raise ValueError(f"不支持的数据源类型: {config.source_type}")
    
    def test_source_connection(self, config: ImportConfig) -> Tuple[bool, str]:
        """测试数据源连接"""
        if config.source_type == 'mysql':
            importer = MySQLImporter(config)
            return importer.test_connection()
        elif config.source_type == 'excel':
            importer = ExcelImporter(config)
            return importer.validate_file()
        return False, "未知数据源类型"
    
    def auto_map_fields(self, source_fields: List[str], 
                       target_fields: List[str]) -> Dict[str, str]:
        """
        自动匹配字段
        
        Args:
            source_fields: 源字段列表
            target_fields: 目标字段列表
            
        Returns:
            字段映射字典
        """
        mapping = {}
        
        # 精确匹配
        for source in source_fields:
            if source in target_fields:
                mapping[source] = source
        
        # 模糊匹配（tushare字段名）
        tushare_mapping = {
            'ts_code': 'ts_code',
            'ann_date': 'ann_date',
            'end_date': 'report_date',
            'total_assets': 'total_assets',
            'total_liab': 'total_liab',
            'total_hldr_eqy_exc_min_int': 'total_equity',
            'total_revenue': 'total_revenue',
            'revenue': 'revenue',
            'operate_profit': 'operate_profit',
            'n_income': 'n_income',
            'n_income_attr_p': 'n_income_attr_p',
            'eps': 'eps',
            'roe': 'roe',
            'roa': 'roa',
        }
        
        for source in source_fields:
            if source not in mapping and source in tushare_mapping:
                target = tushare_mapping[source]
                if target in target_fields:
                    mapping[source] = target
        
        return mapping


# 预定义的tushare字段映射
TUSHARE_FIELD_MAPPING = {
    # 基础信息
    'ts_code': 'ts_code',
    'ann_date': 'ann_date',
    'f_ann_date': 'f_ann_date',
    'end_date': 'report_date',
    'report_type': 'report_type',
    'comp_type': 'comp_type',
    
    # 资产负债表
    'total_assets': 'total_assets',
    'total_liab': 'total_liab',
    'total_hldr_eqy_exc_min_int': 'total_equity',
    'total_cur_assets': 'total_cur_assets',
    'total_nca': 'total_nca',
    'money_cap': 'money_cap',
    'trad_asset': 'trad_asset',
    'notes_receiv': 'notes_receiv',
    'accounts_receiv': 'accounts_receiv',
    'inventories': 'inventories',
    'goodwill': 'goodwill',
    'intan_assets': 'intan_assets',
    'r_and_d': 'r_and_d',
    'fix_assets': 'fix_assets',
    'cip': 'cip',
    'const_materials': 'const_materials',
    'total_cur_liab': 'total_cur_liab',
    'total_ncl': 'total_ncl',
    'notes_payable': 'notes_payable',
    'acct_payable': 'acct_payable',
    'adv_receipts': 'adv_receipts',
    
    # 利润表
    'total_revenue': 'total_revenue',
    'revenue': 'revenue',
    'total_cogs': 'total_cogs',
    'oper_cost': 'oper_cost',
    'operate_profit': 'operate_profit',
    'income_tax': 'income_tax',
    'n_income': 'n_income',
    'n_income_attr_p': 'n_income_attr_p',
    'sell_exp': 'sell_exp',
    'admin_exp': 'admin_exp',
    'fin_exp': 'fin_exp',
    'rd_exp': 'rd_exp',
    'int_income': 'int_income',
    'comm_income': 'comm_income',
    
    # 现金流量表
    'n_cashflow_act': 'n_cashflow_act',
    'n_cashflow_inv_act': 'n_cashflow_inv_act',
    'n_cash_flows_fnc_act': 'n_cash_flows_fnc_act',
    'im_net_cashflow_oper_act': 'im_net_cashflow_oper_act',
    
    # 财务指标（更新后的关键指标）
    'eps': 'eps',
    'dt_eps': 'dt_eps',
    'total_revenue_ps': 'total_revenue_ps',
    'revenue_ps': 'revenue_ps',
    'capital_rese_ps': 'capital_rese_ps',
    'profit_dedt': 'profit_dedt',
    'grossprofit_margin': 'grossprofit_margin',
    'netprofit_margin': 'netprofit_margin',
    'roe': 'roe',
    'roa': 'roa',
    'debt_to_assets': 'debt_to_assets',
    'debt_to_eqt': 'debt_to_eqt',
    'current_ratio': 'current_ratio',
    'quick_ratio': 'quick_ratio',
    'turn_days': 'turn_days',
    'inv_turn': 'inv_turn',
    'ar_turn': 'ar_turn',
    'ca_turn': 'ca_turn',
    'fa_turn': 'fa_turn',
    'ocfps': 'ocfps',
    'cfps': 'cfps',
    'free_cash_flow': 'free_cash_flow',
    'q_sales_yoy': 'q_sales_yoy',
    'q_op_yoy': 'q_op_yoy',
    'q_profit_yoy': 'q_profit_yoy',
}


if __name__ == "__main__":
    # 测试代码
    print("数据导入模块测试")
    print("-" * 50)
    
    # 测试配置
    config = ImportConfig(
        source_type='mysql',
        market='a_share',
        db_host='localhost',
        db_port=3306,
        db_name='tushare_db',
        db_username='root',
        db_password='root'
    )
    
    importer = MySQLImporter(config)
    success, msg = importer.test_connection()
    print(f"MySQL连接测试: {msg}")
