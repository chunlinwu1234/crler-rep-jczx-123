"""
数据库管理模块 V2
支持多市场财务数据存储和管理
"""

import os
import json
import pymysql
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from contextlib import contextmanager
from dataclasses import dataclass

from database_schema import get_all_table_schemas, get_key_metrics
from market_config import MarketType, get_market_config


@dataclass
class DBConfig:
    """数据库配置类"""
    host: str = "localhost"
    port: int = 3306
    database: str = "cims_db"
    user: str = "root"
    password: str = ""
    charset: str = "utf8mb4"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "charset": self.charset,
            "cursorclass": pymysql.cursors.DictCursor
        }


class DatabaseManagerV2:
    """数据库管理器 V2"""
    
    def __init__(self, config: DBConfig = None):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置
        """
        self.config = config or DBConfig()
        self._connection = None
    
    def _get_connection(self):
        """获取数据库连接"""
        if self._connection is None or not self._connection.open:
            self._connection = pymysql.connect(**self.config.to_dict())
        return self._connection
    
    @contextmanager
    def cursor(self):
        """获取数据库游标的上下文管理器"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def init_database(self):
        """初始化数据库，创建数据库和表结构"""
        # 先连接MySQL服务器（不指定数据库）
        config_dict = self.config.to_dict()
        config_dict.pop('cursorclass', None)
        config_dict['database'] = None
        
        conn = pymysql.connect(**config_dict)
        try:
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"✅ 数据库 {self.config.database} 已创建或已存在")
        finally:
            conn.close()
        
        # 创建表结构
        self._create_tables()
    
    def _create_tables(self):
        """创建数据表"""
        schemas = get_all_table_schemas()
        
        with self.cursor() as cursor:
            for table_name, create_sql in schemas.items():
                try:
                    cursor.execute(create_sql)
                    print(f"✅ 表 {table_name} 创建完成")
                except Exception as e:
                    print(f"⚠️ 表 {table_name} 创建失败: {e}")
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            config_dict = self.config.to_dict()
            config_dict.pop('cursorclass', None)
            config_dict['database'] = None
            
            conn = pymysql.connect(**config_dict)
            with conn.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()
                print(f"✅ MySQL服务器连接成功，版本: {version[0]}")
            conn.close()
            return True
        except Exception as e:
            print(f"❌ MySQL连接失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self._connection and self._connection.open:
            self._connection.close()
            self._connection = None


class DataRepositoryV2:
    """数据仓库类 V2"""
    
    def __init__(self, db_manager: DatabaseManagerV2):
        """
        初始化数据仓库
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
    
    # ==================== 公司信息操作 ====================
    
    def create_company(self, symbol: str, name: str, market: str, 
                       name_en: str = None, industry: str = None,
                       exchange: str = None, **kwargs) -> int:
        """
        创建或更新公司记录
        
        Args:
            symbol: 股票代码
            name: 公司名称
            market: 市场类型
            name_en: 英文名称
            industry: 行业
            exchange: 交易所
            
        Returns:
            公司ID
        """
        with self.db.cursor() as cursor:
            # 获取市场配置
            market_config = get_market_config(MarketType(market))
            currency = market_config.get('currency', 'CNY')
            
            sql = """
                INSERT INTO companies (symbol, name, name_en, market, exchange, 
                                     industry, currency, ts_code)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                name_en = VALUES(name_en),
                industry = VALUES(industry),
                exchange = VALUES(exchange),
                updated_at = CURRENT_TIMESTAMP
            """
            ts_code = kwargs.get('ts_code', f"{symbol}.{exchange}")
            cursor.execute(sql, (symbol, name, name_en, market, exchange, 
                               industry, currency, ts_code))
            
            # 获取公司ID
            cursor.execute("SELECT id FROM companies WHERE symbol = %s AND market = %s", 
                         (symbol, market))
            result = cursor.fetchone()
            return result['id'] if result else None
    
    def get_company(self, company_id: int = None, symbol: str = None, 
                   market: str = None) -> Optional[Dict]:
        """获取公司信息"""
        with self.db.cursor() as cursor:
            if company_id:
                cursor.execute("SELECT * FROM companies WHERE id = %s", (company_id,))
            elif symbol and market:
                cursor.execute("SELECT * FROM companies WHERE symbol = %s AND market = %s", 
                             (symbol, market))
            else:
                return None
            
            return cursor.fetchone()
    
    def get_all_companies(self, market: str = None) -> List[Dict]:
        """获取公司列表"""
        with self.db.cursor() as cursor:
            if market:
                cursor.execute("SELECT * FROM companies WHERE market = %s ORDER BY name", 
                             (market,))
            else:
                cursor.execute("SELECT * FROM companies ORDER BY market, name")
            return cursor.fetchall()
    
    # ==================== 财务数据操作 ====================
    
    def save_financial_report(self, company_id: int, data: Dict) -> int:
        """
        保存财务报告
        
        Args:
            company_id: 公司ID
            data: 财务数据字典
            
        Returns:
            记录ID
        """
        with self.db.cursor() as cursor:
            # 构建字段和值
            fields = ['company_id']
            values = [company_id]
            updates = []
            
            for key, value in data.items():
                if key not in ['id', 'company_id', 'created_at', 'updated_at']:
                    fields.append(key)
                    values.append(value)
                    updates.append(f"{key} = VALUES({key})")
            
            sql = f"""
                INSERT INTO financial_reports ({', '.join(fields)})
                VALUES ({', '.join(['%s'] * len(values))})
                ON DUPLICATE KEY UPDATE
                {', '.join(updates)},
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(sql, values)
            return cursor.lastrowid
    
    def get_financial_reports(self, company_id: int, 
                             report_type: str = None,
                             start_date: str = None,
                             end_date: str = None) -> List[Dict]:
        """获取财务报告列表"""
        with self.db.cursor() as cursor:
            sql = "SELECT * FROM financial_reports WHERE company_id = %s"
            params = [company_id]
            
            if report_type:
                sql += " AND report_type = %s"
                params.append(report_type)
            if start_date:
                sql += " AND report_date >= %s"
                params.append(start_date)
            if end_date:
                sql += " AND report_date <= %s"
                params.append(end_date)
            
            sql += " ORDER BY report_date DESC"
            
            cursor.execute(sql, params)
            return cursor.fetchall()
    
    def get_financial_metrics(self, company_id: int, 
                             metrics: List[str],
                             years: int = 5) -> Dict[str, List]:
        """
        获取指定财务指标的历史数据
        
        Args:
            company_id: 公司ID
            metrics: 指标名称列表
            years: 查询年数
            
        Returns:
            指标数据字典
        """
        with self.db.cursor() as cursor:
            sql = f"""
                SELECT report_date, fiscal_year, {', '.join(metrics)}
                FROM financial_reports 
                WHERE company_id = %s AND report_type = 'annual'
                ORDER BY report_date DESC
                LIMIT %s
            """
            cursor.execute(sql, (company_id, years))
            rows = cursor.fetchall()
            
            # 转换为指标字典
            result = {metric: [] for metric in metrics}
            result['years'] = []
            result['dates'] = []
            
            for row in reversed(rows):
                result['years'].append(row['fiscal_year'])
                result['dates'].append(row['report_date'])
                for metric in metrics:
                    result[metric].append(row.get(metric))
            
            return result
    
    # ==================== 数据源操作 ====================
    
    def create_data_source(self, config: Dict) -> int:
        """创建数据源配置"""
        with self.db.cursor() as cursor:
            sql = """
                INSERT INTO data_sources 
                (source_name, source_type, db_host, db_port, db_name, 
                 db_username, db_password, excel_path, market, 
                 table_mapping, field_mapping, sync_schedule)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                config.get('source_name'),
                config.get('source_type'),
                config.get('db_host'),
                config.get('db_port'),
                config.get('db_name'),
                config.get('db_username'),
                config.get('db_password'),
                config.get('excel_path'),
                config.get('market'),
                json.dumps(config.get('table_mapping', {})),
                json.dumps(config.get('field_mapping', {})),
                config.get('sync_schedule', 'manual')
            ))
            return cursor.lastrowid
    
    def get_data_sources(self, source_type: str = None) -> List[Dict]:
        """获取数据源列表"""
        with self.db.cursor() as cursor:
            if source_type:
                cursor.execute("SELECT * FROM data_sources WHERE source_type = %s", 
                             (source_type,))
            else:
                cursor.execute("SELECT * FROM data_sources")
            return cursor.fetchall()
    
    # ==================== 导入日志操作 ====================
    
    def create_import_log(self, source_id: int, import_type: str = 'full') -> int:
        """创建导入日志"""
        with self.db.cursor() as cursor:
            sql = """
                INSERT INTO import_logs (source_id, import_type, start_time, status)
                VALUES (%s, %s, CURRENT_TIMESTAMP, 'running')
            """
            cursor.execute(sql, (source_id, import_type))
            return cursor.lastrowid
    
    def update_import_log(self, log_id: int, status: str, 
                         records_count: int = 0,
                         success_count: int = 0,
                         failed_count: int = 0,
                         error_message: str = None):
        """更新导入日志"""
        with self.db.cursor() as cursor:
            sql = """
                UPDATE import_logs 
                SET status = %s, end_time = CURRENT_TIMESTAMP,
                    records_count = %s, success_count = %s, failed_count = %s,
                    error_message = %s
                WHERE id = %s
            """
            cursor.execute(sql, (status, records_count, success_count, 
                               failed_count, error_message, log_id))


def init_database_with_config(host: str, port: int, database: str, 
                              user: str, password: str) -> bool:
    """
    使用指定配置初始化数据库
    
    Args:
        host: 主机地址
        port: 端口号
        database: 数据库名
        user: 用户名
        password: 密码
        
    Returns:
        是否成功
    """
    config = DBConfig(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
    db_manager = DatabaseManagerV2(config)
    
    try:
        if not db_manager.test_connection():
            return False
        
        db_manager.init_database()
        print("✅ 数据库初始化完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        return False
    finally:
        db_manager.close()


if __name__ == "__main__":
    # 测试代码
    print("数据库模块 V2 测试")
    print("-" * 50)
    
    db_manager = DatabaseManagerV2()
    
    if db_manager.test_connection():
        db_manager.init_database()
        
        repo = DataRepositoryV2(db_manager)
        
        # 创建测试公司
        company_id = repo.create_company(
            symbol="000001",
            name="测试公司",
            market="a_share",
            industry="医药制造"
        )
        print(f"创建公司，ID: {company_id}")
    
    db_manager.close()
