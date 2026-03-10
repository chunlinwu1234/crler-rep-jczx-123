"""
CIMS - 竞争情报监控系统
Streamlit网页界面主文件
提供友好的图形化操作界面
"""
import os
import sys
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from stock_downloader import StockDownloader
from ai_analyzer import AIAnalyzer, ModelConfig, PromptConfig
from database import DatabaseManager, DataRepository, DBConfig
from data_extractor import DataExtractor, DataQueryHelper, create_extractor_with_config
from data_module_ui import render_data_module
import threading
import json
import zipfile
import io


# 设置页面配置
st.set_page_config(
    page_title="CIMS - 竞争情报监控系统",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)


def init_session_state():
    """初始化会话状态"""
    if 'downloader' not in st.session_state:
        st.session_state.downloader = None
    if 'stock_info' not in st.session_state:
        st.session_state.stock_info = None
    if 'announcements' not in st.session_state:
        st.session_state.announcements = []
    if 'downloading' not in st.session_state:
        st.session_state.downloading = False
    if 'download_progress' not in st.session_state:
        st.session_state.download_progress = 0
    if 'analyzer' not in st.session_state:
        st.session_state.analyzer = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    if 'model_config' not in st.session_state:
        st.session_state.model_config = ModelConfig()
    if 'prompt_config' not in st.session_state:
        st.session_state.prompt_config = PromptConfig()
    if 'custom_folder_path' not in st.session_state:
        st.session_state.custom_folder_path = ""
    # 下载模块配置
    if 'download_config' not in st.session_state:
        st.session_state.download_config = {
            'download_dir': os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads"),
            'min_delay': 5,
            'max_delay': 10
        }
    # 数据库配置
    if 'db_config' not in st.session_state:
        st.session_state.db_config = {
            'host': 'localhost',
            'port': 3306,
            'database': 'cims_db',
            'user': 'root',
            'password': 'root'
        }
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = None
    if 'data_extractor' not in st.session_state:
        st.session_state.data_extractor = None
    if 'data_query' not in st.session_state:
        st.session_state.data_query = None


def render_download_config():
    """渲染下载配置界面"""
    with st.expander("⚙️ 下载设置", expanded=True):
        st.subheader("下载配置")
        
        # 下载目录设置
        download_dir = st.text_input(
            "下载目录",
            value=st.session_state.download_config['download_dir'],
            help="公告PDF保存目录"
        )
        
        # 请求间隔设置
        col1, col2 = st.columns(2)
        with col1:
            min_delay = st.number_input(
                "最小间隔(秒)",
                min_value=1,
                max_value=60,
                value=st.session_state.download_config['min_delay'],
                help="请求之间的最小延迟"
            )
        with col2:
            max_delay = st.number_input(
                "最大间隔(秒)",
                min_value=1,
                max_value=60,
                value=st.session_state.download_config['max_delay'],
                help="请求之间的最大延迟"
            )
        
        # 保存配置
        if st.button("💾 保存下载配置", type="primary"):
            st.session_state.download_config = {
                'download_dir': download_dir,
                'min_delay': min_delay,
                'max_delay': max_delay
            }
            # 重新初始化下载器
            st.session_state.downloader = StockDownloader(
                download_dir=download_dir,
                min_delay=min_delay,
                max_delay=max_delay
            )
            st.success("✅ 下载配置已保存！")
        
        st.markdown("---")
        st.info("""
        **说明**：
        - 下载目录：指定公告PDF文件的保存位置
        - 请求间隔：设置下载请求之间的随机延迟，避免被封禁
        """)


def render_model_config():
    """渲染模型配置界面"""
    with st.expander("⚙️ AI模型配置", expanded=st.session_state.analyzer is None):
        st.subheader("AI模型配置")
        
        config = st.session_state.model_config
        
        # 模型提供商选择
        provider = st.selectbox(
            "模型提供商",
            ["Ollama (本地)", "DeepSeek (云服务)", "通义千问 (云服务)"],
            index=0 if config.provider == "ollama" else 
                  1 if config.provider == "deepseek" else 2,
            help="选择AI模型提供商"
        )
        
        # 根据提供商显示不同配置
        if provider == "Ollama (本地)":
            st.session_state.model_config.provider = "ollama"
            
            # Ollama主机配置
            col1, col2 = st.columns(2)
            with col1:
                ollama_host = st.text_input(
                    "Ollama主机地址",
                    value=config.ollama_host or "http://localhost:11434",
                    help="Ollama服务地址，默认本地11434端口"
                )
            with col2:
                # 获取可用模型列表
                try:
                    import ollama
                    models = ollama.list()
                    available_models = [m['model'] for m in models.get('models', [])]
                    if not available_models:
                        available_models = ["qwen2.5:7b", "qwen3:8b", "deepseek-r1:7b"]
                except:
                    available_models = ["qwen2.5:7b", "qwen3:8b", "deepseek-r1:7b"]
                
                ollama_model = st.selectbox(
                    "选择模型",
                    available_models,
                    index=available_models.index(config.ollama_model) if config.ollama_model in available_models else 0,
                    help="选择本地Ollama模型"
                )
            
            st.session_state.model_config.ollama_host = ollama_host
            st.session_state.model_config.ollama_model = ollama_model
            
            # 测试连接
            if st.button("🔄 测试Ollama连接", type="secondary"):
                with st.spinner("正在测试连接..."):
                    try:
                        import ollama
                        os.environ['OLLAMA_HOST'] = ollama_host
                        models = ollama.list()
                        available = [m['model'] for m in models.get('models', [])]
                        if ollama_model in available:
                            st.success(f"✅ 连接成功！模型 '{ollama_model}' 可用")
                        else:
                            st.warning(f"⚠️ 连接成功，但模型 '{ollama_model}' 未找到")
                            st.info(f"可用模型: {', '.join(available) if available else '无'}")
                    except Exception as e:
                        st.error(f"❌ 连接失败: {e}")
                        st.info("请确保Ollama服务已启动: ollama serve")
        
        elif provider == "DeepSeek (云服务)":
            st.session_state.model_config.provider = "deepseek"
            
            col1, col2 = st.columns(2)
            with col1:
                deepseek_api_key = st.text_input(
                    "API Key",
                    value=config.deepseek_api_key or "",
                    type="password",
                    help="DeepSeek API密钥"
                )
            with col2:
                deepseek_model = st.selectbox(
                    "模型",
                    ["deepseek-chat", "deepseek-reasoner"],
                    index=0 if config.deepseek_model == "deepseek-chat" else 1,
                    help="选择DeepSeek模型"
                )
            
            st.session_state.model_config.deepseek_api_key = deepseek_api_key
            st.session_state.model_config.deepseek_model = deepseek_model
            
            if not deepseek_api_key:
                st.warning("⚠️ 请输入DeepSeek API Key")
        
        elif provider == "通义千问 (云服务)":
            st.session_state.model_config.provider = "qwen"
            
            col1, col2 = st.columns(2)
            with col1:
                qwen_api_key = st.text_input(
                    "API Key",
                    value=config.qwen_api_key or "",
                    type="password",
                    help="通义千问 API密钥"
                )
            with col2:
                qwen_model = st.selectbox(
                    "模型",
                    ["qwen-turbo", "qwen-plus", "qwen-max"],
                    index=["qwen-turbo", "qwen-plus", "qwen-max"].index(config.qwen_model) if config.qwen_model in ["qwen-turbo", "qwen-plus", "qwen-max"] else 0,
                    help="选择通义千问模型"
                )
            
            st.session_state.model_config.qwen_api_key = qwen_api_key
            st.session_state.model_config.qwen_model = qwen_model
            
            if not qwen_api_key:
                st.warning("⚠️ 请输入通义千问 API Key")
        
        # 通用参数配置
        st.markdown("---")
        st.write("**模型参数**")
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=config.temperature,
                step=0.1,
                help="创造性程度，越低越保守"
            )
        with col2:
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=512,
                max_value=8192,
                value=config.max_tokens,
                step=512,
                help="最大输出token数"
            )
        
        st.session_state.model_config.temperature = temperature
        st.session_state.model_config.max_tokens = max_tokens
        
        # 保存配置并初始化分析器
        if st.button("💾 保存配置并初始化", type="primary"):
            try:
                st.session_state.analyzer = AIAnalyzer(
                    model_config=st.session_state.model_config,
                    prompt_config=st.session_state.prompt_config
                )
                st.success("✅ 配置已保存，分析器初始化成功！")
            except Exception as e:
                st.error(f"❌ 初始化失败: {e}")


def extract_company_name(file_name):
    """从文件名中提取公司名称

    Args:
        file_name: 文件名

    Returns:
        提取的公司名称，如果无法提取则返回None
    """
    import re

    # 移除文件扩展名
    name_without_ext = os.path.splitext(file_name)[0]

    # 尝试匹配常见的文件名格式
    # 格式1: 公司名称_股票代码_其他信息
    # 格式2: 公司名称：报告名称
    # 格式3: 年份_公司名称_其他

    patterns = [
        r'^([^_:：]+)[_:：]',  # 开头到公司名结束（遇到_或:或：）
        r'[_/]([^_/]+)_[^/]+$',  # 目录后的公司名
        r'^(\d{4}[-_]?\d{2}[-_]?\d{2})?[_-]?([^_-]+)',  # 日期后的公司名
    ]

    for pattern in patterns:
        match = re.search(pattern, name_without_ext)
        if match:
            # 获取最后一个捕获组（最可能是公司名）
            company = match.group(match.lastindex) if match.lastindex else match.group(1)
            # 清理公司名
            company = company.strip()
            # 移除常见的后缀
            suffixes = ['股份有限公司', '有限公司', '集团', '公司', '：', ':']
            for suffix in suffixes:
                if company.endswith(suffix):
                    company = company[:-len(suffix)]
                    break
            if company and len(company) >= 2:
                return company

    return None


def render_chart(chart_data):
    """渲染图表

    Args:
        chart_data: 图表数据字典，包含chart_type, chart_title, labels, datasets
    """
    import plotly.graph_objects as go
    import plotly.express as px

    chart_type = chart_data.get('chart_type', 'bar')
    chart_title = chart_data.get('chart_title', '图表')
    labels = chart_data.get('labels', [])
    datasets = chart_data.get('datasets', [])

    if not labels or not datasets:
        st.warning("图表数据不完整")
        return

    fig = None

    if chart_type == 'bar':
        # 柱状图
        fig = go.Figure()
        for dataset in datasets:
            fig.add_trace(go.Bar(
                name=dataset.get('label', '数据'),
                x=labels,
                y=dataset.get('data', [])
            ))
        fig.update_layout(
            title=chart_title,
            xaxis_title='类别',
            yaxis_title='数值',
            barmode='group'
        )

    elif chart_type == 'line':
        # 折线图
        fig = go.Figure()
        for dataset in datasets:
            fig.add_trace(go.Scatter(
                name=dataset.get('label', '数据'),
                x=labels,
                y=dataset.get('data', []),
                mode='lines+markers'
            ))
        fig.update_layout(
            title=chart_title,
            xaxis_title='时间/类别',
            yaxis_title='数值'
        )

    elif chart_type == 'pie':
        # 饼图
        if datasets:
            values = datasets[0].get('data', [])
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                title=chart_title
            )])

    elif chart_type == 'radar':
        # 雷达图
        fig = go.Figure()
        for dataset in datasets:
            fig.add_trace(go.Scatterpolar(
                r=dataset.get('data', []),
                theta=labels,
                fill='toself',
                name=dataset.get('label', '数据')
            ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True)),
            title=chart_title
        )

    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"不支持的图表类型: {chart_type}")


def render_file_browser():
    """渲染文件浏览器"""
    
    # 浏览方式选择
    browse_mode = st.radio(
        "浏览方式",
        ["从downloads目录选择", "自定义文件夹路径"],
        horizontal=True
    )
    
    selected_file_paths = []
    
    if browse_mode == "从downloads目录选择":
        # 显示downloads目录中的文件
        downloads_dir = st.session_state.download_config['download_dir']
        if os.path.exists(downloads_dir):
            companies = [d for d in os.listdir(downloads_dir) if os.path.isdir(os.path.join(downloads_dir, d))]
            if companies:
                selected_company = st.selectbox("选择公司", companies, key="company_select")
                company_dir = os.path.join(downloads_dir, selected_company)
                files = [f for f in os.listdir(company_dir) if f.endswith((".pdf", ".docx", ".txt"))]
                
                if files:
                    selected_files = st.multiselect("选择文件", files, key="file_select")
                    selected_file_paths = [os.path.join(company_dir, f) for f in selected_files]
                else:
                    st.info("该公司目录下没有可分析的文件")
            else:
                st.info("downloads目录下没有公司文件夹")
        else:
            st.info("downloads目录不存在")
    
    else:  # 自定义文件夹路径
        # 由于Streamlit不支持原生文件夹选择器，使用文本输入
        custom_path = st.text_input(
            "文件夹路径",
            value=st.session_state.custom_folder_path,
            placeholder="例如: D:\\Documents\\Reports",
            help="输入包含文档的文件夹完整路径"
        )
        st.session_state.custom_folder_path = custom_path
        
        if custom_path and os.path.exists(custom_path):
            if os.path.isdir(custom_path):
                # 获取目录中的所有文件
                all_files = []
                for root, dirs, files in os.walk(custom_path):
                    for file in files:
                        if file.endswith((".pdf", ".docx", ".txt")):
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, custom_path)
                            all_files.append((rel_path, full_path))
                
                if all_files:
                    file_options = [f[0] for f in all_files]
                    selected_files = st.multiselect(
                        f"选择文件 (共{len(all_files)}个)",
                        file_options,
                        key="custom_file_select"
                    )
                    selected_file_paths = [f[1] for f in all_files if f[0] in selected_files]
                else:
                    st.info("该目录下没有可分析的PDF、Word或TXT文件")
            else:
                st.error("路径不是有效的文件夹")
        elif custom_path:
            st.error("路径不存在")
    
    return selected_file_paths


def download_results(results, company_name):
    """提供分析结果下载功能"""
    if not results:
        return
    
    st.markdown("---")
    st.subheader("💾 下载分析结果")
    
    # 创建ZIP文件
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, result in enumerate(results):
            if "error" not in result:
                # 生成文件名
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{company_name}_{result['dimension']}_{result['depth']}_{i+1}_{timestamp}.md"
                
                # 构建Markdown内容
                content = f"""# {result['company']} - {result['dimension']}分析报告

**分析深度**: {result['depth']}  
**分析文件**: {result['file']}  
**分析时间**: {result['timestamp']}

---

{result['result']}
"""
                zip_file.writestr(filename, content)
    
    zip_buffer.seek(0)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📦 下载全部结果 (ZIP)",
            data=zip_buffer.getvalue(),
            file_name=f"{company_name}_分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            use_container_width=True
        )
    
    with col2:
        # 下载JSON格式
        json_data = json.dumps(results, ensure_ascii=False, indent=2)
        st.download_button(
            label="📄 下载JSON格式",
            data=json_data,
            file_name=f"{company_name}_分析报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )


def main():
    """主函数"""
    init_session_state()
    
    st.title("🔍 CIMS - 竞争情报监控系统")
    st.markdown("Competitive Intelligence Monitoring System - 智能竞争情报收集与分析平台")
    
    # 侧边栏 - 仅保留关于信息
    with st.sidebar:
        st.header("ℹ️ 关于 CIMS")
        st.markdown("""
        **CIMS** (Competitive Intelligence Monitoring System)
        
        一个智能化的竞争情报收集与分析平台：
        
        📥 **搜索下载**
        - 从巨潮资讯网下载股票公告
        - 支持股票名称或代码搜索
        - 多种公告类型选择
        - 自动随机延迟避免封禁
        
        🤖 **AI分析**
        - 八大维度竞争情报分析
        - 支持本地Ollama和云服务
        - 多文件批量分析
        - 结构化报告输出
        
        📊 **数据管理**
        - MySQL/Excel数据导入
        - AI自动提取财务数据
        - 多市场数据支持(A股/港股/美股等)
        - 数据查询与可视化分析
        
        📈 **分析维度**
        - 战略分析、商业模式
        - 资源能力、财务分析
        - 前景分析、发展历程
        - 股权/子公司、企业文化
        """)
        
        st.markdown("---")
        st.caption("© 2024 CIMS - 竞争情报监控系统")
    
    # 主内容区
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 搜索下载", "📜 历史记录", "⏰ 定时任务", "🤖 AI分析", "📊 数据管理"])
    
    with tab1:
        st.header("🔍 搜索下载")
        st.markdown("从巨潮资讯网搜索并下载股票公告PDF文件")
        
        # 下载设置（仅在此模块显示）
        render_download_config()
        
        st.markdown("---")
        
        # 初始化下载器（如果未初始化）
        if st.session_state.downloader is None:
            st.session_state.downloader = StockDownloader(
                download_dir=st.session_state.download_config['download_dir'],
                min_delay=st.session_state.download_config['min_delay'],
                max_delay=st.session_state.download_config['max_delay']
            )
        
        # 股票搜索
        st.subheader("🔍 搜索股票")
        stock_query = st.text_input(
            "输入股票名称或代码",
            placeholder="例如：普洛药业 或 000739",
            help="支持股票名称或代码搜索"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            search_btn = st.button("搜索", type="primary", use_container_width=True)
        
        if search_btn and stock_query:
            with st.spinner("正在搜索..."):
                stock_info = st.session_state.downloader.search_stock(stock_query)
                if stock_info:
                    st.session_state.stock_info = stock_info
                    st.success(f"找到股票: {stock_info.name} ({stock_info.code})")
                else:
                    st.error("未找到该股票")
        
        # 显示股票信息和公告列表
        if st.session_state.stock_info:
            st.markdown("---")
            stock_info = st.session_state.stock_info
            
            # 股票信息卡片
            st.subheader("📊 股票信息")
            col1, col2, col3 = st.columns(3)
            col1.metric("股票名称", stock_info.name)
            col2.metric("股票代码", stock_info.code)
            exchange_name = "深交所" if stock_info.plate == "szse" else "上交所" if stock_info.plate == "sse" else stock_info.plate
            col3.metric("交易所", exchange_name)
            
            # 公告类型选择
            st.markdown("---")
            st.subheader("📋 公告列表")
            
            # 时间范围选择
            st.markdown("**时间范围**")
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                start_date = st.date_input(
                    "开始日期（可选）",
                    value=None,
                    help="选择公告查询的起始日期，不选则获取所有历史公告"
                )
            with date_col2:
                end_date = st.date_input(
                    "结束日期",
                    value=datetime.now(),
                    help="选择公告查询的结束日期"
                )
            
            # 验证日期范围
            if start_date and end_date and start_date > end_date:
                st.error("开始日期不能晚于结束日期")
            else:
                announcement_type = st.selectbox(
                    "公告类型",
                    ["latest", "periodic"],
                    format_func=lambda x: {
                        "latest": "最新公告",
                        "periodic": "定期报告"
                }.get(x, x)
            )
            
            # 获取公告列表
            if st.button("获取公告列表", type="primary"):
                with st.spinner("正在获取公告列表..."):
                    # 格式化日期为字符串
                    start_date_str = start_date.strftime("%Y-%m-%d") if start_date else None
                    end_date_str = end_date.strftime("%Y-%m-%d") if end_date else None

                    announcements = st.session_state.downloader.get_announcements(
                        stock_info,
                        announcement_type,
                        start_date=start_date_str,
                        end_date=end_date_str
                    )
                    st.session_state.announcements = announcements
                    
                    if announcements:
                        st.success(f"获取到 {len(announcements)} 条公告")
                    else:
                        st.warning("未获取到公告")
            
            # 显示公告列表
            if st.session_state.announcements:
                ann_data = []
                for ann in st.session_state.announcements:
                    ann_data.append({
                        "公告ID": ann.announcement_id,
                        "标题": ann.title,
                        "时间": ann.announcement_time,
                        "类型": ann.announcement_type,
                        "PDF链接": ann.pdf_url
                    })
                
                df = pd.DataFrame(ann_data)
                st.dataframe(df, use_container_width=True)
                
                # 选择要下载的公告
                st.markdown("---")
                selected_indices = st.multiselect(
                    "选择要下载的公告（索引）",
                    options=range(len(st.session_state.announcements)),
                    default=range(len(st.session_state.announcements))
                )
                
                # 下载按钮
                if st.button("开始下载", type="primary"):
                    if selected_indices:
                        import time
                        start_time = time.time()
                        
                        st.session_state.downloading = True
                        selected_anns = [st.session_state.announcements[i] for i in selected_indices]
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        success_count = 0
                        failed_count = 0
                        files = []
                        total_size = 0
                        
                        for i, ann in enumerate(selected_anns):
                            status_text.text(f"正在下载 {i+1}/{len(selected_anns)}: {ann.title}")
                            filepath = st.session_state.downloader.download_pdf(ann, stock_info)
                            
                            if filepath:
                                success_count += 1
                                files.append(filepath)
                                # 计算文件大小
                                if os.path.exists(filepath):
                                    total_size += os.path.getsize(filepath)
                            else:
                                failed_count += 1
                            
                            progress_bar.progress((i + 1) / len(selected_anns))
                        
                        end_time = time.time()
                        elapsed_time = end_time - start_time
                        st.session_state.downloading = False
                        
                        # 显示下载结果统计
                        st.markdown("---")
                        st.subheader("📊 下载统计")
                        
                        # 创建统计卡片
                        col1, col2, col3, col4 = st.columns(4)
                        col1.metric("✅ 成功", success_count)
                        col2.metric("❌ 失败", failed_count)
                        col3.metric("⏱️ 耗时", f"{elapsed_time:.1f}秒")
                        
                        # 计算平均下载速度
                        if elapsed_time > 0:
                            avg_speed = len(selected_anns) / elapsed_time
                            col4.metric("🚀 速度", f"{avg_speed:.1f}个/秒")
                        
                        # 详细信息
                        st.markdown("---")
                        st.write("**详细统计：**")
                        detail_col1, detail_col2, detail_col3 = st.columns(3)
                        
                        with detail_col1:
                            st.write(f"📁 总文件数: {len(selected_anns)}")
                            st.write(f"📥 成功下载: {success_count}")
                            st.write(f"⚠️ 下载失败: {failed_count}")
                        
                        with detail_col2:
                            success_rate = (success_count / len(selected_anns) * 100) if len(selected_anns) > 0 else 0
                            st.write(f"📈 成功率: {success_rate:.1f}%")
                            st.write(f"⏱️ 总耗时: {elapsed_time:.2f}秒")
                            if success_count > 0:
                                avg_time = elapsed_time / success_count
                                st.write(f"⏲️ 平均耗时: {avg_time:.2f}秒/文件")
                        
                        with detail_col3:
                            # 文件大小格式化
                            if total_size > 1024 * 1024:
                                size_str = f"{total_size / (1024 * 1024):.2f} MB"
                            elif total_size > 1024:
                                size_str = f"{total_size / 1024:.2f} KB"
                            else:
                                size_str = f"{total_size} B"
                            st.write(f"💾 总大小: {size_str}")
                            if success_count > 0:
                                avg_size = total_size / success_count
                                if avg_size > 1024 * 1024:
                                    avg_size_str = f"{avg_size / (1024 * 1024):.2f} MB"
                                elif avg_size > 1024:
                                    avg_size_str = f"{avg_size / 1024:.2f} KB"
                                else:
                                    avg_size_str = f"{avg_size:.0f} B"
                                st.write(f"📄 平均大小: {avg_size_str}")
                        
                        if files:
                            st.success(f"📂 文件保存在: {os.path.dirname(files[0])}")
                    else:
                        st.warning("请先选择要下载的公告")
    
    with tab2:
        st.header("📜 历史记录")
        st.info("历史记录功能开发中...")
    
    with tab3:
        st.header("⏰ 定时任务")
        st.info("定时任务功能开发中...")
        
        # 简单的定时任务设置
        st.markdown("---")
        st.write("定时任务设置（开发中）")
        st.radio(
            "执行模式",
            ["人工执行", "定时执行"],
            index=0
        )
    
    with tab4:
        st.header("🤖 AI分析")
        st.markdown("使用AI模型对文档进行多维度竞争情报分析")

        # 定义可用的分析维度（提前定义供Prompt配置使用）
        available_dimensions = [
            "战略分析", "商业模式", "资源能力", "财务分析",
            "前景分析", "发展历程", "股权/子公司", "企业文化"
        ]

        # AI模型配置（仅在此模块显示）
        render_model_config()

        st.markdown("---")

        # 数据库配置
        with st.expander("🗄️ 数据库配置", expanded=False):
            st.subheader("MySQL数据库配置")
            st.info("配置数据存储数据库，用于保存提取的结构化数据")

            db_col1, db_col2 = st.columns(2)
            with db_col1:
                db_host = st.text_input("主机地址", value=st.session_state.db_config['host'])
                db_port = st.number_input("端口号", value=st.session_state.db_config['port'], min_value=1, max_value=65535)
                db_database = st.text_input("数据库名", value=st.session_state.db_config['database'])
            with db_col2:
                db_user = st.text_input("用户名", value=st.session_state.db_config['user'])
                db_password = st.text_input("密码", value=st.session_state.db_config['password'], type="password")

            db_cols = st.columns(3)
            with db_cols[0]:
                if st.button("💾 保存数据库配置", type="primary"):
                    st.session_state.db_config = {
                        'host': db_host,
                        'port': db_port,
                        'database': db_database,
                        'user': db_user,
                        'password': db_password
                    }
                    st.success("✅ 数据库配置已保存！")
            with db_cols[1]:
                if st.button("🔄 测试连接"):
                    try:
                        from database import DatabaseManager, DBConfig
                        config = DBConfig(
                            host=db_host,
                            port=db_port,
                            database=db_database,
                            user=db_user,
                            password=db_password
                        )
                        db_manager = DatabaseManager(config)
                        if db_manager.test_connection():
                            st.success("✅ 数据库连接成功！")
                        db_manager.close()
                    except Exception as e:
                        st.error(f"❌ 连接失败: {e}")
            with db_cols[2]:
                if st.button("🔧 初始化数据库"):
                    try:
                        from database import init_database_with_config
                        if init_database_with_config(db_host, db_port, db_database, db_user, db_password):
                            st.success("✅ 数据库初始化成功！")
                        else:
                            st.error("❌ 数据库初始化失败！")
                    except Exception as e:
                        st.error(f"❌ 初始化失败: {e}")

        st.markdown("---")

        # Prompt配置
        with st.expander("📝 Prompt配置", expanded=False):
            st.subheader("分析Prompt模板配置")
            st.info("您可以自定义分析Prompt模板，修改后将保存到本地配置文件")

            prompt_config = st.session_state.prompt_config

            # 选择要编辑的模板
            template_options = ["基础模板"] + available_dimensions
            selected_template = st.selectbox(
                "选择要编辑的模板",
                template_options,
                help="基础模板是分析的基础框架，各维度模板会在基础模板后追加"
            )

            # 获取模板名称
            template_name = "base" if selected_template == "基础模板" else selected_template

            # 显示当前模板内容
            current_template = prompt_config.get_template(template_name)
            edited_template = st.text_area(
                "模板内容",
                value=current_template,
                height=400,
                help="编辑Prompt模板内容。基础模板可用变量：{company_name}, {analysis_dimension}, {analysis_depth}, {content}"
            )

            # 操作按钮
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 保存模板", type="primary"):
                    prompt_config.set_template(template_name, edited_template)
                    if prompt_config.save_templates():
                        st.success(f"✅ {selected_template} 已保存！")
                    else:
                        st.error("❌ 保存失败")
            with col2:
                if st.button("🔄 重置当前模板"):
                    prompt_config.reset_template(template_name)
                    if prompt_config.save_templates():
                        st.success(f"✅ {selected_template} 已重置为默认！")
                        st.rerun()
                    else:
                        st.error("❌ 重置失败")
            with col3:
                if st.button("🔄 重置所有模板"):
                    prompt_config.reset_all_templates()
                    if prompt_config.save_templates():
                        st.success("✅ 所有模板已重置为默认！")
                        st.rerun()
                    else:
                        st.error("❌ 重置失败")

        st.markdown("---")

        # 检查分析器是否已初始化
        if st.session_state.analyzer is None:
            st.warning("⚠️ 请先配置AI模型并点击'保存配置并初始化'")
        else:
            # 分析维度选择（多选）
            st.markdown("**分析维度**（可多选）")
            
            # 使用columns布局使多选更紧凑
            cols = st.columns(4)
            selected_dimensions = []
            for i, dim in enumerate(available_dimensions):
                with cols[i % 4]:
                    if st.checkbox(dim, value=(dim == "战略分析"), key=f"dim_{dim}"):
                        selected_dimensions.append(dim)
            
            if not selected_dimensions:
                st.warning("请至少选择一个分析维度")
        
        # 分析深度选择
        analysis_depth = st.selectbox(
            "分析深度",
            ["浅层", "中层", "深层"],
            index=1,
            help="浅层：快速概览；中层：详细分析；深层：深度洞察"
        )
        
        # 文件选择区域（合并上传和选择）
        st.markdown("---")
        st.subheader("📁 选择分析文件")
        
        # 使用标签页组织文件来源
        file_tab1, file_tab2 = st.tabs(["📤 上传新文件", "📂 选择已有文件"])
        
        uploaded_files_paths = []
        selected_file_paths = []
        
        with file_tab1:
            uploaded_files = st.file_uploader(
                "上传文件（支持PDF、Word、TXT）",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                help="上传需要分析的文档"
            )
            if uploaded_files:
                temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
                os.makedirs(temp_dir, exist_ok=True)
                for uploaded_file in uploaded_files:
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    uploaded_files_paths.append(file_path)
                st.success(f"✅ 已上传 {len(uploaded_files_paths)} 个文件")
        
        with file_tab2:
            selected_file_paths = render_file_browser()
        
        # 合并所有文件
        all_files = uploaded_files_paths + selected_file_paths
        
        # 公司名称输入（自动识别 + 手动修改）
        st.markdown("---")
        st.subheader("🏢 公司名称")
        
        # 自动识别公司名称
        auto_detected_company = None
        if all_files:
            # 尝试从第一个文件名提取公司名
            first_file = os.path.basename(all_files[0])
            auto_detected_company = extract_company_name(first_file)
            if auto_detected_company:
                st.info(f"🤖 已从文件名识别到公司名称：'{auto_detected_company}'，您可以根据需要修改")
        
        # 公司名称输入框（使用自动识别的值作为默认值）
        company_name = st.text_input(
            "公司名称（用于分析报告标题）",
            value=auto_detected_company if auto_detected_company else "",
            placeholder="例如：凯莱英、普洛药业",
            help="系统会自动从文件名识别公司名称，您也可以手动修改"
        )
        
        if not company_name:
            st.warning("⚠️ 请输入公司名称，用于生成分析报告标题")
        else:
            # 分析按钮
            st.markdown("---")
            # 数据提取选项
            st.markdown("---")
            st.subheader("📊 数据提取与存储")
        extract_data = st.checkbox("🔍 自动提取结构化数据并保存到数据库", value=True,
                                   help="分析时自动提取财务、业务等结构化数据并保存到MySQL数据库，便于后续查询和对比分析")

        # 数据库数据查询选项
        if st.session_state.db_manager is None:
            try:
                from database import DBConfig, DatabaseManager
                from data_extractor import DataQueryHelper
                db_config = DBConfig(**st.session_state.db_config)
                st.session_state.db_manager = DatabaseManager(db_config)
                st.session_state.data_query = DataQueryHelper(st.session_state.db_manager)
            except Exception as e:
                st.warning(f"⚠️ 数据库连接失败: {e}")

        if st.session_state.data_query:
            use_db_data = st.checkbox("📚 结合数据库历史数据进行分析", value=True,
                                      help="在分析时结合数据库中已有的历史数据，提供更全面的分析视角")
            if use_db_data:
                db_summary = st.session_state.data_query.get_company_data_summary(company_name)
                if "未找到" not in db_summary:
                    with st.expander("📋 查看数据库中的公司数据", expanded=False):
                        st.markdown(db_summary)
                else:
                    st.info("💡 数据库中暂无该公司数据，分析后将自动保存")

        st.markdown("---")
        if st.button("🚀 开始分析", type="primary", use_container_width=True):
            if all_files:
                st.session_state.analysis_results = []

                # 初始化数据提取器（如果需要）
                data_extractor = None
                if extract_data and st.session_state.db_manager:
                    try:
                        from data_extractor import DataExtractor
                        data_extractor = DataExtractor(
                            st.session_state.db_manager,
                            st.session_state.model_config
                        )
                    except Exception as e:
                        st.warning(f"⚠️ 数据提取器初始化失败: {e}")

                # 计算总分析任务数
                total_tasks = len(all_files) * len(selected_dimensions)
                current_task = 0

                progress_bar = st.progress(0)
                status_text = st.empty()

                for file_path in all_files:
                    # 解析文档内容
                    from ai_analyzer import DocumentParser
                    parser = DocumentParser()
                    doc_content = parser.parse_file(file_path)

                    # 数据提取和保存
                    if data_extractor and doc_content:
                        try:
                            status_text.text(f"📊 正在提取数据: {os.path.basename(file_path)}...")
                            success, extracted_data = data_extractor.extract_and_save(
                                file_path, doc_content, company_name
                            )
                            if success:
                                st.info(f"✅ 已从 '{os.path.basename(file_path)}' 提取并保存数据")
                        except Exception as e:
                            st.warning(f"⚠️ 数据提取失败: {e}")

                    for dimension in selected_dimensions:
                        current_task += 1
                        status_text.text(f"正在分析 ({current_task}/{total_tasks}): {os.path.basename(file_path)} - {dimension}")

                        # 准备分析上下文
                        analysis_context = doc_content or ""

                        # 如果启用了数据库查询，添加历史数据
                        if use_db_data and st.session_state.data_query:
                            try:
                                trend_data = st.session_state.data_query.get_financial_trend(company_name)
                                if trend_data:
                                    analysis_context += f"\n\n[历史财务数据]\n{trend_data}"
                            except Exception as e:
                                pass  # 忽略数据库查询错误

                        result = st.session_state.analyzer.analyze_document(
                            file_path,
                            company_name,
                            dimension,
                            analysis_depth
                        )
                        st.session_state.analysis_results.append(result)
                        progress_bar.progress(current_task / total_tasks)

                status_text.empty()
                progress_bar.empty()

                # 计算分析统计
                total_analysis_time = sum(r.get('analysis_time', 0) for r in st.session_state.analysis_results if 'error' not in r)
                total_prompt_tokens = sum(r.get('token_usage', {}).get('prompt_tokens', 0) for r in st.session_state.analysis_results if 'error' not in r)
                total_completion_tokens = sum(r.get('token_usage', {}).get('completion_tokens', 0) for r in st.session_state.analysis_results if 'error' not in r)
                total_tokens = sum(r.get('token_usage', {}).get('total_tokens', 0) for r in st.session_state.analysis_results if 'error' not in r)
                success_count = len([r for r in st.session_state.analysis_results if 'error' not in r])
                failed_count = len([r for r in st.session_state.analysis_results if 'error' in r])

                # 显示分析统计
                st.markdown("---")
                st.subheader("📊 分析统计")

                # 统计卡片
                stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                stat_col1.metric("✅ 成功", success_count)
                stat_col2.metric("❌ 失败", failed_count)
                stat_col3.metric("⏱️ 总耗时", f"{total_analysis_time:.1f}秒")
                stat_col4.metric("📝 总Token", f"{total_tokens:,}")

                # 详细信息
                st.markdown("---")
                st.write("**详细统计：**")
                detail_col1, detail_col2, detail_col3 = st.columns(3)

                with detail_col1:
                    st.write(f"📁 分析文件数: {len(all_files)}")
                    st.write(f"📊 分析维度数: {len(selected_dimensions)}")
                    st.write(f"🔢 总任务数: {total_tasks}")

                with detail_col2:
                    if success_count > 0:
                        avg_time = total_analysis_time / success_count
                        st.write(f"⏲️ 平均耗时: {avg_time:.2f}秒/任务")
                    st.write(f"📥 输入Token: {total_prompt_tokens:,}")
                    st.write(f"📤 输出Token: {total_completion_tokens:,}")

                with detail_col3:
                    if total_tokens > 0:
                        input_ratio = (total_prompt_tokens / total_tokens) * 100
                        output_ratio = (total_completion_tokens / total_tokens) * 100
                        st.write(f"📊 输入占比: {input_ratio:.1f}%")
                        st.write(f"📊 输出占比: {output_ratio:.1f}%")
                    success_rate = (success_count / total_tasks * 100) if total_tasks > 0 else 0
                    st.write(f"📈 成功率: {success_rate:.1f}%")

                st.success(f"✅ 分析完成！共分析 {len(all_files)} 个文件，{len(selected_dimensions)} 个维度")
            else:
                st.warning("请上传文件或选择已有文件")
        
        # 显示分析结果
        if st.session_state.analysis_results:
            st.markdown("---")
            st.subheader("📊 分析结果")

            # 按维度分组显示结果
            results_by_dimension = {}
            for result in st.session_state.analysis_results:
                dim = result.get('dimension', '未知维度')
                if dim not in results_by_dimension:
                    results_by_dimension[dim] = []
                results_by_dimension[dim].append(result)

            # 使用tab展示不同维度的结果
            dim_tabs = st.tabs(list(results_by_dimension.keys()))

            for tab, (dim, results) in zip(dim_tabs, results_by_dimension.items()):
                with tab:
                    for i, result in enumerate(results):
                        if "error" in result:
                            st.error(f"❌ 分析失败 ({result['file']}): {result['error']}")
                        else:
                            with st.expander(f"📄 {result['file']}", expanded=(i == 0)):
                                # 显示分析文本
                                st.markdown(result['result'])

                                # 显示图表（如果有）
                                chart_data_list = result.get('chart_data', [])
                                if chart_data_list:
                                    st.markdown("---")
                                    st.subheader("📈 数据可视化")

                                    for chart_data in chart_data_list:
                                        render_chart(chart_data)

            # 下载功能
            download_results(st.session_state.analysis_results, company_name)

            # 数据库可视化图表
            if st.session_state.data_query and company_name:
                st.markdown("---")
                st.subheader("📈 数据库可视化分析")

                # 获取公司ID
                company = st.session_state.data_query.repo.get_company(name=company_name)
                if company:
                    company_id = company['id']

                    # 财务趋势图表
                    financial_metrics = st.session_state.data_query.repo.get_financial_metrics(
                        company_id,
                        ['revenue', 'net_profit', 'gross_margin', 'roe'],
                        years=5
                    )

                    if financial_metrics.get('years'):
                        st.markdown("#### 📊 财务趋势分析")

                        # 创建趋势图表
                        import plotly.graph_objects as go
                        from plotly.subplots import make_subplots

                        # 营收和利润趋势
                        fig1 = make_subplots(specs=[[{"secondary_y": True}]])

                        years = financial_metrics['years']
                        revenue = [r/1e8 if r else 0 for r in financial_metrics['revenue']]
                        profit = [p/1e8 if p else 0 for p in financial_metrics['net_profit']]

                        fig1.add_trace(
                            go.Bar(name='营业收入(亿元)', x=years, y=revenue, marker_color='#3498db'),
                            secondary_y=False
                        )
                        fig1.add_trace(
                            go.Scatter(name='净利润(亿元)', x=years, y=profit, mode='lines+markers',
                                     line=dict(color='#e74c3c', width=3), marker=dict(size=8)),
                            secondary_y=True
                        )

                        fig1.update_layout(
                            title=f"{company_name} 营收与利润趋势",
                            xaxis_title="年份",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            height=400
                        )
                        fig1.update_yaxes(title_text="营业收入(亿元)", secondary_y=False)
                        fig1.update_yaxes(title_text="净利润(亿元)", secondary_y=True)

                        st.plotly_chart(fig1, use_container_width=True)

                        # 盈利能力指标趋势
                        fig2 = go.Figure()

                        gross_margin = [g if g else 0 for g in financial_metrics['gross_margin']]
                        roe = [r if r else 0 for r in financial_metrics['roe']]

                        fig2.add_trace(go.Scatter(
                            name='毛利率(%)', x=years, y=gross_margin,
                            mode='lines+markers', line=dict(color='#2ecc71', width=3),
                            marker=dict(size=8)
                        ))
                        fig2.add_trace(go.Scatter(
                            name='ROE(%)', x=years, y=roe,
                            mode='lines+markers', line=dict(color='#f39c12', width=3),
                            marker=dict(size=8)
                        ))

                        fig2.update_layout(
                            title=f"{company_name} 盈利能力指标趋势",
                            xaxis_title="年份",
                            yaxis_title="百分比(%)",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            height=400
                        )

                        st.plotly_chart(fig2, use_container_width=True)

                        # 数据表格
                        with st.expander("📋 查看详细数据"):
                            df_data = {
                                '年份': years,
                                '营业收入(亿元)': [f"{r:.2f}" for r in revenue],
                                '净利润(亿元)': [f"{p:.2f}" for p in profit],
                                '毛利率(%)': [f"{g:.2f}" if g else "N/A" for g in gross_margin],
                                'ROE(%)': [f"{r:.2f}" if r else "N/A" for r in roe]
                            }
                            df = pd.DataFrame(df_data)
                            st.dataframe(df, use_container_width=True)
                    else:
                        st.info("💡 数据库中暂无该公司的财务数据，请先进行分析以提取数据")

    with tab5:
        # 数据管理模块
        st.write("DEBUG: tab5 开始渲染")
        render_data_module()
        st.write("DEBUG: tab5 渲染完成")


if __name__ == "__main__":
    main()
