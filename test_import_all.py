"""测试所有导入"""
try:
    print("测试导入 streamlit...")
    import streamlit as st
    print("✅ streamlit 导入成功")
    
    print("测试导入 pandas...")
    import pandas as pd
    print("✅ pandas 导入成功")
    
    print("测试导入 plotly...")
    import plotly.express as px
    import plotly.graph_objects as go
    print("✅ plotly 导入成功")
    
    print("测试导入 data_import_module...")
    from data_import_module import DataImportManager, DataSourceConfig
    print("✅ data_import_module 导入成功")
    
    print("测试导入 database_schema_v2...")
    from database_schema_v2 import DatabaseSchemaV2
    print("✅ database_schema_v2 导入成功")
    
    print("\n所有导入成功！")
    
except Exception as e:
    print(f"❌ 导入失败: {e}")
    import traceback
    traceback.print_exc()
