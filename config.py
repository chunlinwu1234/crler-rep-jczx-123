
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

# ==================== Ollama AI配置 ====================
# Ollama服务地址（默认本地11434端口）
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# 默认使用的模型名称
# 可选模型：qwen2.5:7b, qwen3:8b, deepseek-r1:7b 等
# 使用 `ollama list` 命令查看本地可用模型
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# 模型参数配置
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.3"))  # 创造性程度，0-1之间
OLLAMA_MAX_TOKENS = int(os.getenv("OLLAMA_MAX_TOKENS", "4096"))     # 最大输出token数
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "300"))              # 请求超时时间（秒）

# 向量数据库配置
VECTOR_STORE_DIR = os.path.join(PROJECT_ROOT, "vector_store")

# 文档解析配置
MAX_DOCUMENT_LENGTH = 15000  # 单次分析最大字符数
SUPPORTED_DOC_TYPES = [".pdf", ".docx", ".txt"]  # 支持的文档类型

