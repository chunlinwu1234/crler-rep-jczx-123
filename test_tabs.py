"""测试tab渲染"""
import streamlit as st

st.set_page_config(page_title="Tab Test", layout="wide")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Tab1", "Tab2", "Tab3", "Tab4", "Tab5"])

with tab1:
    st.header("Tab 1 Content")
    st.write("This is tab 1")

with tab2:
    st.header("Tab 2 Content")
    st.write("This is tab 2")

with tab3:
    st.header("Tab 3 Content")
    st.write("This is tab 3")

with tab4:
    st.header("Tab 4 Content")
    st.write("This is tab 4")
    
    # 模拟条件
    condition = st.checkbox("Check to stop", value=False)
    if condition:
        st.warning("Stopping!")
        st.stop()
    
    st.write("Tab 4 continues...")

with tab5:
    st.header("📊 数据管理")
    st.write("This is tab 5 - Data Management")
    
    # 测试子标签页
    subtab1, subtab2 = st.tabs(["SubTab1", "SubTab2"])
    with subtab1:
        st.write("SubTab 1 content")
    with subtab2:
        st.write("SubTab 2 content")

st.write("App completed!")
