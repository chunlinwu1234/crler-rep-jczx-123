"""最小化测试"""
import streamlit as st

st.set_page_config(page_title="Minimal Test", layout="wide")

st.title("测试Tab5")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Tab1", "Tab2", "Tab3", "Tab4", "数据管理"])

with tab1:
    st.write("Tab 1")

with tab2:
    st.write("Tab 2")

with tab3:
    st.write("Tab 3")

with tab4:
    st.write("Tab 4")
    # 模拟一个条件停止
    if st.checkbox("停止Tab4", value=False):
        st.stop()
    st.write("Tab 4 continues")

with tab5:
    st.header("📊 数据管理")
    st.write("Tab 5 内容")
    
    tabs = st.tabs(["概览", "导入", "提取"])
    with tabs[0]:
        st.write("概览内容")
    with tabs[1]:
        st.write("导入内容")
    with tabs[2]:
        st.write("提取内容")

st.write("结束")
