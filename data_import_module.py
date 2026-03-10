"""
数据导入模块
支持MySQL直连和Excel导入
支持多市场数据映射
"""

import os
import json
import pandas as pd
import pymysql
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from database_schema_v2 import DatabaseSchemaV2, generate_a_share_mapping


@dataclass
class DataSourceConfig:
    """数据源配置"""
    source_name: str
    source_type: str  # mysql/excel/api
    host: str = None
    port: int = None
    database: str = None
    username: str = None
    password: str = None
    file_path: str = None
    table_mapping: Dict = None
    field_mapping: Dict = None
    sync_schedule: str = 'manual'  # weekly/monthly/manual


class DataImportEngine:
    """数据导入引擎"""
    
    def __init__(self, db_config: Dict):
        """
        初始化导入引擎
        
        Args:
            db_config: 目标数据库配置
        """
        self.db_config = db_config
        self.db_connection = None
        self.source_config = None
        self.import_log_id = None
    
    def connect_target_db(self) -> bool:
        """连接目标数据库"""
        try:
            self.db_connection = pymysql.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return True
        except Exception as e:
            print(f"连接目标数据库失败: {e}")
            return False
    
    def test_source_connection(self, source_config: DataSourceConfig) -> Tuple[bool, str]:
        """
        测试数据源连接
        
        Args:
            source_config: 数据源配置
            
        Returns:
            (是否成功, 错误信息)
        """
        try:
            if source_config.source_type == 'mysql':
                conn = pymysql.connect(
                    host=source_config.host,
                    port=source_config.port,
                    database=source_config.database,
                    user=source_config.username,
                    password=source_config.password,
                    charset='utf8mb4',
                    connect_timeout=5
                )
                conn.close()
                return True, "连接成功"
            elif source_config.source_type == 'excel':
                if os.path.exists(source_config.file_path):
                    return True, "文件存在"
                else:
                    return False, "文件不存在"
            else:
                return False, f"不支持的数据源类型: {source_config.source_type}"
        except Exception as e:
            return False, str(e)
    
    def start_import(self, source_config: DataSourceConfig, 
                    import_type: str = 'incremental') -> int:
        """
        开始数据导入
        
        Args:
            source_config: 数据源配置
            import_type: 导入类型(full/incremental)
            
        Returns:
            导入日志ID
        """
        self.source_config = source_config
        
        # 记录导入日志
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO import_logs (source_id, import_type, start_time, status)
                VALUES (%s, %s, NOW(), 'running')
            """, (source_config.source_name, import_type))
            self.import_log_id = cursor.lastrowid
            self.db_connection.commit()
        
        try:
            if source_config.source_type == 'mysql':
                self._import_from_mysql()
            elif source_config.source_type == 'excel':
                self._import_from_excel()
            
            # 更新导入状态为成功
            self._update_import_status('success')
            
        except Exception as e:
            # 更新导入状态为失败
            self._update_import_status('failed', str(e))
            raise e
        
        return self.import_log_id
    
    def _import_from_mysql(self):
        """从MySQL导入数据"""
        # 连接源数据库
        source_conn = pymysql.connect(
            host=self.source_config.host,
            port=self.source_config.port,
            database=self.source_config.database,
            user=self.source_config.username,
            password=self.source_config.password,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        try:
            table_mapping = self.source_config.table_mapping or {}
            field_mapping = self.source_config.field_mapping or {}
            
            # 获取表映射关系
            source_tables = table_mapping.get('source_tables', [])
            target_table = table_mapping.get('target_table', 'financial_reports')
            
            total_records = 0
            success_records = 0
            failed_records = 0
            
            for source_table in source_tables:
                # 读取源数据
                with source_conn.cursor() as cursor:
                    cursor.execute(f"SELECT * FROM {source_table}")
                    source_data = cursor.fetchall()
                
                print(f"从 {source_table} 读取 {len(source_data)} 条记录")
                
                # 数据转换和导入
                for record in source_data:
                    try:
                        transformed_record = self._transform_record(
                            record, field_mapping, 'CN'
                        )
                        self._insert_or_update_record(transformed_record)
                        success_records += 1
                    except Exception as e:
                        print(f"导入记录失败: {e}")
                        failed_records += 1
                    
                    total_records += 1
            
            # 更新导入统计
            self._update_import_stats(total_records, success_records, failed_records)
            
        finally:
            source_conn.close()
    
    def _import_from_excel(self):
        """从Excel导入数据"""
        file_path = self.source_config.file_path
        field_mapping = self.source_config.field_mapping or {}
        
        # 读取Excel文件
        xl = pd.ExcelFile(file_path)
        
        total_records = 0
        success_records = 0
        failed_records = 0
        
        # 获取表映射关系
        sheet_mapping = field_mapping.get('sheet_mapping', {})
        
        for sheet_name in xl.sheet_names:
            if sheet_name not in sheet_mapping:
                continue
            
            # 读取sheet
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # 字段映射
            column_mapping = sheet_mapping.get(sheet_name, {})
            df = df.rename(columns=column_mapping)
            
            print(f"从 {sheet_name} 读取 {len(df)} 条记录")
            
            # 数据导入
            for _, row in df.iterrows():
                try:
                    record = row.to_dict()
                    # 处理NaN值
                    record = {k: v if pd.notna(v) else None for k, v in record.items()}
                    
                    transformed_record = self._transform_record(
                        record, field_mapping, 'CN'
                    )
                    self._insert_or_update_record(transformed_record)
                    success_records += 1
                except Exception as e:
                    print(f"导入记录失败: {e}")
                    failed_records += 1
                
                total_records += 1
        
        # 更新导入统计
        self._update_import_stats(total_records, success_records, failed_records)
    
    def _transform_record(self, record: Dict, field_mapping: Dict, 
                         market: str) -> Dict:
        """
        转换记录格式
        
        Args:
            record: 原始记录
            field_mapping: 字段映射配置
            market: 市场代码
            
        Returns:
            转换后的记录
        """
        transformed = {}
        
        # 获取市场字段映射
        market_mappings = self._get_market_field_mappings(market)
        
        for local_field, value in record.items():
            # 查找标准字段名
            standard_field = None
            for mapping in market_mappings:
                if mapping['local_field_name'] == local_field:
                    standard_field = mapping['standard_field_name']
                    break
            
            if standard_field:
                transformed[standard_field] = value
            else:
                # 保留原始字段到扩展数据
                if 'extended_data' not in transformed:
                    transformed['extended_data'] = {}
                transformed['extended_data'][local_field] = value
        
        # 处理公司信息
        if 'ts_code' in transformed:
            company_id = self._get_or_create_company(transformed['ts_code'], market)
            transformed['company_id'] = company_id
        
        # 序列化扩展数据
        if 'extended_data' in transformed:
            transformed['extended_data'] = json.dumps(transformed['extended_data'])
        
        return transformed
    
    def _get_market_field_mappings(self, market: str) -> List[Dict]:
        """获取市场字段映射"""
        # 从数据库读取映射配置
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM market_field_mapping WHERE market = %s
            """, (market,))
            return cursor.fetchall()
    
    def _get_or_create_company(self, ts_code: str, market: str) -> int:
        """获取或创建公司记录"""
        with self.db_connection.cursor() as cursor:
            # 查询公司是否存在
            cursor.execute("""
                SELECT id FROM companies WHERE ts_code = %s AND market = %s
            """, (ts_code, market))
            result = cursor.fetchone()
            
            if result:
                return result['id']
            
            # 创建新公司
            symbol = ts_code.split('.')[0] if '.' in ts_code else ts_code
            cursor.execute("""
                INSERT INTO companies (ts_code, symbol, market, currency)
                VALUES (%s, %s, %s, %s)
            """, (ts_code, symbol, market, DatabaseSchemaV2.MARKETS.get(market, {}).get('currency', 'CNY')))
            
            self.db_connection.commit()
            return cursor.lastrowid
    
    def _insert_or_update_record(self, record: Dict):
        """插入或更新记录"""
        # 构建SQL
        fields = []
        values = []
        updates = []
        
        for field, value in record.items():
            if field != 'id' and value is not None:
                fields.append(field)
                values.append(value)
                updates.append(f"{field} = VALUES({field})")
        
        if not fields:
            return
        
        sql = f"""
            INSERT INTO financial_reports ({', '.join(fields)})
            VALUES ({', '.join(['%s'] * len(values))})
            ON DUPLICATE KEY UPDATE
            {', '.join(updates)},
            updated_at = NOW()
        """
        
        with self.db_connection.cursor() as cursor:
            cursor.execute(sql, values)
            self.db_connection.commit()
    
    def _update_import_status(self, status: str, error_message: str = None):
        """更新导入状态"""
        with self.db_connection.cursor() as cursor:
            if error_message:
                cursor.execute("""
                    UPDATE import_logs 
                    SET status = %s, error_message = %s, end_time = NOW()
                    WHERE id = %s
                """, (status, error_message, self.import_log_id))
            else:
                cursor.execute("""
                    UPDATE import_logs 
                    SET status = %s, end_time = NOW()
                    WHERE id = %s
                """, (status, self.import_log_id))
            self.db_connection.commit()
    
    def _update_import_stats(self, total: int, success: int, failed: int):
        """更新导入统计"""
        with self.db_connection.cursor() as cursor:
            cursor.execute("""
                UPDATE import_logs 
                SET records_count = %s, success_count = %s, failed_count = %s
                WHERE id = %s
            """, (total, success, failed, self.import_log_id))
            self.db_connection.commit()
    
    def close(self):
        """关闭连接"""
        if self.db_connection:
            self.db_connection.close()


class DataImportManager:
    """数据导入管理器"""
    
    def __init__(self, db_config: Dict):
        """
        初始化管理器
        
        Args:
            db_config: 数据库配置
        """
        self.db_config = db_config
        self.engine = DataImportEngine(db_config)
    
    def save_data_source(self, config: DataSourceConfig) -> int:
        """
        保存数据源配置
        
        Args:
            config: 数据源配置
            
        Returns:
            数据源ID
        """
        conn = pymysql.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO data_sources 
                    (source_name, source_type, host, port, database_name, 
                     username, password, file_path, table_mapping, field_mapping, sync_schedule)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    source_type = VALUES(source_type),
                    host = VALUES(host),
                    port = VALUES(port),
                    database_name = VALUES(database_name),
                    username = VALUES(username),
                    password = VALUES(password),
                    file_path = VALUES(file_path),
                    table_mapping = VALUES(table_mapping),
                    field_mapping = VALUES(field_mapping),
                    sync_schedule = VALUES(sync_schedule),
                    updated_at = NOW()
                """, (
                    config.source_name, config.source_type, config.host, config.port,
                    config.database, config.username, config.password, config.file_path,
                    json.dumps(config.table_mapping) if config.table_mapping else None,
                    json.dumps(config.field_mapping) if config.field_mapping else None,
                    config.sync_schedule
                ))
                conn.commit()
                return cursor.lastrowid
        finally:
            conn.close()
    
    def get_data_sources(self) -> List[Dict]:
        """获取所有数据源配置"""
        conn = pymysql.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, source_name, source_type, host, port, database_name,
                           file_path, sync_schedule, is_active, last_sync_at, created_at
                    FROM data_sources WHERE is_active = TRUE
                    ORDER BY created_at DESC
                """)
                return cursor.fetchall()
        finally:
            conn.close()
    
    def initialize_a_share_mapping(self):
        """初始化A股字段映射"""
        conn = pymysql.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            database=self.db_config['database'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        try:
            mappings = generate_a_share_mapping()
            
            with conn.cursor() as cursor:
                for mapping in mappings:
                    cursor.execute("""
                        INSERT INTO market_field_mapping 
                        (market, local_field_name, local_field_name_en, standard_field_name,
                         field_category, data_type, description, description_en, is_required)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        description = VALUES(description),
                        description_en = VALUES(description_en),
                        is_required = VALUES(is_required)
                    """, (
                        mapping['market'], mapping['local_field_name'],
                        mapping['local_field_name_en'], mapping['standard_field_name'],
                        mapping['field_category'], mapping['data_type'],
                        mapping['description'], mapping['description_en'],
                        mapping['is_required']
                    ))
                conn.commit()
                print(f"已初始化 {len(mappings)} 个A股字段映射")
        finally:
            conn.close()


# 测试代码
if __name__ == "__main__":
    # 数据库配置
    db_config = {
        'host': 'localhost',
        'port': 3306,
        'database': 'cims_db',
        'user': 'root',
        'password': 'root'
    }
    
    # 创建管理器
    manager = DataImportManager(db_config)
    
    # 初始化A股字段映射
    manager.initialize_a_share_mapping()
    
    print("\n数据导入模块初始化完成")
