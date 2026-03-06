
"""
股票公告下载器核心模块
负责从巨潮资讯网获取股票信息和下载公告PDF
"""
import os
import time
import random
import json
import re
from datetime import datetime, timedelta
import requests
import brotli


class StockInfo:
    """股票信息类，存储股票基本信息"""
    
    def __init__(self, code, name, org_id, plate):
        self.code = code  # 股票代码
        self.name = name  # 股票名称
        self.org_id = org_id  # 机构ID
        self.plate = plate  # 板块（szse: 深交所, sse: 上交所）
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "code": self.code,
            "name": self.name,
            "org_id": self.org_id,
            "plate": self.plate
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建实例"""
        return cls(data["code"], data["name"], data["org_id"], data["plate"])


class AnnouncementInfo:
    """公告信息类，存储公告基本信息"""
    
    def __init__(self, announcement_id, title, announcement_time, 
                 announcement_type, pdf_url=None, adjunct_url=None):
        self.announcement_id = announcement_id  # 公告ID
        self.title = title  # 公告标题
        self.announcement_time = announcement_time  # 公告时间
        self.announcement_type = announcement_type  # 公告类型
        self.pdf_url = pdf_url  # PDF下载链接
        self.adjunct_url = adjunct_url  # 原始附件URL
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "announcement_id": self.announcement_id,
            "title": self.title,
            "announcement_time": self.announcement_time,
            "announcement_type": self.announcement_type,
            "pdf_url": self.pdf_url,
            "adjunct_url": self.adjunct_url
        }


class StockDownloader:
    """股票公告下载器主类"""
    
    def __init__(self, download_dir=None, 
                 headers=None,
                 min_delay=5, max_delay=10):
        """
        初始化下载器
        
        Args:
            download_dir: 下载目录，默认为config.DEFAULT_DOWNLOAD_DIR
            headers: 请求头部，默认为config.DEFAULT_HEADERS
            min_delay: 最小请求间隔（秒）
            max_delay: 最大请求间隔（秒）
        """
        from config import DEFAULT_DOWNLOAD_DIR, DEFAULT_HEADERS
        
        self.download_dir = download_dir or DEFAULT_DOWNLOAD_DIR
        self.headers = headers or DEFAULT_HEADERS
        self.min_delay = min_delay
        self.max_delay = max_delay
        
        # 确保下载目录存在
        os.makedirs(self.download_dir, exist_ok=True)
        
        # 初始化会话
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # 股票代码与名称映射
        self.stock_map = {}
        self._load_stock_map()
    
    def _load_stock_map(self):
        """加载股票代码与名称映射"""
        from config import STOCK_MAP_FILE
        
        if os.path.exists(STOCK_MAP_FILE):
            try:
                with open(STOCK_MAP_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for code, info in data.items():
                        self.stock_map[code] = StockInfo.from_dict(info)
                        self.stock_map[info["name"]] = StockInfo.from_dict(info)
            except Exception as e:
                print(f"加载股票映射文件失败: {e}")
    
    def _save_stock_map(self):
        """保存股票代码与名称映射"""
        from config import STOCK_MAP_FILE
        
        data = {}
        for key, info in self.stock_map.items():
            if key == info.code:  # 只保存一次
                data[info.code] = info.to_dict()
        
        try:
            with open(STOCK_MAP_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存股票映射文件失败: {e}")
    
    def _random_delay(self):
        """随机延迟请求，避免被封禁"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)
    
    def search_stock(self, query):
        """
        根据股票名称或代码搜索股票信息
        
        Args:
            query: 股票名称或代码
            
        Returns:
            股票信息对象，未找到返回None
        """
        # 先在本地映射中查找
        query = query.strip()
        if query in self.stock_map:
            return self.stock_map[query]
        
        # 预定义的股票映射（基于示例文件）
        predefined_stocks = {
            "000739": {"name": "普洛药业", "org_id": "gssz0000739", "plate": "szse"},
            "普洛药业": {"name": "普洛药业", "org_id": "gssz0000739", "plate": "szse"},
            "600276": {"name": "恒瑞医药", "org_id": "gssh0600276", "plate": "sse"},
            "恒瑞医药": {"name": "恒瑞医药", "org_id": "gssh0600276", "plate": "sse"}
        }
        
        # 先检查预定义的股票
        if query in predefined_stocks:
            stock_data = predefined_stocks[query]
            # 确定股票代码
            stock_code = query
            if len(query) != 6:
                # 查找对应的6位代码
                for k, v in predefined_stocks.items():
                    if v["name"] == stock_data["name"] and len(k) == 6:
                        stock_code = k
                        break
            
            stock_info = StockInfo(
                code=stock_code,
                name=stock_data["name"],
                org_id=stock_data["org_id"],
                plate=stock_data["plate"]
            )
            
            # 保存到本地映射
            self.stock_map[stock_info.code] = stock_info
            self.stock_map[stock_info.name] = stock_info
            self._save_stock_map()
            
            return stock_info
        
        # 如果是6位代码，尝试根据规则构建
        if len(query) == 6:
            # 判断板块
            if query.startswith(("000", "001", "002", "003", "300")):
                plate = "szse"
                org_id = f"gssz000{query}"
            else:
                plate = "sse"
                org_id = f"gssh0{query}"
            
            stock_info = StockInfo(query, query, org_id, plate)
            self.stock_map[query] = stock_info
            self._save_stock_map()
            
            return stock_info
        
        return None
    
    def get_announcements(self, stock_info, 
                          announcement_type="latest",
                          start_date=None,
                          end_date=None,
                          max_count=10):
        """
        获取股票公告列表
        
        Args:
            stock_info: 股票信息对象
            announcement_type: 公告类型 (latest: 最新公告, periodic: 定期报告, research: 调研)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            max_count: 每种类型最多获取的公告数量
            
        Returns:
            公告信息列表
        """
        announcements = []
        
        try:
            # 构建查询参数
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                # 调研类型使用更长的时间范围（10年）
                if announcement_type == "research":
                    start_date = (datetime.now() - timedelta(days=3650)).strftime("%Y-%m-%d")
                else:
                    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            # 公告类型对应的category
            category_map = {
                "latest": "",
                "periodic": "category_ndbg_szsh;category_bndbg_szsh;category_yjdbg_szsh;category_sjdbg_szsh",
                "research": ""
            }
            category = category_map.get(announcement_type, "")
            
            # 根据板块确定column参数
            column = "szse" if stock_info.plate == "szse" else "sse"
            
            # 确定要获取的页数
            max_pages = 1
            if announcement_type == "research":
                max_pages = 100  # 调研类型获取更多页（100页）
            
            url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
            
            print(f"正在请求公告列表，股票: {stock_info.name}({stock_info.code}), 类型: {announcement_type}")
            
            # 调研类型使用特殊的方法：搜索所有股票的调研公告，然后过滤
            if announcement_type == "research":
                return self._get_research_announcements(stock_info, start_date, end_date, max_pages, max_count)
            
            # 其他类型使用正常方法
            for page_num in range(1, max_pages + 1):
                data = {
                    "pageNum": page_num,
                    "pageSize": 30,
                    "column": column,
                    "tabName": "fulltext",
                    "plate": stock_info.plate,
                    "stock": f"{stock_info.code},{stock_info.org_id}",
                    "searchkey": "",
                    "secid": "",
                    "category": category,
                    "trade": "",
                    "seDate": f"{start_date}~{end_date}",
                    "sortName": "",
                    "sortType": "",
                    "isHLtitle": True
                }
                
                self._random_delay()
                response = self.session.post(url, data=data, timeout=30)
                response.raise_for_status()
                
                # 尝试正确解码响应
                content = response.content
                content_encoding = response.headers.get('Content-Encoding', '')
                
                # 处理Brotli压缩
                if 'br' in content_encoding:
                    try:
                        content = brotli.decompress(content)
                    except:
                        pass
                
                # 尝试解析JSON
                text = content.decode('utf-8')
                result = json.loads(text)
                
                # 处理返回的公告
                if result.get("announcements"):
                    page_announcements = result["announcements"]
                    print(f"第 {page_num} 页获取到 {len(page_announcements)} 条公告")
                    
                    for item in page_announcements:
                        # 检查是否已经达到最大数量
                        if len(announcements) >= max_count:
                            break
                        
                        announcement_id = str(item.get("announcementId", ""))
                        title = item.get("announcementTitle", "")
                        announcement_time = item.get("announcementTime", "")
                        adjunct_url = item.get("adjunctUrl", "")
                        
                        # 通过标题判断公告类型
                        is_periodic = False
                        is_research = False
                        
                        # 定期报告关键词
                        periodic_keywords = ["年度报告", "半年报告", "季度报告", "一季报", "中报", "三季报", "年报", "季度", "半年度"]
                        for keyword in periodic_keywords:
                            if keyword in title:
                                is_periodic = True
                                break
                        
                        # 调研关键词
                        research_keywords = [
                            "调研", "投资者关系", "活动记录表", "投资者调研", "机构调研",
                            "投资者关系活动", "调研活动", "机构投资者", "特定对象调研",
                            "分析师会议", "业绩说明会", "路演", "接受调研", "现场参观",
                            "记录表", "关系活动", "投资者", "活动记录", "集体接待日"
                        ]
                        for keyword in research_keywords:
                            if keyword in title:
                                is_research = True
                                break
                        
                        # 根据用户选择的类型过滤
                        should_include = True
                        if announcement_type == "periodic":
                            should_include = is_periodic
                        elif announcement_type == "latest":
                            should_include = not (is_periodic or is_research)
                        
                        if not should_include:
                            continue
                        
                        # 确定显示的类型
                        display_type = "latest"
                        if is_periodic:
                            display_type = "periodic"
                        elif is_research:
                            display_type = "research"
                        
                        # 构建完整的PDF URL
                        pdf_url = None
                        if adjunct_url:
                            pdf_url = f"https://www.cninfo.com.cn/{adjunct_url}"
                        
                        # 转换时间格式
                        if announcement_time:
                            try:
                                dt = datetime.fromtimestamp(int(announcement_time) / 1000)
                                announcement_time = dt.strftime("%Y-%m-%d")
                            except:
                                pass
                        
                        announcement_info = AnnouncementInfo(
                            announcement_id=announcement_id,
                            title=title,
                            announcement_time=announcement_time,
                            announcement_type=display_type,
                            pdf_url=pdf_url,
                            adjunct_url=adjunct_url
                        )
                        announcements.append(announcement_info)
                    
                    # 检查是否已经达到最大数量
                    if len(announcements) >= max_count:
                        break
                    
                    # 如果本页数据少于30条，说明已经是最后一页
                    if len(page_announcements) < 30:
                        break
                else:
                    break
            
            # 确保不超过最大数量
            announcements = announcements[:max_count]
            print(f"总共获取到 {len(announcements)} 条公告")
            return announcements
            
        except Exception as e:
            print(f"获取公告列表失败: {e}")
            import traceback
            traceback.print_exc()
            return announcements
    
    def _get_research_announcements(self, stock_info, start_date, end_date, max_pages, max_count=10):
        """
        专门获取调研公告的方法
        使用正确的API参数：tabName='relation'，category=''
        
        Args:
            stock_info: 股票信息对象
            start_date: 开始日期
            end_date: 结束日期
            max_pages: 最大页数
            max_count: 最多获取的公告数量
            
        Returns:
            调研公告列表
        """
        announcements = []
        url = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
        
        # 根据板块确定column参数
        column = "szse" if stock_info.plate == "szse" else "sse"
        
        print(f"获取股票的调研公告（使用tabName='relation'）...")
        
        # 使用正确的调研API参数获取公告
        for page_num in range(1, max_pages + 1):
            # 检查是否已经达到最大数量
            if len(announcements) >= max_count:
                break
                
            data = {
                "pageNum": page_num,
                "pageSize": 30,
                "column": column,
                "tabName": "relation",  # 调研专用tabName
                "plate": stock_info.plate,
                "stock": f"{stock_info.code},{stock_info.org_id}",
                "searchkey": "",
                "secid": "",
                "category": "",  # 调研category必须为空
                "trade": "",
                "seDate": f"{start_date}~{end_date}",
                "sortName": "",
                "sortType": "",
                "isHLtitle": True
            }
            
            self._random_delay()
            response = self.session.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            # 尝试正确解码响应
            content = response.content
            content_encoding = response.headers.get('Content-Encoding', '')
            
            # 处理Brotli压缩
            if 'br' in content_encoding:
                try:
                    content = brotli.decompress(content)
                except:
                    pass
            
            # 尝试解析JSON
            text = content.decode('utf-8')
            result = json.loads(text)
            
            # 处理返回的公告
            if result.get("announcements"):
                page_announcements = result["announcements"]
                print(f"第 {page_num} 页获取到 {len(page_announcements)} 条调研公告")
                
                for item in page_announcements:
                    # 检查是否已经达到最大数量
                    if len(announcements) >= max_count:
                        break
                        
                    announcement_id = str(item.get("announcementId", ""))
                    title = item.get("announcementTitle", "")
                    announcement_time = item.get("announcementTime", "")
                    adjunct_url = item.get("adjunctUrl", "")
                    
                    # 检查是否已经添加过这个公告
                    already_exists = False
                    for ann in announcements:
                        if ann.announcement_id == announcement_id:
                            already_exists = True
                            break
                    
                    if already_exists:
                        continue
                    
                    # 构建完整的PDF URL
                    pdf_url = None
                    if adjunct_url:
                        pdf_url = f"https://www.cninfo.com.cn/{adjunct_url}"
                    
                    # 转换时间格式
                    if announcement_time:
                        try:
                            dt = datetime.fromtimestamp(int(announcement_time) / 1000)
                            announcement_time = dt.strftime("%Y-%m-%d")
                        except:
                            pass
                    
                    announcement_info = AnnouncementInfo(
                        announcement_id=announcement_id,
                        title=title,
                        announcement_time=announcement_time,
                        announcement_type="research",
                        pdf_url=pdf_url,
                        adjunct_url=adjunct_url
                    )
                    announcements.append(announcement_info)
                    print(f"  ✓ 找到: [{announcement_time}] {title}")
                
                # 检查是否已经达到最大数量
                if len(announcements) >= max_count:
                    break
                    
                # 如果本页数据少于30条，说明已经是最后一页
                if len(page_announcements) < 30:
                    break
            else:
                break
        
        # 按时间倒序排序
        announcements.sort(key=lambda x: x.announcement_time, reverse=True)
        
        # 确保不超过最大数量
        announcements = announcements[:max_count]
        
        print(f"总共获取到 {len(announcements)} 条调研公告")
        return announcements
    
    def download_pdf(self, announcement, 
                    stock_info):
        """
        下载单个公告PDF
        
        Args:
            announcement: 公告信息对象
            stock_info: 股票信息对象
            
        Returns:
            保存的文件路径，下载失败返回None
        """
        if not announcement.pdf_url and not announcement.adjunct_url:
            print(f"公告 {announcement.title} 没有PDF链接")
            return None
        
        try:
            # 创建股票目录
            stock_dir = os.path.join(self.download_dir, f"{stock_info.name}_{stock_info.code}")
            os.makedirs(stock_dir, exist_ok=True)
            
            # 清理文件名，避免非法字符
            safe_title = re.sub(r'[\\/:*?"&lt;&gt;|]', '_', announcement.title)
            safe_title = safe_title[:100]  # 限制文件名长度
            
            # 构建文件名
            filename = f"{announcement.announcement_time}_{safe_title}.pdf"
            filepath = os.path.join(stock_dir, filename)
            
            # 如果文件已存在，跳过
            if os.path.exists(filepath):
                print(f"文件已存在，跳过: {filename}")
                return filepath
            
            print(f"正在下载: {announcement.title}")
            
            # 尝试多个URL
            urls_to_try = []
            if announcement.pdf_url:
                urls_to_try.append(announcement.pdf_url)
            if announcement.adjunct_url:
                urls_to_try.append(f"https://www.cninfo.com.cn/{announcement.adjunct_url}")
                urls_to_try.append(f"https://static.cninfo.com.cn/{announcement.adjunct_url}")
            
            response = None
            for url in urls_to_try:
                try:
                    print(f"尝试URL: {url}")
                    self._random_delay()
                    response = self.session.get(url, stream=True, timeout=60)
                    if response.status_code == 200:
                        print(f"成功获取PDF")
                        break
                except Exception as e:
                    print(f"URL失败: {e}")
                    continue
            
            if response is None or response.status_code != 200:
                print(f"所有URL都失败了")
                return None
            
            # 保存文件
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"下载完成: {filename}")
            return filepath
            
        except Exception as e:
            print(f"下载公告失败: {announcement.title}, 错误: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def batch_download(self, query, 
                      announcement_types=None,
                      start_date=None,
                      end_date=None,
                      max_count=10):
        """
        批量下载股票公告
        
        Args:
            query: 股票名称或代码
            announcement_types: 公告类型列表，默认为["latest", "periodic", "research"]
            start_date: 开始日期
            end_date: 结束日期
            max_count: 每种类型最多下载数量
            
        Returns:
            下载结果统计
        """
        if announcement_types is None:
            announcement_types = ["latest", "periodic", "research"]
        
        stats = {
            "stock_name": "",
            "stock_code": "",
            "total": 0,
            "success": 0,
            "failed": 0,
            "files": []
        }
        
        # 搜索股票信息
        stock_info = self.search_stock(query)
        if not stock_info:
            print(f"未找到股票信息: {query}")
            return stats
        
        stats["stock_name"] = stock_info.name
        stats["stock_code"] = stock_info.code
        
        print(f"开始下载 {stock_info.name}({stock_info.code}) 的公告...")
        
        # 下载不同类型的公告
        for ann_type in announcement_types:
            print(f"正在获取 {ann_type} 类型的公告...")
            announcements = self.get_announcements(
                stock_info, ann_type, start_date, end_date, max_count
            )
            
            # 只下载前max_count个
            announcements = announcements[:max_count]
            
            for ann in announcements:
                stats["total"] += 1
                filepath = self.download_pdf(ann, stock_info)
                
                if filepath:
                    stats["success"] += 1
                    stats["files"].append(filepath)
                else:
                    stats["failed"] += 1
        
        print(f"\n下载完成! 成功: {stats['success']}, 失败: {stats['failed']}")
        return stats


def main():
    """示例主函数"""
    downloader = StockDownloader()
    
    # 示例：下载普洛药业的公告
    result = downloader.batch_download(
        query="000739",
        announcement_types=["latest"],
        max_count=2
    )
    
    print(result)


if __name__ == "__main__":
    main()

