
# 巨潮资讯公告下载器

一个用于从巨潮资讯网（cninfo.com.cn）下载股票公告PDF的Python工具，提供友好的Streamlit网页界面。

## 项目介绍

本项目帮助用户快速下载指定股票的公告PDF文件，支持：
- 按股票名称或代码搜索
- 多种公告类型（最新公告、定期报告、调研）
- 自定义下载路径
- 自动随机延迟避免被封禁
- Streamlit网页界面，操作简单

## 安装说明

### 环境要求

- Python 3.8+
- Windows操作系统

### 安装步骤

1. 克隆或下载项目到本地
2. 安装依赖包：
   ```bash
   pip install -r requirements.txt
   ```

## 使用说明

### 启动网页版
cmd或powershell命令行中，切换到app.py文件夹下
```bash
streamlit run app.py
```

启动后浏览器会自动打开 `http://localhost:8501`

### 操作步骤

1. **搜索股票**：输入股票名称或代码，点击搜索
2. **筛选公告**：选择公告类型、日期范围和数量
3. **获取列表**：点击"获取公告列表"查看可用公告
4. **选择下载**：勾选需要下载的公告
5. **开始下载**：点击"开始下载"按钮

### 配置项

- **下载目录**：设置PDF文件保存位置
- **请求间隔**：设置请求之间的随机延迟范围（5-10秒）

## 项目结构

```
CIMS/
├── app.py                    # Streamlit网页主程序
├── config.py                 # 配置文件
├── stock_downloader.py       # 核心下载模块
├── requirements.txt          # Python依赖包列表
├── README.md                 # 项目说明文档
├── 巨潮资讯URL示例.txt       # URL示例文件
├── downloads/                # 默认下载目录（自动创建）
└── stock_map.json            # 股票信息映射文件（自动创建）
```

## 文件结构说明

### 核心文件

| 文件 | 说明 |
|------|------|
| `app.py` | Streamlit网页界面主文件，提供用户交互界面 |
| `config.py` | 配置文件，存储默认设置和常量 |
| `stock_downloader.py` | 核心下载模块，实现股票搜索、公告获取、PDF下载功能 |
| `requirements.txt` | Python依赖包列表 |

### 数据文件

| 文件 | 说明 |
|------|------|
| `stock_map.json` | 股票代码与名称的映射缓存，提高搜索效率 |
| `downloads/` | 下载的PDF文件存储目录，按股票名称+代码分类 |

## 核心模块说明

### StockInfo类
股票信息类，存储股票的基本信息：
- `code`: 股票代码
- `name`: 股票名称
- `org_id`: 机构ID
- `plate`: 板块（szse深交所，sse上交所）

### AnnouncementInfo类
公告信息类，存储公告的基本信息：
- `announcement_id`: 公告ID
- `title`: 公告标题
- `announcement_time`: 公告时间
- `announcement_type`: 公告类型
- `pdf_url`: PDF下载链接

### StockDownloader类
下载器主类，提供以下主要方法：

- `search_stock(query)`: 根据股票名称或代码搜索股票信息
- `get_announcements(stock_info, ...)`: 获取指定股票的公告列表
- `download_pdf(announcement, stock_info)`: 下载单个公告PDF
- `batch_download(query, ...)`: 批量下载股票公告

## 代码规范

### 命名规范
- 类名：大驼峰命名法（如 `StockDownloader`）
- 函数名：小写字母+下划线（如 `search_stock`）
- 常量：全大写+下划线（如 `DEFAULT_DOWNLOAD_DIR`）
- 私有方法：单下划线前缀（如 `_random_delay`）

### 注释规范
- 所有函数和类必须添加中文文档字符串
- 关键逻辑添加行内注释
- 使用清晰的变量名和函数名，避免无意义的命名

### 错误处理
- 使用try-except捕获异常
- 提供友好的错误提示信息
- 避免程序崩溃，尽可能优雅处理异常

## 贡献说明

欢迎提交Issue和Pull Request！

1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 注意事项

1. **请遵守巨潮资讯网的使用条款**，合理使用本工具
2. 设置适当的请求间隔，避免对服务器造成过大压力
3. 本工具仅供学习和研究使用
4. 如遇到问题，请检查网络连接和股票代码是否正确

## 许可证

MIT License

## 更新日志

### v1.0.0 (2026-03-05)
- 初始版本发布
- 支持股票搜索和公告下载
- Streamlit网页界面
- 随机延迟避免封禁

