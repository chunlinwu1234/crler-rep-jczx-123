
"""
配置文件模块
存储项目的默认配置和常量
"""
import os

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

# 默认下载目录
DEFAULT_DOWNLOAD_DIR = os.path.join(PROJECT_ROOT, "downloads")

# 默认请求头部
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# 巨潮资讯网相关URL
CNINFO_BASE_URL = "https://www.cninfo.com.cn"
CNINFO_DISCLOSURE_URL = "https://www.cninfo.com.cn/new/disclosure/stock"
CNINFO_LIST_URL = "https://www.cninfo.com.cn/new/hisAnnouncement/query"

# 请求间隔设置（秒）
MIN_DELAY = 5
MAX_DELAY = 10

# 股票代码与名称映射文件路径
STOCK_MAP_FILE = os.path.join(PROJECT_ROOT, "stock_map.json")

