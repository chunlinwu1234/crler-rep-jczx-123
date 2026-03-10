"""
CIMS - 简化测试版本
"""
import streamlit as st
from data_module_ui_simple import render_data_module

# 设置页面配置
st.set_page_config(
    page_title="CIMS - 简化测试",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """主函数"""
    st.title("🔍 CIMS - 竞争情报监控系统")
    st.markdown("简化测试版本")
    
    # 主内容区
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 搜索下载", "📜 历史记录", "⏰ 定时任务", "🤖 AI分析", "📊 数据管理"])
    
    with tab1:
        st.header("🔍 搜索下载")
        st.write("搜索下载内容")
    
    with tab2:
        st.header("📜 历史记录")
        st.write("历史记录内容")
    
    with tab3:
        st.header("⏰ 定时任务")
        st.write("定时任务内容")
    
    with tab4:
        st.header("🤖 AI分析")
        st.write("AI分析内容")
    
    with tab5:
        st.write("DEBUG: tab5 开始渲染")
        render_data_module()
        st.write("DEBUG: tab5 渲染完成")

if __name__ == "__main__":
    main()
