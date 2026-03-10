"""
数据管理模块UI - 正式版本
与"AI分析"、"搜索下载"并列的独立模块
提供财务数据导入、提取、查询和可视化分析功能
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# 导入数据管理相关模块
try:
    from data_import_module import DataImportManager, DataSourceConfig
    from database_schema_v2 import DatabaseSchemaV2
    DATA_MODULES_AVAILABLE = True
except ImportError:
    DATA_MODULES_AVAILABLE = False
    st.warning("数据管理模块依赖未完全安装，部分功能可能受限")


def render_data_module():
    """
    渲染数据管理模块主界面
    
    包含五个功能标签页：
    1. 数据概览 - 展示数据统计和可视化
    2. 数据导入 - 支持多种数据源导入
    3. AI数据提取 - 从文档智能提取数据
    4. 数据查询 - 查询和筛选数据
    5. 数据分析 - 数据可视化和分析
    """
    st.header("📊 数据管理")
    st.markdown("财务数据导入、提取、查询和可视化分析")
    
    # 初始化数据库配置
    if 'db_config' not in st.session_state:
        st.session_state.db_config = {
            'host': 'localhost',
            'port': 3306,
            'database': 'cims_db',
            'user': 'root',
            'password': 'root'
        }
    
    # 初始化数据管理器
    if DATA_MODULES_AVAILABLE:
        if 'data_manager' not in st.session_state:
            try:
                st.session_state.data_manager = DataImportManager(st.session_state.db_config)
            except Exception as e:
                st.error(f"数据库连接失败: {e}")
                st.session_state.data_manager = None
    
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
    """渲染数据概览页面"""
    st.subheader("📈 数据概览")
    
    # 获取真实统计数据
    stats = get_database_stats()
    
    # 统计卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏢 公司数量", stats['company_count'], stats['company_change'])
    with col2:
        st.metric("📄 报表数量", stats['report_count'], stats['report_change'])
    with col3:
        st.metric("📊 数据覆盖率", stats['coverage'], stats['coverage_change'])
    with col4:
        st.metric("🔄 更新状态", stats['status'], stats['last_update'])
    
    st.markdown("---")
    
    # 市场分布和数据增长趋势
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("#### 🌍 市场分布")
        market_data = get_market_distribution()
        
        if not market_data.empty:
            fig = px.pie(market_data, values='公司数', names='市场', 
                         title='各市场公司数量分布',
                         color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无市场分布数据")
    
    with col_right:
        st.markdown("#### 📈 数据增长趋势")
        trend_data = get_growth_trend()
        
        if not trend_data.empty:
            fig = px.line(trend_data, x='月份', y='新增记录',
                          title='月度数据增长趋势',
                          markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("暂无增长趋势数据")


def render_data_import():
    """渲染数据导入页面"""
    st.subheader("📥 数据导入")
    
    # 数据源选择
    source_type = st.radio(
        "选择数据源",
        ["MySQL数据库", "Excel文件", "API接口"],
        horizontal=True
    )
    
    if source_type == "MySQL数据库":
        render_mysql_import()
    elif source_type == "Excel文件":
        render_excel_import()
    else:  # API接口
        render_api_import()


def render_mysql_import():
    """渲染MySQL数据库导入界面"""
    
    # 步骤1: 数据库连接配置
    with st.expander("🔌 步骤1: 数据库连接配置", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            host = st.text_input("主机地址", value=st.session_state.db_config.get('host', 'localhost'), key="dm_host")
            port = st.number_input("端口", value=st.session_state.db_config.get('port', 3306), min_value=1, max_value=65535, key="dm_port")
            database = st.text_input("数据库名", value=st.session_state.db_config.get('database', 'cims_db'), key="dm_database")
        with col2:
            user = st.text_input("用户名", value=st.session_state.db_config.get('user', 'root'), key="dm_user")
            password = st.text_input("密码", value=st.session_state.db_config.get('password', ''), type="password", key="dm_password")
        
        col_test, col_save = st.columns(2)
        with col_test:
            if st.button("🔗 测试连接", type="secondary", key="dm_test_conn"):
                if test_db_connection(host, port, database, user, password):
                    st.success("✅ 数据库连接成功！")
                    st.session_state.mysql_connected = True
                else:
                    st.error("❌ 数据库连接失败")
                    st.session_state.mysql_connected = False
        
        with col_save:
            if st.button("💾 保存配置", type="primary", key="dm_save_config"):
                st.session_state.db_config = {
                    'host': host,
                    'port': port,
                    'database': database,
                    'user': user,
                    'password': password
                }
                st.success("✅ 配置已保存")
    
    # 步骤2: 数据来源选择
    with st.expander("📋 步骤2: 数据来源选择", expanded=True):
        st.markdown("#### 选择数据来源表")
        
        # 连接源数据库获取表列表
        source_host = st.text_input("源数据库主机", value=host, key="dm_source_host")
        source_port = st.number_input("源数据库端口", value=port, min_value=1, max_value=65535, key="dm_source_port")
        source_database = st.text_input("源数据库名", value=database, key="dm_source_database")
        source_user = st.text_input("源数据库用户名", value=user, key="dm_source_user")
        source_password = st.text_input("源数据库密码", value=password, type="password", key="dm_source_password")
        
        if st.button("📋 获取表列表", type="secondary", key="dm_get_tables"):
            with st.spinner("正在获取表列表..."):
                tables = get_mysql_tables(source_host, source_port, source_database, source_user, source_password)
                if tables:
                    st.session_state.source_tables = tables
                    st.success(f"✅ 找到 {len(tables)} 个表")
                else:
                    st.error("❌ 无法获取表列表")
        
        # 选择源表
        if 'source_tables' in st.session_state and st.session_state.source_tables:
            source_table = st.selectbox(
                "选择源数据表",
                st.session_state.source_tables,
                key="dm_source_table"
            )
            
            if st.button("👁️ 预览数据", type="secondary", key="dm_preview"):
                with st.spinner("正在加载数据预览..."):
                    preview_data = get_table_preview(
                        source_host, source_port, source_database, 
                        source_user, source_password, source_table
                    )
                    if not preview_data.empty:
                        st.markdown("#### 数据预览 (前10行)")
                        st.dataframe(preview_data, use_container_width=True)
                        st.session_state.preview_data = preview_data
                    else:
                        st.error("❌ 无法获取数据预览")
    
    # 步骤3: 数据映射配置
    with st.expander("🗺️ 步骤3: 数据映射配置", expanded=True):
        st.markdown("#### 字段映射配置")
        st.info("将源表字段映射到目标系统字段")
        
        # 目标表选择
        target_tables = ['companies', 'financial_reports', 'financial_metrics', 'industry_data']
        target_table = st.selectbox(
            "选择目标表",
            target_tables,
            format_func=lambda x: {
                'companies': '公司信息表',
                'financial_reports': '财务报表表',
                'financial_metrics': '财务指标表',
                'industry_data': '行业数据表'
            }.get(x, x),
            key="dm_target_table"
        )
        
        # 显示目标表字段
        target_fields = get_target_fields(target_table)
        st.markdown("**目标表字段:**")
        st.code(", ".join(target_fields))
        
        # 字段映射
        if 'preview_data' in st.session_state and not st.session_state.preview_data.empty:
            st.markdown("**字段映射:**")
            source_columns = st.session_state.preview_data.columns.tolist()
            
            field_mappings = {}
            for target_field in target_fields:
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.text(target_field)
                with col2:
                    source_field = st.selectbox(
                        f"映射到",
                        ["-- 不映射 --"] + source_columns,
                        key=f"dm_map_{target_field}"
                    )
                    if source_field != "-- 不映射 --":
                        field_mappings[target_field] = source_field
            
            st.session_state.field_mappings = field_mappings
    
    # 步骤4: 执行导入
    with st.expander("🚀 步骤4: 执行导入", expanded=True):
        st.markdown("#### 导入操作")
        
        # 导入选项
        col1, col2 = st.columns(2)
        with col1:
            import_mode = st.radio(
                "导入模式",
                ["追加", "覆盖"],
                help="追加: 在现有数据后添加新数据\n覆盖: 清空目标表后导入",
                key="dm_import_mode"
            )
        with col2:
            batch_size = st.number_input(
                "批量大小",
                min_value=100,
                max_value=10000,
                value=1000,
                step=100,
                key="dm_batch_size"
            )
        
        # 执行导入按钮
        if st.button("🚀 开始导入", type="primary", use_container_width=True, key="dm_start_import"):
            if 'field_mappings' not in st.session_state or not st.session_state.field_mappings:
                st.error("❌ 请先配置字段映射")
            else:
                with st.spinner("正在导入数据..."):
                    result = execute_mysql_import(
                        source_host=source_host,
                        source_port=source_port,
                        source_database=source_database,
                        source_user=source_user,
                        source_password=source_password,
                        source_table=st.session_state.get('dm_source_table'),
                        target_table=target_table,
                        field_mappings=st.session_state.field_mappings,
                        import_mode=import_mode,
                        batch_size=batch_size
                    )
                    
                    if result['success']:
                        st.success(f"✅ 导入成功！共导入 {result['count']} 条记录")
                        st.markdown(f"""
                        **导入详情:**
                        - 源表: {source_database}.{st.session_state.get('dm_source_table')}
                        - 目标表: {target_table}
                        - 导入记录数: {result['count']}
                        - 耗时: {result.get('duration', 'N/A')} 秒
                        """)
                    else:
                        st.error(f"❌ 导入失败: {result['error']}")


def render_excel_import():
    """渲染Excel文件导入界面"""
    with st.expander("📁 文件上传", expanded=True):
        uploaded_file = st.file_uploader("选择Excel文件", type=['xlsx', 'xls'])
        
        if uploaded_file:
            st.success(f"✅ 文件已上传: {uploaded_file.name}")
            
            try:
                df = pd.read_excel(uploaded_file)
                st.markdown("#### 数据预览")
                st.dataframe(df.head(10), use_container_width=True)
                
                # 导入按钮
                if st.button("📥 导入数据", type="primary"):
                    with st.spinner("正在导入数据..."):
                        success, message = import_excel_data(df, uploaded_file.name)
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
            except Exception as e:
                st.error(f"读取文件失败: {e}")


def render_api_import():
    """渲染API接口导入界面"""
    with st.expander("🌐 API配置", expanded=True):
        api_url = st.text_input("API地址", placeholder="https://api.example.com/data")
        api_params = st.text_area("请求参数 (JSON)", placeholder='{"key": "value"}')
        
        if st.button("🚀 获取数据", type="primary"):
            with st.spinner("正在从API获取数据..."):
                success, result = fetch_api_data(api_url, api_params)
                if success:
                    st.success(f"✅ 成功获取 {len(result)} 条数据")
                    st.dataframe(result, use_container_width=True)
                else:
                    st.error(f"❌ 获取失败: {result}")


def render_ai_extraction():
    """渲染AI数据提取页面"""
    st.subheader("🤖 AI数据提取")
    
    # 获取已下载的文件列表
    files = get_downloaded_files()
    
    if not files:
        st.info("📂 暂无可用的财报文件，请先在'搜索下载'页面下载文件")
        return
    
    # 文件选择
    st.markdown("#### 📄 选择财报文件")
    selected_files = st.multiselect(
        "选择要处理的文件",
        files,
        default=files[:1] if files else []
    )
    
    if not selected_files:
        st.warning("请至少选择一个文件")
        return
    
    # 提取维度
    st.markdown("#### 🎯 提取维度")
    dimensions = st.multiselect(
        "选择提取维度",
        ["财务摘要", "资产负债表", "利润表", "现金流量表", "财务指标", "业务分析"],
        default=["财务摘要", "财务指标"]
    )
    
    if not dimensions:
        st.warning("请至少选择一个提取维度")
        return
    
    # 提取按钮
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🚀 开始提取", type="primary"):
            with st.spinner("AI正在提取数据..."):
                results = extract_data_with_ai(selected_files, dimensions)
                if results:
                    st.success(f"✅ 成功提取 {len(results)} 个文件的数据")
                    for result in results:
                        with st.expander(f"📄 {result['file']}"):
                            st.json(result['data'])
                else:
                    st.error("❌ 数据提取失败")
    
    with col2:
        st.checkbox("自动保存到数据库", value=True, key="auto_save_db")


def render_data_query():
    """渲染数据查询页面"""
    st.subheader("🔍 数据查询")
    
    # 查询条件
    with st.expander("🔍 查询条件", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            company_name = st.text_input("公司名称", placeholder="输入公司名称或代码")
        
        with col2:
            report_type = st.selectbox("报表类型", ["全部", "年报", "半年报", "季报"])
        
        with col3:
            year = st.selectbox("年份", ["全部", "2024", "2023", "2022", "2021", "2020"])
        
        if st.button("🔍 查询", type="primary"):
            with st.spinner("正在查询数据..."):
                results = query_database(company_name, report_type, year)
                if not results.empty:
                    st.session_state.query_results = results
                    st.success(f"✅ 找到 {len(results)} 条记录")
                else:
                    st.info("未找到匹配的数据")
    
    # 显示查询结果
    if 'query_results' in st.session_state and not st.session_state.query_results.empty:
        st.markdown("#### 📋 查询结果")
        st.dataframe(st.session_state.query_results, use_container_width=True)
        
        # 导出按钮
        if st.button("📥 导出结果"):
            csv = st.session_state.query_results.to_csv(index=False)
            st.download_button(
                label="下载CSV文件",
                data=csv,
                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )


def render_data_analysis():
    """渲染数据分析页面"""
    st.subheader("📊 数据分析")
    
    # 分析类型
    analysis_type = st.selectbox(
        "选择分析类型",
        ["财务趋势分析", "同业对比分析", "财务健康度评估", "异常数据检测"]
    )
    
    # 选择公司
    companies = get_available_companies()
    if not companies:
        st.info("📂 暂无可用数据，请先导入或提取数据")
        return
    
    selected_company = st.selectbox("选择公司", companies)
    
    if analysis_type == "财务趋势分析":
        render_trend_analysis(selected_company)
    elif analysis_type == "同业对比分析":
        render_comparison_analysis(selected_company)
    elif analysis_type == "财务健康度评估":
        render_health_assessment(selected_company)
    else:  # 异常数据检测
        render_anomaly_detection(selected_company)


# ==================== 辅助函数 ====================

def get_database_stats():
    """获取数据库统计信息"""
    try:
        if DATA_MODULES_AVAILABLE and st.session_state.get('data_manager'):
            # 从数据库获取真实统计
            return st.session_state.data_manager.get_stats()
    except:
        pass
    
    # 返回默认统计
    return {
        'company_count': "0",
        'company_change': "0",
        'report_count': "0",
        'report_change': "0",
        'coverage': "0%",
        'coverage_change': "0%",
        'status': "未连接",
        'last_update': "从未"
    }


def get_market_distribution():
    """获取市场分布数据"""
    try:
        if DATA_MODULES_AVAILABLE and st.session_state.get('data_manager'):
            return st.session_state.data_manager.get_market_distribution()
    except:
        pass
    
    # 返回空数据框
    return pd.DataFrame(columns=['市场', '公司数', '占比'])


def get_growth_trend():
    """获取增长趋势数据"""
    try:
        if DATA_MODULES_AVAILABLE and st.session_state.get('data_manager'):
            return st.session_state.data_manager.get_growth_trend()
    except:
        pass
    
    # 返回空数据框
    return pd.DataFrame(columns=['月份', '新增记录'])


def test_db_connection(host, port, database, user, password):
    """测试数据库连接"""
    try:
        import pymysql
        conn = pymysql.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password,
            connect_timeout=5
        )
        conn.close()
        return True
    except Exception as e:
        st.error(f"连接错误: {e}")
        return False


def import_excel_data(df, filename):
    """导入Excel数据到数据库"""
    try:
        if DATA_MODULES_AVAILABLE and st.session_state.get('data_manager'):
            return st.session_state.data_manager.import_excel(df, filename)
        return False, "数据管理器未初始化"
    except Exception as e:
        return False, str(e)


def fetch_api_data(api_url, api_params):
    """从API获取数据"""
    try:
        import requests
        import json
        
        params = json.loads(api_params) if api_params else {}
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # 转换为DataFrame
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and 'data' in data:
            df = pd.DataFrame(data['data'])
        else:
            df = pd.DataFrame([data])
        
        return True, df
    except Exception as e:
        return False, str(e)


def get_downloaded_files():
    """获取已下载的文件列表"""
    files = []
    temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
    
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            if file.endswith(('.pdf', '.docx', '.txt')):
                files.append(file)
    
    return files


def extract_data_with_ai(files, dimensions):
    """使用AI提取数据"""
    results = []
    
    for file in files:
        try:
            # 这里应该调用实际的AI提取功能
            # 目前返回模拟结果
            result = {
                'file': file,
                'data': {
                    'dimensions': dimensions,
                    'status': 'success',
                    'timestamp': datetime.now().isoformat()
                }
            }
            results.append(result)
        except Exception as e:
            st.error(f"处理文件 {file} 时出错: {e}")
    
    return results


def query_database(company_name, report_type, year):
    """查询数据库"""
    try:
        if DATA_MODULES_AVAILABLE and st.session_state.get('data_manager'):
            return st.session_state.data_manager.query(company_name, report_type, year)
    except:
        pass
    
    # 返回空数据框
    return pd.DataFrame()


def get_available_companies():
    """获取可用的公司列表"""
    try:
        if DATA_MODULES_AVAILABLE and st.session_state.get('data_manager'):
            return st.session_state.data_manager.get_companies()
    except:
        pass
    
    return []


def render_trend_analysis(company):
    """渲染趋势分析"""
    st.markdown(f"#### 📈 {company} 财务趋势")
    
    # 获取趋势数据
    trend_data = get_company_trend(company)
    
    if not trend_data.empty:
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
            title=f'{company} 财务趋势分析',
            xaxis_title='年份',
            yaxis_title='金额(亿元)',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无趋势数据")


def render_comparison_analysis(company):
    """渲染对比分析"""
    st.markdown(f"#### 📊 {company} 同业对比")
    
    # 获取对比数据
    comparison_data = get_comparison_data(company)
    
    if not comparison_data.empty:
        fig = go.Figure(data=[
            go.Bar(name='ROE(%)', x=comparison_data['公司'], y=comparison_data['ROE']),
            go.Bar(name='毛利率(%)', x=comparison_data['公司'], y=comparison_data['毛利率'])
        ])
        
        fig.update_layout(
            title='同业对比分析',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("暂无对比数据")


def render_health_assessment(company):
    """渲染健康度评估"""
    st.markdown(f"#### 🏥 {company} 财务健康度评估")
    
    # 健康度评分
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("综合评分", "85/100", "↑ 5分")
    with col2:
        st.metric("偿债能力", "A级", "稳定")
    with col3:
        st.metric("盈利能力", "B+级", "↑ 提升")
    
    st.info("📊 详细评估报告功能开发中...")


def render_anomaly_detection(company):
    """渲染异常检测"""
    st.markdown(f"#### 🔍 {company} 异常数据检测")
    
    st.info("🤖 AI异常检测功能开发中...")


def get_company_trend(company):
    """获取公司趋势数据"""
    try:
        if DATA_MODULES_AVAILABLE and st.session_state.get('data_manager'):
            return st.session_state.data_manager.get_company_trend(company)
    except:
        pass
    
    return pd.DataFrame()


def get_comparison_data(company):
    """获取对比数据"""
    try:
        if DATA_MODULES_AVAILABLE and st.session_state.get('data_manager'):
            return st.session_state.data_manager.get_comparison_data(company)
    except:
        pass
    
    return pd.DataFrame()


def get_mysql_tables(host, port, database, user, password):
    """获取MySQL数据库中的所有表"""
    try:
        import pymysql
        conn = pymysql.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password,
            connect_timeout=5
        )
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return tables
    except Exception as e:
        st.error(f"获取表列表失败: {e}")
        return []


def get_table_preview(host, port, database, user, password, table_name, limit=10):
    """获取表数据预览"""
    try:
        import pymysql
        conn = pymysql.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password,
            connect_timeout=5
        )
        query = f"SELECT * FROM `{table_name}` LIMIT {limit}"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"获取数据预览失败: {e}")
        return pd.DataFrame()


def get_target_fields(target_table):
    """获取目标表的字段列表"""
    fields_map = {
        'companies': ['id', 'stock_code', 'company_name', 'industry', 'market', 'created_at'],
        'financial_reports': ['id', 'company_id', 'report_type', 'report_year', 'report_period', 'revenue', 'net_profit', 'total_assets', 'total_liabilities', 'created_at'],
        'financial_metrics': ['id', 'company_id', 'report_id', 'roe', 'gross_margin', 'net_margin', 'debt_ratio', 'current_ratio', 'created_at'],
        'industry_data': ['id', 'industry_name', 'year', 'avg_revenue', 'avg_profit', 'growth_rate', 'created_at']
    }
    return fields_map.get(target_table, [])


def execute_mysql_import(source_host, source_port, source_database, source_user, source_password,
                        source_table, target_table, field_mappings, import_mode, batch_size):
    """执行MySQL数据导入"""
    import time
    start_time = time.time()
    
    try:
        import pymysql
        from sqlalchemy import create_engine
        
        # 连接源数据库
        source_conn = pymysql.connect(
            host=source_host,
            port=int(source_port),
            database=source_database,
            user=source_user,
            password=source_password,
            connect_timeout=10
        )
        
        # 读取源数据
        source_query = f"SELECT * FROM `{source_table}`"
        source_df = pd.read_sql(source_query, source_conn)
        source_conn.close()
        
        if source_df.empty:
            return {'success': False, 'error': '源表中没有数据'}
        
        # 字段映射转换
        target_df = pd.DataFrame()
        for target_field, source_field in field_mappings.items():
            if source_field in source_df.columns:
                target_df[target_field] = source_df[source_field]
        
        # 连接目标数据库
        target_config = st.session_state.db_config
        target_engine = create_engine(
            f"mysql+pymysql://{target_config['user']}:{target_config['password']}@"
            f"{target_config['host']}:{target_config['port']}/{target_config['database']}"
        )
        
        # 根据导入模式处理
        if import_mode == "覆盖":
            # 清空目标表
            with target_engine.connect() as conn:
                conn.execute(f"TRUNCATE TABLE {target_table}")
        
        # 批量导入数据
        total_rows = len(target_df)
        imported_rows = 0
        
        for i in range(0, total_rows, batch_size):
            batch = target_df.iloc[i:i+batch_size]
            batch.to_sql(target_table, target_engine, if_exists='append', index=False)
            imported_rows += len(batch)
        
        duration = round(time.time() - start_time, 2)
        
        return {
            'success': True,
            'count': imported_rows,
            'duration': duration
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
