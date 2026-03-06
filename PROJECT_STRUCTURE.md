
# 项目结构说明

## 目录树

```
CIMS/
│
├── __init__.py                 # Python包初始化文件（空文件）
├── app.py                      # Streamlit网页主程序
├── config.py                   # 配置文件
├── stock_downloader.py         # 核心下载模块
├── requirements.txt            # Python依赖包列表
├── README.md                   # 项目说明文档
├── PROJECT_STRUCTURE.md        # 本文档，项目结构详细说明
├── 巨潮资讯URL示例.txt         # 巨潮资讯URL示例文件
│
├── downloads/                  # 默认下载目录（自动创建）
│   └── [股票名称_股票代码]/    # 按股票分类的子目录
│       └── [公告文件].pdf      # 下载的PDF文件
│
└── stock_map.json              # 股票信息映射文件（自动创建）
```

## 文件详细说明

### 1. 核心程序文件

#### app.py
- **功能**: Streamlit网页界面主文件
- **主要内容**:
  - 页面配置和布局
  - 用户交互界面（侧边栏设置、搜索框、筛选条件等）
  - 搜索股票、获取公告、下载PDF的交互逻辑
  - 进度显示和结果展示
- **关键函数**:
  - `init_session_state()`: 初始化会话状态
  - `main()`: 主函数，程序入口

#### config.py
- **功能**: 配置文件，存储项目的默认配置和常量
- **主要配置项**:
  - `PROJECT_ROOT`: 项目根目录
  - `DEFAULT_DOWNLOAD_DIR`: 默认下载目录
  - `DEFAULT_HEADERS`: 默认HTTP请求头部（包含User-Agent）
  - `CNINFO_BASE_URL`: 巨潮资讯网基础URL
  - `MIN_DELAY`, `MAX_DELAY`: 请求间隔范围（秒）
  - `STOCK_MAP_FILE`: 股票信息映射文件路径

#### stock_downloader.py
- **功能**: 核心下载模块，实现所有业务逻辑
- **主要类**:
  1. **StockInfo**: 股票信息类
     - 属性: code（代码）, name（名称）, org_id（机构ID）, plate（板块）
     - 方法: to_dict(), from_dict()

  2. **AnnouncementInfo**: 公告信息类
     - 属性: announcement_id, title, announcement_time, announcement_type, pdf_url
     - 方法: to_dict()

  3. **StockDownloader**: 下载器主类
     - 初始化参数: download_dir, headers, min_delay, max_delay
     - 主要方法:
       - `search_stock(query)`: 搜索股票
       - `get_announcements(...)`: 获取公告列表
       - `download_pdf(...)`: 下载单个PDF
       - `batch_download(...)`: 批量下载
       - `_random_delay()`: 随机延迟
       - `_load_stock_map()`: 加载股票映射
       - `_save_stock_map()`: 保存股票映射

### 2. 配置和文档文件

#### requirements.txt
- **功能**: Python依赖包列表
- **包含的包**:
  - streamlit: Web框架
  - pandas: 数据处理
  - requests: HTTP请求

#### README.md
- **功能**: 项目说明文档
- **内容**: 项目介绍、安装说明、使用说明、项目结构、核心模块说明、代码规范、贡献说明等

#### PROJECT_STRUCTURE.md (本文档)
- **功能**: 详细的项目结构说明

#### 巨潮资讯URL示例.txt
- **功能**: 提供巨潮资讯网URL格式的示例
- **内容**: 包含普洛药业和恒瑞医药的各种公告类型URL示例

### 3. 数据和输出文件

#### stock_map.json（自动创建）
- **功能**: 缓存股票代码与名称的映射关系
- **格式**: JSON格式
- **示例**:
  ```json
  {
    "000739": {
      "code": "000739",
      "name": "普洛药业",
      "org_id": "gssz0000739",
      "plate": "szse"
    }
  }
  ```

#### downloads/（自动创建）
- **功能**: PDF文件的默认下载目录
- **结构**: 按"股票名称_股票代码"创建子目录
- **文件命名**: "公告时间_公告标题.pdf"
- **示例**:
  ```
  downloads/
  ├── 普洛药业_000739/
  │   ├── 2026-02-28_关于2025年度业绩预告的公告.pdf
  │   └── ...
  └── 恒瑞医药_600276/
      └── ...
  ```

## 数据流程

```
用户输入股票名称/代码
    ↓
search_stock() 搜索股票信息
    ↓
get_announcements() 获取公告列表
    ↓
用户选择要下载的公告
    ↓
download_pdf() 逐个下载PDF文件
    ↓
保存到downloads/[股票名_代码]/目录
```

## 模块依赖关系

```
app.py (Streamlit界面)
    ↓ 依赖
stock_downloader.py (核心业务逻辑)
    ↓ 依赖
config.py (配置文件)
    ↓ 依赖
第三方库 (requests, pandas等)
```

## 扩展建议

1. **数据库集成**: 可以添加SQLite或其他数据库来存储下载历史
2. **定时任务**: 集成APScheduler实现定时自动下载
3. **更多公告类型**: 扩展支持更多公告类别
4. **PDF内容解析**: 添加PDF文本提取和分析功能
5. **多股票批量下载**: 支持同时下载多个股票的公告

