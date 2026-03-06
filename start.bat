
@echo off
chcp 65001 &gt;nul
echo ========================================
echo   巨潮资讯公告下载器
echo ========================================
echo.
echo 正在启动Streamlit网页界面...
echo.

REM 检查Python是否安装
python --version &gt;nul 2&gt;&amp;1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖包...
pip show streamlit &gt;nul 2&gt;&amp;1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
)

echo.
echo 启动网页界面...
echo 打开浏览器访问: http://localhost:8501
echo.
streamlit run app.py

pause

