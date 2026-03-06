
"""
Streamlit网页界面主文件
提供友好的图形化操作界面
"""
import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from stock_downloader import StockDownloader
import threading
import json


# 设置页面配置
st.set_page_config(
    page_title="巨潮资讯公告下载器",
    page_icon="📄",
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


def main():
    """主函数"""
    init_session_state()
    
    st.title("📄 巨潮资讯公告下载器")
    st.markdown("从巨潮资讯网下载股票公告PDF文件")
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # 下载目录设置
        download_dir = st.text_input(
            "下载目录",
            value=os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads"),
            help="公告PDF保存目录"
        )
        
        # 请求间隔设置
        col1, col2 = st.columns(2)
        with col1:
            min_delay = st.number_input(
                "最小间隔(秒)",
                min_value=1,
                max_value=60,
                value=5,
                help="请求之间的最小延迟"
            )
        with col2:
            max_delay = st.number_input(
                "最大间隔(秒)",
                min_value=1,
                max_value=60,
                value=10,
                help="请求之间的最大延迟"
            )
        
        st.markdown("---")
        
        st.header("ℹ️ 关于")
        st.markdown("""
        这是一个用于从巨潮资讯网下载股票公告的工具
        - 支持股票名称或代码搜索
        - 支持多种公告类型
        - 自动随机延迟避免封禁
        """)
    
    # 主内容区
    tab1, tab2, tab3 = st.tabs(["搜索下载", "历史记录", "定时任务"])
    
    with tab1:
        # 初始化下载器
        if st.session_state.downloader is None:
            st.session_state.downloader = StockDownloader(
                download_dir=download_dir,
                min_delay=min_delay,
                max_delay=max_delay
            )
        
        st.subheader("🔍 搜索股票")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            stock_query = st.text_input(
                "股票名称或代码",
                placeholder="例如：普洛药业 或 000739",
                help="输入股票名称或6位代码"
            )
        with col2:
            search_btn = st.button("搜索", type="primary")
        
        # 搜索股票
        if search_btn and stock_query:
            with st.spinner("正在搜索股票信息..."):
                stock_info = st.session_state.downloader.search_stock(stock_query)
                if stock_info:
                    st.session_state.stock_info = stock_info
                    st.success(f"找到股票：{stock_info.name} ({stock_info.code}")
                else:
                    st.error(f"未找到股票信息")
        
        # 显示股票信息和公告
        if st.session_state.stock_info:
            stock_info = st.session_state.stock_info
            st.markdown("---")
            st.subheader(f"📊 股票信息")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("股票名称", stock_info.name)
            col2.metric("股票代码", stock_info.code)
            col3.metric("机构ID", stock_info.org_id)
            col4.metric("板块", "深交所" if stock_info.plate == "szse" else "上交所")
            
            st.markdown("---")
            st.subheader("📋 公告筛选")
            
            # 公告类型选择
            ann_types = st.multiselect(
                "公告类型",
                ["latest", "periodic", "research"],
                default=["latest"],
                format_func=lambda x: {
                    "latest": "最新公告",
                    "periodic": "定期报告",
                    "research": "调研"
                }.get(x, x)
            )
            
            # 根据选择的类型给出提示
            if "research" in ann_types:
                st.info("💡 提示：调研公告可能分布在较长时间范围内，建议使用10年以上的时间范围")
            
            # 日期范围选择
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "开始日期",
                    value=datetime.now() - timedelta(days=3650 if "research" in ann_types else 365)
                )
            with col2:
                end_date = st.date_input(
                    "结束日期",
                    value=datetime.now()
                )
            
            max_count = st.slider(
                "每种类型最多下载数量",
                min_value=1,
                max_value=100,
                value=10
            )
            
            # 获取公告列表
            if st.button("获取公告列表"):
                with st.spinner("正在获取公告列表..."):
                    all_announcements = []
                    for ann_type in ann_types:
                        ann_list = st.session_state.downloader.get_announcements(
                            stock_info,
                            ann_type,
                            start_date.strftime("%Y-%m-%d"),
                            end_date.strftime("%Y-%m-%d"),
                            max_count
                        )
                        all_announcements.extend(ann_list)
                    
                    st.session_state.announcements = all_announcements
            
            # 显示公告列表
            if st.session_state.announcements:
                st.markdown("---")
                st.subheader("📄 公告列表")
                
                # 转换为DataFrame显示
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
                        st.session_state.downloading = True
                        selected_anns = [st.session_state.announcements[i] for i in selected_indices]
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        success_count = 0
                        failed_count = 0
                        files = []
                        
                        for i, ann in enumerate(selected_anns):
                            status_text.text(f"正在下载 {i+1}/{len(selected_anns)}: {ann.title}")
                            filepath = st.session_state.downloader.download_pdf(ann, stock_info)
                            
                            if filepath:
                                success_count += 1
                                files.append(filepath)
                            else:
                                failed_count += 1
                            
                            progress_bar.progress((i + 1) / len(selected_anns))
                        
                        st.session_state.downloading = False
                        
                        # 显示下载结果
                        st.markdown("---")
                        st.subheader("✅ 下载完成")
                        col1, col2 = st.columns(2)
                        col1.metric("成功", success_count)
                        col2.metric("失败", failed_count)
                        
                        if files:
                            st.success(f"文件保存在: {os.path.dirname(files[0])}")
                    else:
                        st.warning("请先选择要下载的公告")
    
    with tab2:
        st.subheader("📜 历史记录")
        st.info("历史记录功能开发中...")
    
    with tab3:
        st.subheader("⏰ 定时任务")
        st.info("定时任务功能开发中...")
        
        # 简单的定时任务设置
        st.markdown("---")
        st.write("定时任务设置（开发中）")
        st.markdown("支持人工触发模式选择：")
        st.radio(
            "执行模式",
            ["人工执行", "定时执行"],
            index=0
        )


if __name__ == "__main__":
    main()

