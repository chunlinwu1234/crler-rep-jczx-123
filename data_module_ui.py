"""
数据管理模块UI
与"AI分析"、"搜索下载"并列的独立模块
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


def render_data_module():
    """渲染数据管理模块"""
    st.header("📊 数据管理")
    st.markdown("财务数据导入、提取、查询和可视化分析")
    
    # 数据管理模块标签页
    tabs = st.tabs(["📈 数据概览", "📥 数据导入", "🤖 AI数据提取", "🔍 数据查询", "📊 数据分析"])
    
    with tabs[0]:
        render_data_overview()
    
    with tabs[1]:
        render_data_import()
    
    with tabs[2]:
        render_ai_extraction()
    
    with tabs[3]:
        render_data_query()
    
    with tabs[4]:
        render_data_analysis()


def render_data_overview():
    """渲染数据概览"""
    st.subheader("📈 数据概览")
    
    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏢 公司数量", "1,234", "+56 本月新增")
    with col2:
        st.metric("📄 报表数量", "15,678", "+892 本月新增")
    with col3:
        st.metric("📊 数据覆盖率", "98.5%", "+2.1%")
    with col4:
        st.metric("🔄 更新状态", "正常", "上次: 2小时前")
    
    st.markdown("---")
    
    # 市场分布
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 🌍 市场分布")
        market_data = pd.DataFrame({
            '市场': ['A股', '港股', '美股', '印度', '瑞士', '日本'],
            '公司数': [850, 234, 89, 45, 12, 4],
            '占比': [68.9, 19.0, 7.2, 3.6, 1.0, 0.3]
        })
        
        fig = px.pie(market_data, values='公司数', names='市场', 
                     title='各市场公司数量分布',
                     color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_right:
        st.markdown("#### 📈 数据增长趋势")
        trend_data = pd.DataFrame({
            '月份': ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05', '2024-06'],
            '新增记录': [1200, 1350, 1180, 1420, 1680, 1890]
        })
        
        fig = px.line(trend_data, x='月份', y='新增记录',
                      title='月度数据增长趋势',
                      markers=True)
        st.plotly_chart(fig, use_container_width=True)


def render_data_import():
    """渲染数据导入"""
    st.subheader("📥 数据导入")
    
    # 数据源选择
    source_type = st.radio(
        "选择数据源",
        ["MySQL数据库", "Excel文件", "API接口"],
        horizontal=True
    )
    
    if source_type == "MySQL数据库":
        with st.expander("🔌 数据库连接配置", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("主机地址", value="localhost", key="db_host")
                st.number_input("端口", value=3306, key="db_port")
                st.text_input("数据库名", value="cims_db", key="db_name")
            with col2:
                st.text_input("用户名", value="root", key="db_user")
                st.text_input("密码", type="password", value="root", key="db_pass")
            
            if st.button("🔗 测试连接", type="primary"):
                st.success("✅ 数据库连接成功！")
    
    elif source_type == "Excel文件":
        with st.expander("📁 文件上传", expanded=True):
            uploaded_file = st.file_uploader("选择Excel文件", type=['xlsx', 'xls'])
            if uploaded_file:
                st.success(f"✅ 文件已上传: {uploaded_file.name}")
                
                # 显示预览
                try:
                    df = pd.read_excel(uploaded_file)
                    st.markdown("#### 数据预览")
                    st.dataframe(df.head(10), use_container_width=True)
                except Exception as e:
                    st.error(f"读取文件失败: {e}")
    
    else:  # API接口
        with st.expander("🌐 API配置", expanded=True):
            st.text_input("API地址", placeholder="https://api.example.com/data")
            st.text_area("请求参数 (JSON)", placeholder='{"key": "value"}')
            st.button("🚀 获取数据", type="primary")


def render_ai_extraction():
    """渲染AI数据提取"""
    st.subheader("🤖 AI数据提取")
    
    # 文件选择
    st.markdown("#### 📄 选择财报文件")
    
    # 模拟文件列表
    file_options = [
        "600000_浦发银行_2023年报.pdf",
        "000001_平安银行_2023年报.pdf",
        "600036_招商银行_2023年报.pdf"
    ]
    
    selected_files = st.multiselect(
        "选择要处理的文件",
        file_options,
        default=file_options[:1]
    )
    
    # 提取维度
    st.markdown("#### 🎯 提取维度")
    
    dimensions = st.multiselect(
        "选择提取维度",
        ["财务摘要", "资产负债表", "利润表", "现金流量表", "财务指标", "业务分析"],
        default=["财务摘要", "财务指标"]
    )
    
    # 提取按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚀 开始提取", type="primary"):
            with st.spinner("AI正在提取数据..."):
                # 模拟处理
                import time
                time.sleep(2)
            st.success("✅ 数据提取完成！")
    
    with col2:
        st.checkbox("自动保存到数据库", value=True)


def render_data_query():
    """渲染数据查询"""
    st.subheader("🔍 数据查询")
    
    # 查询条件
    with st.expander("🔍 查询条件", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.text_input("公司名称", placeholder="输入公司名称或代码")
        
        with col2:
            st.selectbox("报表类型", ["全部", "年报", "半年报", "季报"])
        
        with col3:
            st.selectbox("年份", ["全部", "2024", "2023", "2022", "2021", "2020"])
        
        st.button("🔍 查询", type="primary")
    
    # 查询结果
    st.markdown("#### 📋 查询结果")
    
    # 模拟数据
    result_data = pd.DataFrame({
        '公司名称': ['浦发银行', '平安银行', '招商银行'],
        '股票代码': ['600000', '000001', '600036'],
        '报表类型': ['年报', '年报', '年报'],
        '年份': [2023, 2023, 2023],
        '营业收入(亿)': [1567.23, 1456.78, 2345.67],
        '净利润(亿)': [234.56, 289.34, 456.78]
    })
    
    st.dataframe(result_data, use_container_width=True)


def render_data_analysis():
    """渲染数据分析"""
    st.subheader("📊 数据分析")
    
    # 分析类型
    analysis_type = st.selectbox(
        "选择分析类型",
        ["财务趋势分析", "同业对比分析", "财务健康度评估", "异常数据检测"]
    )
    
    if analysis_type == "财务趋势分析":
        st.markdown("#### 📈 营收趋势")
        
        # 模拟数据
        trend_data = pd.DataFrame({
            '年份': [2019, 2020, 2021, 2022, 2023],
            '营业收入': [1456, 1567, 1678, 1789, 1890],
            '净利润': [234, 245, 267, 289, 312]
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=trend_data['年份'], y=trend_data['营业收入'],
            mode='lines+markers', name='营业收入',
            line=dict(color='#3498db', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=trend_data['年份'], y=trend_data['净利润'],
            mode='lines+markers', name='净利润',
            line=dict(color='#e74c3c', width=3)
        ))
        
        fig.update_layout(
            title='财务趋势分析',
            xaxis_title='年份',
            yaxis_title='金额(亿元)',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "同业对比分析":
        st.markdown("#### 📊 同业对比")
        
        comparison_data = pd.DataFrame({
            '公司': ['浦发银行', '平安银行', '招商银行', '行业平均'],
            'ROE(%)': [12.5, 14.2, 16.8, 14.5],
            '毛利率(%)': [35.2, 38.6, 42.1, 38.6]
        })
        
        fig = go.Figure(data=[
            go.Bar(name='ROE(%)', x=comparison_data['公司'], y=comparison_data['ROE(%)']),
            go.Bar(name='毛利率(%)', x=comparison_data['公司'], y=comparison_data['毛利率(%)'])
        ])
        
        fig.update_layout(
            title='同业对比分析',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
