"""
数据管理模块UI - 超简化版
"""

import streamlit as st

def render_data_module():
    """渲染数据管理模块"""
    st.header("📊 数据管理")
    st.markdown("财务数据导入、提取、查询和可视化分析")
    
    st.write("这是数据管理模块的内容")
    st.write("测试测试测试")
    
    # 简单的标签页
    tabs = st.tabs(["概览", "导入", "提取"])
    
    with tabs[0]:
        st.write("概览内容")
    with tabs[1]:
        st.write("导入内容")
    with tabs[2]:
        st.write("提取内容")
