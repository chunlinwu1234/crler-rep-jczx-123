"""
结构化数据提取模块
使用AI从文档中提取结构化数据并存储到数据库
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from database import DatabaseManager, DataRepository, DBConfig


@dataclass
class ExtractedData:
    """提取的数据结构"""
    company_name: str
    stock_code: Optional[str]
    report_year: Optional[int]
    report_period: Optional[str]
    financial_data: Dict
    business_data: Dict
    strategic_info: Dict


class DataExtractor:
    """数据提取器"""
    
    # 数据提取Prompt模板
    EXTRACTION_PROMPT = """【角色定义】
你是一位专业的财务数据提取专家，擅长从企业年报、财务报表中提取结构化数据。

【任务描述】
请从以下文档内容中提取关键财务和业务数据，并以JSON格式返回。

【文档内容】
{content}

【提取要求】
1. 尽可能提取所有数值型数据
2. 金额单位统一转换为"元"
3. 如果某项数据在文档中未找到，设为null
4. 确保数值准确，不要编造数据

【输出格式】
请严格按照以下JSON格式输出：

```json
{{
  "company_info": {{
    "name": "公司全称",
    "stock_code": "股票代码",
    "report_year": 2024,
    "report_period": "年度/半年度/第一季度/第二季度/第三季度"
  }},
  "financial_data": {{
    "revenue": 营业收入,
    "operating_cost": 营业成本,
    "gross_profit": 毛利润,
    "operating_profit": 营业利润,
    "net_profit": 净利润,
    "net_profit_parent": 归母净利润,
    "total_assets": 总资产,
    "total_liabilities": 总负债,
    "equity": 股东权益,
    "current_assets": 流动资产,
    "current_liabilities": 流动负债,
    "inventory": 存货,
    "accounts_receivable": 应收账款,
    "operating_cash_flow": 经营活动现金流,
    "investing_cash_flow": 投资活动现金流,
    "financing_cash_flow": 筹资活动现金流,
    "gross_margin": 毛利率百分比,
    "net_margin": 净利率百分比,
    "roe": ROE百分比,
    "roa": ROA百分比,
    "debt_ratio": 资产负债率百分比,
    "current_ratio": 流动比率
  }},
  "business_data": {{
    "r_d_investment": 研发投入,
    "r_d_expense": 研发费用,
    "r_d_capitalized": 研发资本化金额,
    "r_d_intensity": 研发强度百分比,
    "employee_count": 员工人数,
    "r_d_personnel": 研发人员数量,
    "production_capacity": "产能情况描述",
    "capacity_utilization": 产能利用率百分比,
    "market_share": 市场份额百分比,
    "domestic_revenue": 国内收入,
    "overseas_revenue": 海外收入,
    "main_products": "主要产品描述",
    "new_products": "新产品描述"
  }},
  "strategic_info": {{
    "company_mission": "公司使命",
    "company_vision": "公司愿景",
    "core_values": "核心价值观",
    "strategic_goals": "战略目标",
    "key_strategies": "关键战略举措",
    "strengths": "优势分析",
    "weaknesses": "劣势分析",
    "opportunities": "机会分析",
    "threats": "威胁分析",
    "business_model": "商业模式描述",
    "value_proposition": "价值主张",
    "customer_segments": "客户细分",
    "revenue_streams": "收入来源"
  }}
}}
```

注意：
- 所有金额字段单位为"元"
- 百分比字段直接填写数值（如25.5表示25.5%）
- 文本字段如果未找到填null
- 数值字段如果未找到填null"""
    
    def __init__(self, db_manager: DatabaseManager, model_config=None):
        """
        初始化数据提取器
        
        Args:
            db_manager: 数据库管理器
            model_config: AI模型配置
        """
        self.db = db_manager
        self.repo = DataRepository(db_manager)
        self.model_config = model_config
    
    def extract_from_document(self, file_path: str, content: str, 
                             company_name: str = None) -> ExtractedData:
        """
        从文档内容中提取结构化数据
        
        Args:
            file_path: 文件路径
            content: 文档内容
            company_name: 公司名称（可选）
            
        Returns:
            提取的数据结构
        """
        # 使用AI提取数据
        extracted_json = self._call_ai_for_extraction(content)
        
        # 解析提取的数据
        data = self._parse_extracted_data(extracted_json)
        
        # 如果提供了公司名称，覆盖AI识别的
        if company_name:
            data['company_info']['name'] = company_name
        
        # 构建提取结果
        result = ExtractedData(
            company_name=data['company_info'].get('name'),
            stock_code=data['company_info'].get('stock_code'),
            report_year=data['company_info'].get('report_year'),
            report_period=data['company_info'].get('report_period'),
            financial_data=data.get('financial_data', {}),
            business_data=data.get('business_data', {}),
            strategic_info=data.get('strategic_info', {})
        )
        
        return result
    
    def _call_ai_for_extraction(self, content: str) -> str:
        """
        调用AI模型提取数据
        
        Args:
            content: 文档内容
            
        Returns:
            AI返回的JSON字符串
        """
        # 限制内容长度，避免超出模型限制
        max_length = 15000
        if len(content) > max_length:
            content = content[:max_length] + "\n...[内容截断]"
        
        prompt = self.EXTRACTION_PROMPT.format(content=content)
        
        # 如果有模型配置，使用配置调用AI
        if self.model_config:
            try:
                from ai_analyzer import AIAnalyzer
                analyzer = AIAnalyzer(self.model_config)
                result, _ = analyzer._call_model(prompt)
                return result
            except Exception as e:
                print(f"AI提取失败: {e}")
                return self._mock_extraction()
        else:
            # 模拟提取（用于测试）
            return self._mock_extraction()
    
    def _mock_extraction(self) -> str:
        """模拟数据提取（用于测试）"""
        return json.dumps({
            "company_info": {
                "name": "示例公司",
                "stock_code": None,
                "report_year": datetime.now().year,
                "report_period": "年度"
            },
            "financial_data": {},
            "business_data": {},
            "strategic_info": {}
        }, ensure_ascii=False, indent=2)
    
    def _parse_extracted_data(self, json_text: str) -> Dict:
        """
        解析AI返回的JSON数据
        
        Args:
            json_text: JSON文本
            
        Returns:
            解析后的数据字典
        """
        # 提取JSON代码块
        json_match = re.search(r'```json\s*(.*?)\s*```', json_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        
        try:
            data = json.loads(json_text.strip())
            return data
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            return {
                "company_info": {},
                "financial_data": {},
                "business_data": {},
                "strategic_info": {}
            }
    
    def save_to_database(self, extracted_data: ExtractedData, 
                        file_path: str, file_name: str) -> bool:
        """
        将提取的数据保存到数据库
        
        Args:
            extracted_data: 提取的数据
            file_path: 文件路径
            file_name: 文件名
            
        Returns:
            是否成功
        """
        try:
            # 1. 创建或获取公司记录
            company_id = self.repo.create_company(
                name=extracted_data.company_name or "未知公司",
                stock_code=extracted_data.stock_code
            )
            
            # 2. 创建文档记录
            doc_type = self._detect_doc_type(file_name)
            document_id = self.repo.create_document(
                company_id=company_id,
                file_name=file_name,
                file_path=file_path,
                doc_type=doc_type,
                report_year=extracted_data.report_year,
                report_period=extracted_data.report_period
            )
            
            # 3. 保存财务数据
            if extracted_data.financial_data:
                financial_data = extracted_data.financial_data.copy()
                financial_data['report_year'] = extracted_data.report_year
                self.repo.save_financial_data(company_id, financial_data, document_id)
            
            # 4. 保存业务数据
            if extracted_data.business_data:
                business_data = extracted_data.business_data.copy()
                business_data['report_year'] = extracted_data.report_year
                self.repo.save_business_data(company_id, business_data, document_id)
            
            # 5. 保存战略信息
            if extracted_data.strategic_info:
                strategic_data = extracted_data.strategic_info.copy()
                if extracted_data.report_year:
                    strategic_data['report_date'] = f"{extracted_data.report_year}-12-31"
                self.repo.save_strategic_info(company_id, strategic_data, document_id)
            
            # 6. 更新文档提取状态
            self.repo.update_document_extracted(document_id, True)
            
            print(f"✅ 数据已保存到数据库，公司ID: {company_id}, 文档ID: {document_id}")
            return True
            
        except Exception as e:
            print(f"❌ 保存数据失败: {e}")
            return False
    
    def _detect_doc_type(self, file_name: str) -> str:
        """
        检测文档类型
        
        Args:
            file_name: 文件名
            
        Returns:
            文档类型
        """
        file_name_lower = file_name.lower()
        
        if '年报' in file_name or '年度报告' in file_name:
            return '年报'
        elif '半年报' in file_name or '半年度' in file_name:
            return '半年报'
        elif '季报' in file_name or '季度' in file_name:
            if '一' in file_name or '1' in file_name:
                return '第一季度季报'
            elif '二' in file_name or '2' in file_name:
                return '第二季度季报'
            elif '三' in file_name or '3' in file_name:
                return '第三季度季报'
            else:
                return '季报'
        elif '公告' in file_name:
            return '公告'
        else:
            return '其他'
    
    def extract_and_save(self, file_path: str, content: str, 
                        company_name: str = None) -> Tuple[bool, ExtractedData]:
        """
        提取数据并保存到数据库
        
        Args:
            file_path: 文件路径
            content: 文档内容
            company_name: 公司名称
            
        Returns:
            (是否成功, 提取的数据)
        """
        # 提取数据
        extracted_data = self.extract_from_document(file_path, content, company_name)
        
        # 保存到数据库
        file_name = os.path.basename(file_path)
        success = self.save_to_database(extracted_data, file_path, file_name)
        
        return success, extracted_data
    
    def get_company_financial_history(self, company_id: int, 
                                     metrics: List[str] = None) -> Dict:
        """
        获取公司财务历史数据
        
        Args:
            company_id: 公司ID
            metrics: 指标列表，默认为常用指标
            
        Returns:
            历史数据字典
        """
        if metrics is None:
            metrics = ['revenue', 'net_profit', 'total_assets', 'roe']
        
        return self.repo.get_financial_metrics(company_id, metrics)
    
    def compare_companies(self, company_ids: List[int], metric: str, 
                         year: int = None) -> List[Dict]:
        """
        对比多家公司的某项指标
        
        Args:
            company_ids: 公司ID列表
            metric: 指标名称
            year: 年份
            
        Returns:
            对比结果
        """
        return self.repo.compare_companies(company_ids, metric, year)


class DataQueryHelper:
    """数据查询助手，为AI分析提供数据支持"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化查询助手
        
        Args:
            db_manager: 数据库管理器
        """
        self.db = db_manager
        self.repo = DataRepository(db_manager)
    
    def get_company_data_summary(self, company_name: str) -> str:
        """
        获取公司数据摘要，用于AI分析
        
        Args:
            company_name: 公司名称
            
        Returns:
            数据摘要文本
        """
        company = self.repo.get_company(name=company_name)
        if not company:
            return f"数据库中未找到公司 '{company_name}' 的数据。"
        
        company_id = company['id']
        
        # 获取最新财务数据
        financial_data = self.repo.get_financial_data(company_id)
        
        # 获取业务数据
        business_data = self.repo.get_business_data(company_id)
        
        # 获取战略信息
        strategic_info = self.repo.get_strategic_info(company_id)
        
        # 构建摘要
        summary = f"【{company_name} 数据摘要】\n\n"
        
        # 公司基本信息
        summary += f"股票代码: {company.get('stock_code', 'N/A')}\n"
        summary += f"所属行业: {company.get('industry', 'N/A')}\n\n"
        
        # 最新财务数据
        if financial_data:
            latest = financial_data[-1]  # 最新数据
            summary += "【最新财务数据】\n"
            summary += f"报告期: {latest.get('report_year', 'N/A')}年\n"
            summary += f"营业收入: {self._format_amount(latest.get('revenue'))}\n"
            summary += f"净利润: {self._format_amount(latest.get('net_profit'))}\n"
            summary += f"总资产: {self._format_amount(latest.get('total_assets'))}\n"
            summary += f"ROE: {latest.get('roe', 'N/A')}%\n"
            summary += f"毛利率: {latest.get('gross_margin', 'N/A')}%\n\n"
        
        # 业务数据
        if business_data:
            latest_business = business_data[-1]
            summary += "【业务数据】\n"
            summary += f"研发投入: {self._format_amount(latest_business.get('r_d_investment'))}\n"
            summary += f"研发强度: {latest_business.get('r_d_intensity', 'N/A')}%\n"
            summary += f"员工人数: {latest_business.get('employee_count', 'N/A')}\n\n"
        
        # 战略信息
        if strategic_info:
            summary += "【战略信息】\n"
            if strategic_info.get('company_mission'):
                summary += f"使命: {strategic_info['company_mission']}\n"
            if strategic_info.get('company_vision'):
                summary += f"愿景: {strategic_info['company_vision']}\n"
            if strategic_info.get('key_strategies'):
                summary += f"关键战略: {strategic_info['key_strategies']}\n"
        
        return summary
    
    def get_financial_trend(self, company_name: str, years: int = 5) -> str:
        """
        获取财务趋势数据
        
        Args:
            company_name: 公司名称
            years: 查询年数
            
        Returns:
            趋势数据文本
        """
        company = self.repo.get_company(name=company_name)
        if not company:
            return ""
        
        metrics = self.repo.get_financial_metrics(
            company['id'], 
            ['revenue', 'net_profit', 'gross_margin', 'roe'],
            years
        )
        
        if not metrics.get('years'):
            return ""
        
        trend_text = f"【{company_name} 近{len(metrics['years'])}年财务趋势】\n\n"
        trend_text += "年份 | 营业收入(亿元) | 净利润(亿元) | 毛利率(%) | ROE(%)\n"
        trend_text += "-" * 60 + "\n"
        
        for i, year in enumerate(metrics['years']):
            revenue = metrics['revenue'][i] / 1e8 if metrics['revenue'][i] else 0
            profit = metrics['net_profit'][i] / 1e8 if metrics['net_profit'][i] else 0
            margin = metrics['gross_margin'][i] or 0
            roe = metrics['roe'][i] or 0
            
            trend_text += f"{year} | {revenue:.2f} | {profit:.2f} | {margin:.2f} | {roe:.2f}\n"
        
        return trend_text
    
    def _format_amount(self, amount) -> str:
        """格式化金额"""
        if amount is None:
            return "N/A"
        
        if amount >= 1e8:
            return f"{amount/1e8:.2f}亿元"
        elif amount >= 1e4:
            return f"{amount/1e4:.2f}万元"
        else:
            return f"{amount:.2f}元"


def create_extractor_with_config(host: str = 'localhost', port: int = 3306,
                                 database: str = 'cims_db', user: str = 'root',
                                 password: str = 'root', model_config=None) -> DataExtractor:
    """
    使用配置创建数据提取器
    
    Args:
        host: 主机地址
        port: 端口号
        database: 数据库名
        user: 用户名
        password: 密码
        model_config: AI模型配置
        
    Returns:
        数据提取器实例
    """
    config = DBConfig(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
    db_manager = DatabaseManager(config)
    return DataExtractor(db_manager, model_config)


if __name__ == "__main__":
    # 测试代码
    print("数据提取模块测试")
    print("-" * 50)
    
    # 创建提取器
    extractor = create_extractor_with_config(
        host='localhost',
        port=3306,
        database='cims_db',
        user='root',
        password='root'
    )
    
    # 测试数据提取
    test_content = """
    普洛药业股份有限公司 2024年年度报告
    
    一、主要会计数据和财务指标
    营业收入：12,085,634,123.45元
    归属于上市公司股东的净利润：1,056,789,234.56元
    总资产：15,678,901,234.56元
    净资产收益率(ROE)：12.34%
    
    二、研发投入
    研发投入金额：567,890,123.45元
    研发投入占营业收入比例：4.70%
    研发人员数量：1,234人
    """
    
    result = extractor.extract_from_document(
        file_path="test.pdf",
        content=test_content,
        company_name="普洛药业"
    )
    
    print(f"提取结果:")
    print(f"  公司名称: {result.company_name}")
    print(f"  股票代码: {result.stock_code}")
    print(f"  报告年份: {result.report_year}")
    print(f"  财务数据: {result.financial_data}")
