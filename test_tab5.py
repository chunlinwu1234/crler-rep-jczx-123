"""测试Tab5问题"""
import streamlit as st

st.set_page_config(page_title="Tab5 Test", layout="wide")

st.title("测试Tab5")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Tab1", "Tab2", "Tab3", "Tab4", "Tab5"])

with tab1:
    st.write("Tab1内容")

with tab2:
    st.write("Tab2内容")

with tab3:
    st.write("Tab3内容")

with tab4:
    st.write("Tab4内容")

with tab5:
    st.write("Tab5内容 - 这应该显示")
    st.header("Tab5标题")
    st.markdown("这是Tab5的内容")

st.write("页面底部")
