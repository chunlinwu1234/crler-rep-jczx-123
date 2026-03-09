"""
数据提取与存储模块
使用MySQL数据库存储结构化数据
"""

import os
import json
import pymysql
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class DBConfig:
    """数据库配置类"""
    host: str = "localhost"
    port: int = 3306
    database: str = "cims_db"
    user: str = "root"
    password: str = ""
    charset: str = "utf8mb4"
    
    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            database=os.getenv("MYSQL_DATABASE", "cims_db"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            charset="utf8mb4"
        )
    
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


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: DBConfig = None):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置，如果为None则从环境变量加载
        """
        self.config = config or DBConfig.from_env()
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
                # 创建数据库
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.config.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"✅ 数据库 {self.config.database} 已创建或已存在")
        finally:
            conn.close()
        
        # 创建表结构
        self._create_tables()
    
    def _create_tables(self):
        """创建数据表"""
        with self.cursor() as cursor:
            # 公司信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL COMMENT '公司名称',
                    stock_code VARCHAR(20) COMMENT '股票代码',
                    industry VARCHAR(50) COMMENT '所属行业',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uk_stock_code (stock_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公司信息表'
            """)
            
            # 文档元数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company_id INT NOT NULL COMMENT '公司ID',
                    file_name VARCHAR(255) NOT NULL COMMENT '文件名',
                    file_path VARCHAR(500) COMMENT '文件路径',
                    doc_type VARCHAR(50) COMMENT '文档类型(年报/半年报/季报/公告)',
                    report_year INT COMMENT '报告年份',
                    report_period VARCHAR(20) COMMENT '报告期(年度/半年度/第一季度/第二季度/第三季度)',
                    extracted BOOLEAN DEFAULT FALSE COMMENT '是否已提取数据',
                    extracted_at TIMESTAMP NULL COMMENT '数据提取时间',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    INDEX idx_company_year (company_id, report_year)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档元数据表'
            """)
            
            # 财务数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS financial_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company_id INT NOT NULL COMMENT '公司ID',
                    document_id INT COMMENT '文档ID',
                    report_date DATE COMMENT '报告期',
                    report_year INT COMMENT '报告年份',
                    
                    -- 利润表关键指标
                    revenue DECIMAL(20, 2) COMMENT '营业收入(元)',
                    operating_cost DECIMAL(20, 2) COMMENT '营业成本(元)',
                    gross_profit DECIMAL(20, 2) COMMENT '毛利润(元)',
                    operating_profit DECIMAL(20, 2) COMMENT '营业利润(元)',
                    net_profit DECIMAL(20, 2) COMMENT '净利润(元)',
                    net_profit_parent DECIMAL(20, 2) COMMENT '归母净利润(元)',
                    
                    -- 资产负债表关键指标
                    total_assets DECIMAL(20, 2) COMMENT '总资产(元)',
                    total_liabilities DECIMAL(20, 2) COMMENT '总负债(元)',
                    equity DECIMAL(20, 2) COMMENT '股东权益(元)',
                    current_assets DECIMAL(20, 2) COMMENT '流动资产(元)',
                    current_liabilities DECIMAL(20, 2) COMMENT '流动负债(元)',
                    inventory DECIMAL(20, 2) COMMENT '存货(元)',
                    accounts_receivable DECIMAL(20, 2) COMMENT '应收账款(元)',
                    
                    -- 现金流量表关键指标
                    operating_cash_flow DECIMAL(20, 2) COMMENT '经营活动现金流(元)',
                    investing_cash_flow DECIMAL(20, 2) COMMENT '投资活动现金流(元)',
                    financing_cash_flow DECIMAL(20, 2) COMMENT '筹资活动现金流(元)',
                    
                    -- 比率指标
                    gross_margin DECIMAL(5, 2) COMMENT '毛利率(%)',
                    net_margin DECIMAL(5, 2) COMMENT '净利率(%)',
                    roe DECIMAL(5, 2) COMMENT '净资产收益率ROE(%)',
                    roa DECIMAL(5, 2) COMMENT '总资产收益率ROA(%)',
                    debt_ratio DECIMAL(5, 2) COMMENT '资产负债率(%)',
                    current_ratio DECIMAL(5, 2) COMMENT '流动比率',
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL,
                    UNIQUE KEY uk_company_date (company_id, report_date),
                    INDEX idx_year (report_year)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务数据表'
            """)
            
            # 业务数据表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS business_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company_id INT NOT NULL COMMENT '公司ID',
                    document_id INT COMMENT '文档ID',
                    report_date DATE COMMENT '报告期',
                    report_year INT COMMENT '报告年份',
                    
                    -- 研发数据
                    r_d_investment DECIMAL(20, 2) COMMENT '研发投入(元)',
                    r_d_expense DECIMAL(20, 2) COMMENT '研发费用(元)',
                    r_d_capitalized DECIMAL(20, 2) COMMENT '研发资本化金额(元)',
                    r_d_intensity DECIMAL(5, 2) COMMENT '研发强度(%)',
                    
                    -- 人员数据
                    employee_count INT COMMENT '员工人数',
                    r_d_personnel INT COMMENT '研发人员数量',
                    
                    -- 生产数据
                    production_capacity VARCHAR(500) COMMENT '产能情况',
                    capacity_utilization DECIMAL(5, 2) COMMENT '产能利用率(%)',
                    
                    -- 市场数据
                    market_share DECIMAL(5, 2) COMMENT '市场份额(%)',
                    domestic_revenue DECIMAL(20, 2) COMMENT '国内收入(元)',
                    overseas_revenue DECIMAL(20, 2) COMMENT '海外收入(元)',
                    
                    -- 产品数据
                    main_products TEXT COMMENT '主要产品',
                    new_products TEXT COMMENT '新产品',
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL,
                    UNIQUE KEY uk_company_date (company_id, report_date),
                    INDEX idx_year (report_year)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='业务数据表'
            """)
            
            # 战略与业务信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategic_info (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    company_id INT NOT NULL COMMENT '公司ID',
                    document_id INT COMMENT '文档ID',
                    report_date DATE COMMENT '报告期',
                    
                    -- 战略信息
                    company_mission TEXT COMMENT '公司使命',
                    company_vision TEXT COMMENT '公司愿景',
                    core_values TEXT COMMENT '核心价值观',
                    strategic_goals TEXT COMMENT '战略目标',
                    key_strategies TEXT COMMENT '关键战略举措',
                    
                    -- SWOT分析
                    strengths TEXT COMMENT '优势',
                    weaknesses TEXT COMMENT '劣势',
                    opportunities TEXT COMMENT '机会',
                    threats TEXT COMMENT '威胁',
                    
                    -- 商业模式
                    business_model TEXT COMMENT '商业模式描述',
                    value_proposition TEXT COMMENT '价值主张',
                    customer_segments TEXT COMMENT '客户细分',
                    revenue_streams TEXT COMMENT '收入来源',
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL,
                    UNIQUE KEY uk_company_date (company_id, report_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='战略与业务信息表'
            """)
            
            print("✅ 数据表创建完成")
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            # 先测试服务器连接（不指定数据库）
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


class DataRepository:
    """数据仓库类，提供数据的增删改查操作"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化数据仓库
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
    
    # ==================== 公司信息操作 ====================
    
    def create_company(self, name: str, stock_code: str = None, industry: str = None) -> int:
        """
        创建公司记录
        
        Args:
            name: 公司名称
            stock_code: 股票代码
            industry: 所属行业
            
        Returns:
            公司ID
        """
        with self.db.cursor() as cursor:
            sql = """
                INSERT INTO companies (name, stock_code, industry)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                industry = VALUES(industry),
                updated_at = CURRENT_TIMESTAMP
            """
            cursor.execute(sql, (name, stock_code, industry))
            
            # 获取公司ID
            if stock_code:
                cursor.execute("SELECT id FROM companies WHERE stock_code = %s", (stock_code,))
            else:
                cursor.execute("SELECT id FROM companies WHERE name = %s", (name,))
            
            result = cursor.fetchone()
            return result['id'] if result else None
    
    def get_company(self, company_id: int = None, stock_code: str = None, name: str = None) -> Optional[Dict]:
        """
        获取公司信息
        
        Args:
            company_id: 公司ID
            stock_code: 股票代码
            name: 公司名称
            
        Returns:
            公司信息字典
        """
        with self.db.cursor() as cursor:
            if company_id:
                cursor.execute("SELECT * FROM companies WHERE id = %s", (company_id,))
            elif stock_code:
                cursor.execute("SELECT * FROM companies WHERE stock_code = %s", (stock_code,))
            elif name:
                cursor.execute("SELECT * FROM companies WHERE name = %s", (name,))
            else:
                return None
            
            return cursor.fetchone()
    
    def get_all_companies(self) -> List[Dict]:
        """获取所有公司列表"""
        with self.db.cursor() as cursor:
            cursor.execute("SELECT * FROM companies ORDER BY name")
            return cursor.fetchall()
    
    # ==================== 文档操作 ====================
    
    def create_document(self, company_id: int, file_name: str, file_path: str = None,
                       doc_type: str = None, report_year: int = None, 
                       report_period: str = None) -> int:
        """
        创建文档记录
        
        Args:
            company_id: 公司ID
            file_name: 文件名
            file_path: 文件路径
            doc_type: 文档类型
            report_year: 报告年份
            report_period: 报告期
            
        Returns:
            文档ID
        """
        with self.db.cursor() as cursor:
            sql = """
                INSERT INTO documents (company_id, file_name, file_path, doc_type, 
                                     report_year, report_period)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (company_id, file_name, file_path, doc_type, 
                               report_year, report_period))
            return cursor.lastrowid
    
    def update_document_extracted(self, document_id: int, extracted: bool = True):
        """
        更新文档提取状态
        
        Args:
            document_id: 文档ID
            extracted: 是否已提取
        """
        with self.db.cursor() as cursor:
            if extracted:
                cursor.execute("""
                    UPDATE documents 
                    SET extracted = %s, extracted_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (extracted, document_id))
            else:
                cursor.execute("""
                    UPDATE documents 
                    SET extracted = %s, extracted_at = NULL
                    WHERE id = %s
                """, (extracted, document_id))
    
    def get_documents_by_company(self, company_id: int, doc_type: str = None) -> List[Dict]:
        """
        获取公司的文档列表
        
        Args:
            company_id: 公司ID
            doc_type: 文档类型筛选
            
        Returns:
            文档列表
        """
        with self.db.cursor() as cursor:
            if doc_type:
                cursor.execute("""
                    SELECT * FROM documents 
                    WHERE company_id = %s AND doc_type = %s
                    ORDER BY report_year DESC, created_at DESC
                """, (company_id, doc_type))
            else:
                cursor.execute("""
                    SELECT * FROM documents 
                    WHERE company_id = %s
                    ORDER BY report_year DESC, created_at DESC
                """, (company_id,))
            return cursor.fetchall()
    
    # ==================== 财务数据操作 ====================
    
    def save_financial_data(self, company_id: int, data: Dict, document_id: int = None) -> int:
        """
        保存财务数据
        
        Args:
            company_id: 公司ID
            data: 财务数据字典
            document_id: 文档ID
            
        Returns:
            记录ID
        """
        with self.db.cursor() as cursor:
            # 构建SQL语句
            fields = ['company_id', 'document_id']
            values = [company_id, document_id]
            updates = []
            
            for key, value in data.items():
                if key not in ['id', 'company_id', 'document_id', 'created_at', 'updated_at']:
                    fields.append(key)
                    values.append(value)
                    updates.append(f"{key} = VALUES({key})")
            
            sql = f"""
                INSERT INTO financial_data ({', '.join(fields)})
                VALUES ({', '.join(['%s'] * len(values))})
                ON DUPLICATE KEY UPDATE
                {', '.join(updates)},
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(sql, values)
            return cursor.lastrowid
    
    def get_financial_data(self, company_id: int, start_year: int = None, 
                          end_year: int = None) -> List[Dict]:
        """
        获取财务数据
        
        Args:
            company_id: 公司ID
            start_year: 起始年份
            end_year: 结束年份
            
        Returns:
            财务数据列表
        """
        with self.db.cursor() as cursor:
            if start_year and end_year:
                cursor.execute("""
                    SELECT * FROM financial_data 
                    WHERE company_id = %s AND report_year BETWEEN %s AND %s
                    ORDER BY report_year ASC
                """, (company_id, start_year, end_year))
            elif start_year:
                cursor.execute("""
                    SELECT * FROM financial_data 
                    WHERE company_id = %s AND report_year >= %s
                    ORDER BY report_year ASC
                """, (company_id, start_year))
            elif end_year:
                cursor.execute("""
                    SELECT * FROM financial_data 
                    WHERE company_id = %s AND report_year <= %s
                    ORDER BY report_year ASC
                """, (company_id, end_year))
            else:
                cursor.execute("""
                    SELECT * FROM financial_data 
                    WHERE company_id = %s
                    ORDER BY report_year ASC
                """, (company_id,))
            
            return cursor.fetchall()
    
    def get_financial_metrics(self, company_id: int, metrics: List[str], 
                             years: int = 5) -> Dict[str, List]:
        """
        获取指定财务指标的历史数据
        
        Args:
            company_id: 公司ID
            metrics: 指标名称列表
            years: 查询年数
            
        Returns:
            指标数据字典 {指标名: [数值列表]}
        """
        with self.db.cursor() as cursor:
            # 获取最近N年的数据
            cursor.execute("""
                SELECT report_year, {metrics}
                FROM financial_data 
                WHERE company_id = %s
                ORDER BY report_year DESC
                LIMIT %s
            """.format(metrics=', '.join(metrics)), (company_id, years))
            
            rows = cursor.fetchall()
            
            # 转换为指标字典
            result = {metric: [] for metric in metrics}
            years_list = []
            
            for row in reversed(rows):  # 反转，按年份升序
                years_list.append(row['report_year'])
                for metric in metrics:
                    result[metric].append(row.get(metric))
            
            result['years'] = years_list
            return result
    
    # ==================== 业务数据操作 ====================
    
    def save_business_data(self, company_id: int, data: Dict, document_id: int = None) -> int:
        """
        保存业务数据
        
        Args:
            company_id: 公司ID
            data: 业务数据字典
            document_id: 文档ID
            
        Returns:
            记录ID
        """
        with self.db.cursor() as cursor:
            fields = ['company_id', 'document_id']
            values = [company_id, document_id]
            updates = []
            
            for key, value in data.items():
                if key not in ['id', 'company_id', 'document_id', 'created_at', 'updated_at']:
                    fields.append(key)
                    values.append(value)
                    updates.append(f"{key} = VALUES({key})")
            
            sql = f"""
                INSERT INTO business_data ({', '.join(fields)})
                VALUES ({', '.join(['%s'] * len(values))})
                ON DUPLICATE KEY UPDATE
                {', '.join(updates)},
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(sql, values)
            return cursor.lastrowid
    
    def get_business_data(self, company_id: int, start_year: int = None, 
                         end_year: int = None) -> List[Dict]:
        """获取业务数据"""
        with self.db.cursor() as cursor:
            if start_year and end_year:
                cursor.execute("""
                    SELECT * FROM business_data 
                    WHERE company_id = %s AND report_year BETWEEN %s AND %s
                    ORDER BY report_year ASC
                """, (company_id, start_year, end_year))
            elif start_year:
                cursor.execute("""
                    SELECT * FROM business_data 
                    WHERE company_id = %s AND report_year >= %s
                    ORDER BY report_year ASC
                """, (company_id, start_year))
            elif end_year:
                cursor.execute("""
                    SELECT * FROM business_data 
                    WHERE company_id = %s AND report_year <= %s
                    ORDER BY report_year ASC
                """, (company_id, end_year))
            else:
                cursor.execute("""
                    SELECT * FROM business_data 
                    WHERE company_id = %s
                    ORDER BY report_year ASC
                """, (company_id,))
            
            return cursor.fetchall()
    
    # ==================== 战略信息操作 ====================
    
    def save_strategic_info(self, company_id: int, data: Dict, document_id: int = None) -> int:
        """
        保存战略信息
        
        Args:
            company_id: 公司ID
            data: 战略信息字典
            document_id: 文档ID
            
        Returns:
            记录ID
        """
        with self.db.cursor() as cursor:
            fields = ['company_id', 'document_id']
            values = [company_id, document_id]
            updates = []
            
            for key, value in data.items():
                if key not in ['id', 'company_id', 'document_id', 'created_at', 'updated_at']:
                    fields.append(key)
                    values.append(value)
                    updates.append(f"{key} = VALUES({key})")
            
            sql = f"""
                INSERT INTO strategic_info ({', '.join(fields)})
                VALUES ({', '.join(['%s'] * len(values))})
                ON DUPLICATE KEY UPDATE
                {', '.join(updates)},
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(sql, values)
            return cursor.lastrowid
    
    def get_strategic_info(self, company_id: int, report_date: str = None) -> Optional[Dict]:
        """
        获取战略信息
        
        Args:
            company_id: 公司ID
            report_date: 报告日期
            
        Returns:
            战略信息字典
        """
        with self.db.cursor() as cursor:
            if report_date:
                cursor.execute("""
                    SELECT * FROM strategic_info 
                    WHERE company_id = %s AND report_date = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (company_id, report_date))
            else:
                cursor.execute("""
                    SELECT * FROM strategic_info 
                    WHERE company_id = %s
                    ORDER BY report_date DESC, created_at DESC
                    LIMIT 1
                """, (company_id,))
            
            return cursor.fetchone()
    
    # ==================== 对比分析操作 ====================
    
    def compare_companies(self, company_ids: List[int], metric: str, 
                         year: int = None) -> List[Dict]:
        """
        对比多家公司的某项指标
        
        Args:
            company_ids: 公司ID列表
            metric: 指标名称
            year: 年份，为None则取最新数据
            
        Returns:
            对比结果列表
        """
        with self.db.cursor() as cursor:
            if year:
                # 指定年份的数据
                cursor.execute(f"""
                    SELECT c.name as company_name, c.stock_code, fd.{metric}
                    FROM financial_data fd
                    JOIN companies c ON fd.company_id = c.id
                    WHERE fd.company_id IN %s AND fd.report_year = %s
                    ORDER BY fd.{metric} DESC
                """, (tuple(company_ids), year))
            else:
                # 最新数据
                cursor.execute(f"""
                    SELECT c.name as company_name, c.stock_code, fd.{metric}, fd.report_year
                    FROM financial_data fd
                    JOIN companies c ON fd.company_id = c.id
                    INNER JOIN (
                        SELECT company_id, MAX(report_year) as max_year
                        FROM financial_data
                        WHERE company_id IN %s
                        GROUP BY company_id
                    ) latest ON fd.company_id = latest.company_id 
                            AND fd.report_year = latest.max_year
                    WHERE fd.company_id IN %s
                    ORDER BY fd.{metric} DESC
                """, (tuple(company_ids), tuple(company_ids)))
            
            return cursor.fetchall()


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
    
    db_manager = DatabaseManager(config)
    
    try:
        # 测试连接
        if not db_manager.test_connection():
            return False
        
        # 初始化数据库和表
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
    print("数据库模块测试")
    print("-" * 50)
    
    # 从环境变量加载配置
    db_manager = DatabaseManager()
    
    if db_manager.test_connection():
        db_manager.init_database()
        
        # 测试数据仓库
        repo = DataRepository(db_manager)
        
        # 创建测试公司
        company_id = repo.create_company(
            name="测试公司",
            stock_code="000001",
            industry="医药制造"
        )
        print(f"创建公司，ID: {company_id}")
        
        # 查询公司
        company = repo.get_company(company_id=company_id)
        print(f"查询公司: {company}")
    
    db_manager.close()
