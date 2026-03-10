"""
初始化数据库V2架构
支持多市场、支持MySQL和Excel导入
"""
import pymysql
from database_schema_v2 import DatabaseSchemaV2, generate_a_share_mapping


def init_database_v2(host='localhost', port=3306, database='cims_db', 
                     user='root', password='root'):
    """
    初始化数据库V2架构
    
    Args:
        host: 主机地址
        port: 端口号
        database: 数据库名
        user: 用户名
        password: 密码
        
    Returns:
        是否成功
    """
    print("=" * 80)
    print("CIMS 数据库V2架构初始化")
    print("=" * 80)
    
    # 1. 连接MySQL服务器（不指定数据库）
    print("\n1. 连接MySQL服务器...")
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        print("✅ MySQL服务器连接成功")
    except Exception as e:
        print(f"❌ MySQL连接失败: {e}")
        return False
    
    # 2. 创建数据库
    print(f"\n2. 创建数据库 {database}...")
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                CREATE DATABASE IF NOT EXISTS {database} 
                CHARACTER SET utf8mb4 
                COLLATE utf8mb4_unicode_ci
            """)
        print(f"✅ 数据库 {database} 已创建或已存在")
    except Exception as e:
        print(f"❌ 创建数据库失败: {e}")
        conn.close()
        return False
    
    conn.close()
    
    # 3. 连接新创建的数据库
    print(f"\n3. 连接数据库 {database}...")
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        print(f"✅ 数据库连接成功")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    
    # 4. 创建数据表
    print("\n4. 创建数据表...")
    try:
        sql = DatabaseSchemaV2.generate_create_table_sql()
        
        with conn.cursor() as cursor:
            # 分割SQL语句并执行
            statements = sql.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    try:
                        cursor.execute(statement + ';')
                    except Exception as e:
                        if 'already exists' in str(e).lower():
                            print(f"  ⚠️ 表已存在，跳过")
                        else:
                            print(f"  ❌ 执行SQL失败: {e}")
                            print(f"  SQL: {statement[:100]}...")
        
        conn.commit()
        print("✅ 数据表创建完成")
    except Exception as e:
        print(f"❌ 创建数据表失败: {e}")
        conn.close()
        return False
    
    # 5. 初始化A股字段映射
    print("\n5. 初始化A股字段映射...")
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
                    mapping['market'],
                    mapping['local_field_name'],
                    mapping['local_field_name_en'],
                    mapping['standard_field_name'],
                    mapping['field_category'],
                    mapping['data_type'],
                    mapping['description'],
                    mapping['description_en'],
                    mapping['is_required']
                ))
        
        conn.commit()
        print(f"✅ 已初始化 {len(mappings)} 个A股字段映射")
    except Exception as e:
        print(f"❌ 初始化字段映射失败: {e}")
        conn.close()
        return False
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ 数据库V2架构初始化完成！")
    print("=" * 80)
    print("\n创建的表：")
    print("  - companies (公司信息表)")
    print("  - financial_reports (财务报表核心表)")
    print("  - market_field_mapping (市场字段映射表)")
    print("  - data_sources (数据源配置表)")
    print("  - import_logs (数据导入日志表)")
    print("  - ai_extraction_logs (AI提取文档记录表)")
    print("\n支持的市场：")
    for code, info in DatabaseSchemaV2.MARKETS.items():
        print(f"  - {code}: {info['name']} ({info['name_en']}) [{info['currency']}]")
    
    return True


if __name__ == "__main__":
    import sys
    
    # 默认配置
    host = 'localhost'
    port = 3306
    database = 'cims_db'
    user = 'root'
    password = 'root'
    
    # 可以通过命令行参数覆盖
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    if len(sys.argv) > 3:
        database = sys.argv[3]
    if len(sys.argv) > 4:
        user = sys.argv[4]
    if len(sys.argv) > 5:
        password = sys.argv[5]
    
    success = init_database_v2(host, port, database, user, password)
    
    if not success:
        exit(1)
