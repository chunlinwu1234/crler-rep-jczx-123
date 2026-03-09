"""
数据库初始化脚本
"""
from database import init_database_with_config

if __name__ == "__main__":
    print("正在初始化MySQL数据库...")
    print("-" * 50)
    
    success = init_database_with_config(
        host='localhost',
        port=3306,
        database='cims_db',
        user='root',
        password='root'
    )
    
    if success:
        print("-" * 50)
        print("✅ 数据库初始化成功！")
    else:
        print("-" * 50)
        print("❌ 数据库初始化失败！")
