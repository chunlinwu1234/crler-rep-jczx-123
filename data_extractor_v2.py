"""
数据提取模块 V2
支持文档语言自动识别和中英文对照输出
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from langdetect import detect, detect_langs

from database_v2 import DatabaseManagerV2, DataRepositoryV2, DBConfig
from market_config import MarketType, get_market_config


@dataclass
class ExtractedData:
    """提取的数据结构（中英文对照）"""
    company_name: str
    company_name_en: Optional[str]
    stock_code: Optional[str]
    report_year: Optional[int]
    report_period: Optional[str]
    report_period_en: Optional[str]
    document_language: str  # 文档语言
    language_confidence: float  # 语言识别置信度
    
    # 财务数据（中英文对照）
    financial_data: Dict[str, Any]  # 包含中文名、英文名、数值
    
    # 业务数据
    business_data: Dict[str, Any]
    
    # 战略信息
    strategic_info: Dict[str, Any]


class LanguageDetector:
    """语言检测器"""
    
    @staticmethod
    def detect_language(text: str) -> Tuple[str, float]:
        """
        检测文本语言
        
        Args:
            text: 文本内容
            
        Returns:
            (语言代码, 置信度)
        """
        try:
            # 限制文本长度
            sample_text = text[:1000] if len(text) > 1000 else text
            
            # 检测语言
            lang = detect(sample_text)
            probs = detect_langs(sample_text)
            confidence = max(p.prob for p in probs)
            
            return lang, confidence
        except Exception as e:
            # 默认中文
            return 'zh', 0.5
    
    @staticmethod
    def is_chinese(text: str) -> bool:
        """判断是否中文"""
        lang, _ = LanguageDetector.detect_language(text)
        return lang == 'zh'
    
    @staticmethod
    def is_english(text: str) -> bool:
        """判断是否英文"""
        lang, _ = LanguageDetector.detect_language(text)
        return lang == 'en'


class DataExtractorV2:
    """数据提取器 V2"""
    
    # 数据提取Prompt模板（支持中英文）
    EXTRACTION_PROMPT_ZH = """【角色定义】
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
5. 输出中英文对照格式

【输出格式】
请严格按照以下JSON格式输出：

```json
{{
  "company_info": {{
    "name": "公司全称（中文）",
    "name_en": "Company Name (English)",
    "stock_code": "股票代码",
    "report_year": 2024,
    "report_period": "年度/半年度/第一季度/第二季度/第三季度",
    "report_period_en": "Annual/Semi-annual/Q1/Q2/Q3"
  }},
  "financial_data": {{
    "total_assets": {{"name": "总资产", "name_en": "Total Assets", "value": 金额, "unit": "元"}},
    "total_liab": {{"name": "总负债", "name_en": "Total Liabilities", "value": 金额, "unit": "元"}},
    "total_equity": {{"name": "股东权益", "name_en": "Total Equity", "value": 金额, "unit": "元"}},
    "total_revenue": {{"name": "营业总收入", "name_en": "Total Revenue", "value": 金额, "unit": "元"}},
    "revenue": {{"name": "营业收入", "name_en": "Revenue", "value": 金额, "unit": "元"}},
    "operate_profit": {{"name": "营业利润", "name_en": "Operating Profit", "value": 金额, "unit": "元"}},
    "n_income": {{"name": "净利润", "name_en": "Net Income", "value": 金额, "unit": "元"}},
    "n_income_attr_p": {{"name": "归母净利润", "name_en": "Net Income Attributable to Parent", "value": 金额, "unit": "元"}},
    "eps": {{"name": "基本每股收益", "name_en": "EPS", "value": 数值, "unit": "元"}},
    "roe": {{"name": "净资产收益率", "name_en": "ROE", "value": 百分比, "unit": "%"}},
    "roa": {{"name": "总资产报酬率", "name_en": "ROA", "value": 百分比, "unit": "%"}},
    "grossprofit_margin": {{"name": "销售毛利率", "name_en": "Gross Profit Margin", "value": 百分比, "unit": "%"}},
    "netprofit_margin": {{"name": "销售净利率", "name_en": "Net Profit Margin", "value": 百分比, "unit": "%"}}
  }},
  "business_data": {{
    "rd_exp": {{"name": "研发费用", "name_en": "R&D Expenses", "value": 金额, "unit": "元"}},
    "employee_count": {{"name": "员工人数", "name_en": "Employee Count", "value": 数量, "unit": "人"}},
    "main_products": {{"name": "主要产品", "name_en": "Main Products", "value": "描述"}}
  }},
  "strategic_info": {{
    "company_mission": {{"name": "公司使命", "name_en": "Mission", "value": "描述"}},
    "company_vision": {{"name": "公司愿景", "name_en": "Vision", "value": "描述"}},
    "core_values": {{"name": "核心价值观", "name_en": "Core Values", "value": "描述"}},
    "key_strategies": {{"name": "关键战略", "name_en": "Key Strategies", "value": "描述"}}
  }}
}}
```

注意：
- 所有金额字段单位为"元"
- 百分比字段直接填写数值（如25.5表示25.5%）
- 文本字段如果未找到填null
- 数值字段如果未找到填null
- 必须同时提供中文和英文名称"""

    EXTRACTION_PROMPT_EN = """【Role】
You are a professional financial data extraction expert, specializing in extracting structured data from annual reports and financial statements.

【Task】
Please extract key financial and business data from the following document content and return it in JSON format.

【Document Content】
{content}

【Requirements】
1. Extract all numerical data as much as possible
2. Convert all amounts to "Yuan" (CNY)
3. Set to null if data not found
4. Ensure accuracy, do not fabricate data
5. Output in bilingual format (Chinese and English)

【Output Format】
Please output strictly in the following JSON format:

```json
{{
  "company_info": {{
    "name": "Company Name (Chinese)",
    "name_en": "Company Name (English)",
    "stock_code": "Stock Code",
    "report_year": 2024,
    "report_period": "Annual/Semi-annual/Q1/Q2/Q3",
    "report_period_en": "Annual/Semi-annual/Q1/Q2/Q3"
  }},
  "financial_data": {{
    "total_assets": {{"name": "总资产", "name_en": "Total Assets", "value": amount, "unit": "CNY"}},
    "total_liab": {{"name": "总负债", "name_en": "Total Liabilities", "value": amount, "unit": "CNY"}},
    "total_equity": {{"name": "股东权益", "name_en": "Total Equity", "value": amount, "unit": "CNY"}},
    "total_revenue": {{"name": "营业总收入", "name_en": "Total Revenue", "value": amount, "unit": "CNY"}},
    "revenue": {{"name": "营业收入", "name_en": "Revenue", "value": amount, "unit": "CNY"}},
    "operate_profit": {{"name": "营业利润", "name_en": "Operating Profit", "value": amount, "unit": "CNY"}},
    "n_income": {{"name": "净利润", "name_en": "Net Income", "value": amount, "unit": "CNY"}},
    "n_income_attr_p": {{"name": "归母净利润", "name_en": "Net Income Attributable to Parent", "value": amount, "unit": "CNY"}},
    "eps": {{"name": "基本每股收益", "name_en": "EPS", "value": value, "unit": "CNY"}},
    "roe": {{"name": "净资产收益率", "name_en": "ROE", "value": percentage, "unit": "%"}},
    "roa": {{"name": "总资产报酬率", "name_en": "ROA", "value": percentage, "unit": "%"}},
    "grossprofit_margin": {{"name": "销售毛利率", "name_en": "Gross Profit Margin", "value": percentage, "unit": "%"}},
    "netprofit_margin": {{"name": "销售净利率", "name_en": "Net Profit Margin", "value": percentage, "unit": "%"}}
  }},
  "business_data": {{
    "rd_exp": {{"name": "研发费用", "name_en": "R&D Expenses", "value": amount, "unit": "CNY"}},
    "employee_count": {{"name": "员工人数", "name_en": "Employee Count", "value": number, "unit": "people"}},
    "main_products": {{"name": "主要产品", "name_en": "Main Products", "value": "description"}}
  }},
  "strategic_info": {{
    "company_mission": {{"name": "公司使命", "name_en": "Mission", "value": "description"}},
    "company_vision": {{"name": "公司愿景", "name_en": "Vision", "value": "description"}},
    "core_values": {{"name": "核心价值观", "name_en": "Core Values", "value": "description"}},
    "key_strategies": {{"name": "关键战略", "name_en": "Key Strategies", "value": "description"}}
  }}
}}
```

Note:
- All amount fields in "CNY"
- Percentage fields as numbers (e.g., 25.5 means 25.5%)
- Set to null if not found
- Must provide both Chinese and English names"""

    def __init__(self, db_manager: DatabaseManagerV2, model_config=None):
        """
        初始化数据提取器
        
        Args:
            db_manager: 数据库管理器
            model_config: AI模型配置
        """
        self.db = db_manager
        self.repo = DataRepositoryV2(db_manager)
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
            提取的数据结构（中英文对照）
        """
        # 1. 检测文档语言
        doc_language, confidence = LanguageDetector.detect_language(content)
        print(f"📄 检测到文档语言: {doc_language} (置信度: {confidence:.2f})")
        
        # 2. 根据语言选择Prompt
        if doc_language == 'en':
            prompt = self.EXTRACTION_PROMPT_EN
        else:
            prompt = self.EXTRACTION_PROMPT_ZH
        
        # 3. 使用AI提取数据
        extracted_json = self._call_ai_for_extraction(content, prompt)
        
        # 4. 解析提取的数据
        data = self._parse_extracted_data(extracted_json)
        
        # 5. 如果提供了公司名称，覆盖AI识别的
        if company_name:
            data['company_info']['name'] = company_name
        
        # 6. 构建提取结果
        result = ExtractedData(
            company_name=data['company_info'].get('name'),
            company_name_en=data['company_info'].get('name_en'),
            stock_code=data['company_info'].get('stock_code'),
            report_year=data['company_info'].get('report_year'),
            report_period=data['company_info'].get('report_period'),
            report_period_en=data['company_info'].get('report_period_en'),
            document_language=doc_language,
            language_confidence=confidence,
            financial_data=data.get('financial_data', {}),
            business_data=data.get('business_data', {}),
            strategic_info=data.get('strategic_info', {})
        )
        
        return result
    
    def _call_ai_for_extraction(self, content: str, prompt_template: str) -> str:
        """调用AI模型提取数据"""
        # 限制内容长度
        max_length = 15000
        if len(content) > max_length:
            content = content[:max_length] + "\n...[Content Truncated]"
        
        prompt = prompt_template.format(content=content)
        
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
            return self._mock_extraction()
    
    def _mock_extraction(self) -> str:
        """模拟数据提取（用于测试）"""
        return json.dumps({
            "company_info": {
                "name": "示例公司",
                "name_en": "Example Company",
                "stock_code": None,
                "report_year": datetime.now().year,
                "report_period": "年度",
                "report_period_en": "Annual"
            },
            "financial_data": {},
            "business_data": {},
            "strategic_info": {}
        }, ensure_ascii=False, indent=2)
    
    def _parse_extracted_data(self, json_text: str) -> Dict:
        """解析AI返回的JSON数据"""
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
                symbol=extracted_data.stock_code or "UNKNOWN",
                name=extracted_data.company_name or "未知公司",
                name_en=extracted_data.company_name_en,
                market="a_share"  # 默认A股，可根据需要调整
            )
            
            # 2. 准备财务数据（提取value字段）
            financial_data = {}
            for key, value_obj in extracted_data.financial_data.items():
                if isinstance(value_obj, dict):
                    financial_data[key] = value_obj.get('value')
                else:
                    financial_data[key] = value_obj
            
            # 添加报告期信息
            financial_data['report_date'] = f"{extracted_data.report_year}-12-31" if extracted_data.report_year else None
            financial_data['report_type'] = 'annual'
            financial_data['extended_data'] = json.dumps({
                'financial_data': extracted_data.financial_data,
                'business_data': extracted_data.business_data,
                'strategic_info': extracted_data.strategic_info
            }, ensure_ascii=False)
            
            # 3. 保存财务数据
            self.repo.save_financial_report(company_id, financial_data)
            
            print(f"✅ 数据已保存到数据库，公司ID: {company_id}")
            return True
            
        except Exception as e:
            print(f"❌ 保存数据失败: {e}")
            return False
    
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


class DataQueryHelperV2:
    """数据查询助手 V2"""
    
    def __init__(self, db_manager: DatabaseManagerV2):
        self.db = db_manager
        self.repo = DataRepositoryV2(db_manager)
    
    def get_company_data_summary(self, company_name: str, language: str = 'zh') -> str:
        """
        获取公司数据摘要
        
        Args:
            company_name: 公司名称
            language: 输出语言(zh/en)
            
        Returns:
            数据摘要文本
        """
        company = self.repo.get_company(name=company_name)
        if not company:
            return f"{'Database' if language == 'en' else '数据库'}中未找到公司 '{company_name}' 的数据。"
        
        company_id = company['id']
        
        # 获取最新财务数据
        reports = self.repo.get_financial_reports(company_id)
        
        if language == 'en':
            return self._format_summary_en(company, reports)
        else:
            return self._format_summary_zh(company, reports)
    
    def _format_summary_zh(self, company: Dict, reports: List[Dict]) -> str:
        """格式化中文摘要"""
        summary = f"【{company['name']} 数据摘要】\n\n"
        summary += f"股票代码: {company.get('symbol', 'N/A')}\n"
        summary += f"市场: {company.get('market', 'N/A')}\n"
        summary += f"行业: {company.get('industry', 'N/A')}\n\n"
        
        if reports:
            latest = reports[0]
            summary += "【最新财务数据】\n"
            summary += f"报告期: {latest.get('report_date', 'N/A')}\n"
            summary += f"营业收入: {self._format_amount(latest.get('total_revenue'))}\n"
            summary += f"净利润: {self._format_amount(latest.get('n_income_attr_p'))}\n"
            summary += f"总资产: {self._format_amount(latest.get('total_assets'))}\n"
            summary += f"ROE: {latest.get('roe', 'N/A')}%\n"
        
        return summary
    
    def _format_summary_en(self, company: Dict, reports: List[Dict]) -> str:
        """格式化英文摘要"""
        summary = f"【{company.get('name_en', company['name'])} Data Summary】\n\n"
        summary += f"Stock Code: {company.get('symbol', 'N/A')}\n"
        summary += f"Market: {company.get('market', 'N/A')}\n"
        summary += f"Industry: {company.get('industry_en', company.get('industry', 'N/A'))}\n\n"
        
        if reports:
            latest = reports[0]
            summary += "【Latest Financial Data】\n"
            summary += f"Report Date: {latest.get('report_date', 'N/A')}\n"
            summary += f"Revenue: {self._format_amount(latest.get('total_revenue'))}\n"
            summary += f"Net Income: {self._format_amount(latest.get('n_income_attr_p'))}\n"
            summary += f"Total Assets: {self._format_amount(latest.get('total_assets'))}\n"
            summary += f"ROE: {latest.get('roe', 'N/A')}%\n"
        
        return summary
    
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
                                 password: str = 'root', model_config=None) -> DataExtractorV2:
    """使用配置创建数据提取器"""
    config = DBConfig(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    
    db_manager = DatabaseManagerV2(config)
    return DataExtractorV2(db_manager, model_config)


if __name__ == "__main__":
    # 测试代码
    print("数据提取模块 V2 测试")
    print("-" * 50)
    
    # 测试语言检测
    test_texts = [
        "普洛药业股份有限公司 2024年年度报告",
        "Pfizer Inc. Annual Report 2024",
        "ロシュ株式会社 有価証券報告書"
    ]
    
    for text in test_texts:
        lang, conf = LanguageDetector.detect_language(text)
        print(f"文本: {text[:30]}... -> 语言: {lang}, 置信度: {conf:.2f}")
