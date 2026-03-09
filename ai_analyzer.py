"""
AI分析模块
负责PDF解析、多模型调用（Ollama本地/DeepSeek/通义千问）、向量数据库存储和八大维度分析
"""
import os
import sys
import json
import PyPDF2
from docx import Document
import chromadb
from chromadb.config import Settings
from datetime import datetime
from typing import Optional, Dict, Any, List

# 添加项目根目录到路径以导入config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config


class PromptConfig:
    """Prompt配置管理类"""
    
    # 默认Prompt模板
    DEFAULT_TEMPLATES = {
        "base": """【角色定义】
你是一位资深的医药行业战略分析师，擅长从企业公告、年报中提取竞争情报。

【任务描述】
请根据以下文档内容，对{company_name}进行{analysis_depth}深度的{analysis_dimension}分析。

【文档内容】
{content}

【分析维度】
{analysis_dimension}

【分析深度】
{analysis_depth}

【输出要求】
1. 结构化输出，使用Markdown格式
2. 包含定量数据和定性分析
3. 识别关键趋势和潜在风险
4. 输出语言：中文
5. 分析要基于文档内容，不要凭空猜测
6. **重要：在分析中如涉及可量化的对比数据，请在报告末尾提供图表数据（JSON格式），用于生成可视化图表**

【输出格式】
请按照以下格式输出：

# {company_name} {analysis_dimension}分析报告

## 一、分析摘要
[200字以内的分析概况]

## 二、详细分析
[根据分析维度和深度的具体内容]

## 三、关键发现
[3-5个关键发现]

## 四、风险与机会
[识别主要风险和机会]

## 五、建议
[基于分析结果的建议]

## 六、图表数据（可选）
如果分析中包含可量化的对比数据，请在此部分提供JSON格式的图表数据，格式如下：

```json
{
  "chart_type": "bar|line|pie|radar",
  "chart_title": "图表标题",
  "labels": ["标签1", "标签2", ...],
  "datasets": [
    {
      "label": "数据系列名称",
      "data": [数值1, 数值2, ...]
    }
  ]
}
```

支持的图表类型：
- bar: 柱状图（适合对比数据）
- line: 折线图（适合趋势数据）
- pie: 饼图（适合占比数据）
- radar: 雷达图（适合多维评估）""",
        
        "战略分析": """【战略分析重点】
- 识别公司使命、愿景、战略目标
- 分析关键战略举措
- 进行SWOT分析
- 识别战略演变趋势""",
        
        "商业模式": """【商业模式分析重点】
- 填充9宫格画布（客户细分、价值主张、渠道、客户关系、收入来源、核心资源、关键业务、重要合作、成本结构）
- 识别商业模式类型
- 分析创新点和差异化
- 评估可持续性和风险""",
        
        "资源能力": """【资源能力分析重点】
- 盘点技术、生产、人力、资质、供应链、渠道、品牌等资源
- 定量统计与定性评估相结合
- 识别核心能力和资源缺口
- 进行同业对比分析""",
        
        "财务分析": """【财务分析重点】
- 分析营收、利润、现金流等核心指标
- 识别财务趋势和异常
- 评估财务健康度
- 对比行业平均水平""",
        
        "前景分析": """【前景分析重点】
- 分析行业发展趋势
- 评估公司增长潜力
- 识别未来机遇和挑战
- 预测未来3-5年发展""",
        
        "发展历程": """【发展历程分析重点】
- 梳理公司发展里程碑
- 分析发展阶段特征
- 识别关键转折点
- 总结发展规律""",
        
        "股权/子公司": """【股权/子公司分析重点】
- 分析股权结构
- 梳理子公司布局
- 识别关联交易
- 评估治理结构""",
        
        "企业文化": """【企业文化分析重点】
- 识别核心价值观
- 分析文化特征
- 评估文化落地情况
- 对比行业文化差异"""
    }
    
    def __init__(self, config_file=None):
        """初始化Prompt配置
        
        Args:
            config_file: 配置文件路径，默认使用项目目录下的prompt_config.json
        """
        if config_file is None:
            config_file = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "prompt_config.json"
            )
        self.config_file = config_file
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, str]:
        """加载Prompt模板
        
        Returns:
            模板字典
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_templates = json.load(f)
                    # 合并保存的模板和默认模板
                    templates = self.DEFAULT_TEMPLATES.copy()
                    templates.update(saved_templates)
                    return templates
            except Exception as e:
                print(f"加载Prompt配置失败: {e}，使用默认配置")
                return self.DEFAULT_TEMPLATES.copy()
        return self.DEFAULT_TEMPLATES.copy()
    
    def save_templates(self):
        """保存模板到配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.templates, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存Prompt配置失败: {e}")
            return False
    
    def get_template(self, template_name: str) -> str:
        """获取指定模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            模板内容
        """
        return self.templates.get(template_name, self.DEFAULT_TEMPLATES.get(template_name, ""))
    
    def set_template(self, template_name: str, content: str):
        """设置模板内容
        
        Args:
            template_name: 模板名称
            content: 模板内容
        """
        self.templates[template_name] = content
    
    def reset_template(self, template_name: str):
        """重置模板为默认值
        
        Args:
            template_name: 模板名称
        """
        if template_name in self.DEFAULT_TEMPLATES:
            self.templates[template_name] = self.DEFAULT_TEMPLATES[template_name]
    
    def reset_all_templates(self):
        """重置所有模板为默认值"""
        self.templates = self.DEFAULT_TEMPLATES.copy()
    
    def generate_prompt(self, company_name: str, analysis_dimension: str, 
                       analysis_depth: str, content: str) -> str:
        """生成完整的分析Prompt
        
        Args:
            company_name: 公司名称
            analysis_dimension: 分析维度
            analysis_depth: 分析深度
            content: 文档内容
            
        Returns:
            完整的Prompt
        """
        # 获取基础模板
        base_template = self.get_template("base")
        
        # 获取维度特定的补充模板
        dimension_template = self.get_template(analysis_dimension)
        
        # 截取内容（避免超过模型限制）
        max_content_length = getattr(config, 'MAX_DOCUMENT_LENGTH', 15000)
        if len(content) > max_content_length:
            content = content[:max_content_length] + "\n...（内容过长，已截断）"
        
        # 填充基础模板
        prompt = base_template.format(
            company_name=company_name,
            analysis_dimension=analysis_dimension,
            analysis_depth=analysis_depth,
            content=content
        )
        
        # 添加维度特定的补充内容
        if dimension_template:
            prompt += "\n" + dimension_template
        
        return prompt
    
    def list_templates(self) -> List[str]:
        """列出所有可用的模板名称
        
        Returns:
            模板名称列表
        """
        return list(self.templates.keys())


class ModelConfig:
    """模型配置类"""
    
    def __init__(self):
        """初始化模型配置"""
        # 默认使用Ollama本地模型
        self.provider: str = "ollama"  # 可选: ollama, deepseek, qwen
        
        # Ollama配置
        self.ollama_host: str = getattr(config, 'OLLAMA_HOST', 'http://localhost:11434')
        self.ollama_model: str = getattr(config, 'OLLAMA_MODEL', 'qwen2.5:7b')
        
        # DeepSeek配置
        self.deepseek_api_key: str = ""
        self.deepseek_model: str = "deepseek-chat"  # 或 deepseek-reasoner
        
        # 通义千问配置
        self.qwen_api_key: str = ""
        self.qwen_model: str = "qwen-turbo"  # 可选: qwen-turbo, qwen-plus, qwen-max
        
        # 通用参数
        self.temperature: float = getattr(config, 'OLLAMA_TEMPERATURE', 0.3)
        self.max_tokens: int = getattr(config, 'OLLAMA_MAX_TOKENS', 4096)
        self.timeout: int = getattr(config, 'OLLAMA_TIMEOUT', 300)


class DocumentParser:
    """文档解析类"""
    
    @staticmethod
    def parse_pdf(pdf_path):
        """解析PDF文件
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            解析后的文本内容
        """
        try:
            with open(pdf_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"解析PDF失败: {e}")
            return ""
    
    @staticmethod
    def parse_docx(docx_path):
        """解析Word文件
        
        Args:
            docx_path: Word文件路径
            
        Returns:
            解析后的文本内容
        """
        try:
            doc = Document(docx_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            print(f"解析Word失败: {e}")
            return ""
    
    @staticmethod
    def parse_file(file_path):
        """根据文件扩展名自动选择解析方法
        
        Args:
            file_path: 文件路径
            
        Returns:
            解析后的文本内容
        """
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            return DocumentParser.parse_pdf(file_path)
        elif ext == '.docx':
            return DocumentParser.parse_docx(file_path)
        elif ext == '.txt':
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except:
                try:
                    with open(file_path, 'r', encoding='gbk') as f:
                        return f.read()
                except Exception as e:
                    print(f"解析TXT失败: {e}")
                    return ""
        else:
            return ""


class VectorStore:
    """向量存储类"""
    
    def __init__(self, persist_dir=None):
        """初始化向量存储
        
        Args:
            persist_dir: 持久化目录，默认使用config中的配置
        """
        if persist_dir is None:
            persist_dir = getattr(config, 'VECTOR_STORE_DIR', 
                                 os.path.join(os.path.dirname(__file__), "vector_store"))
        os.makedirs(persist_dir, exist_ok=True)
        
        # 使用新的Chroma客户端初始化方式
        from chromadb.config import Settings
        self.client = chromadb.PersistentClient(
            path=persist_dir
        )
        self.collection = self.client.get_or_create_collection("cims_documents")
    
    def add_document(self, doc_id, content, metadata):
        """添加文档到向量存储
        
        Args:
            doc_id: 文档ID
            content: 文档内容
            metadata: 元数据
        """
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            return True
        except Exception as e:
            print(f"添加文档到向量存储失败: {e}")
            return False
    
    def query(self, query_text, n_results=3):
        """查询相关文档
        
        Args:
            query_text: 查询文本
            n_results: 返回结果数量
            
        Returns:
            查询结果
        """
        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return results
        except Exception as e:
            print(f"查询向量存储失败: {e}")
            return {"documents": [[""], [""], [""]], "metadatas": [[{}], [{}], [{}]]}


class AIAnalyzer:
    """AI分析器类"""

    def __init__(self, vector_store=None, model_config: Optional[ModelConfig] = None, prompt_config: Optional[PromptConfig] = None):
        """初始化AI分析器

        Args:
            vector_store: 向量存储实例
            model_config: 模型配置实例
            prompt_config: Prompt配置实例
        """
        self.vector_store = vector_store or VectorStore()
        self.parser = DocumentParser()
        self.model_config = model_config or ModelConfig()
        self.prompt_config = prompt_config or PromptConfig()

        # 验证模型配置
        self._validate_config()
    
    def _validate_config(self):
        """验证模型配置"""
        provider = self.model_config.provider
        
        if provider == "ollama":
            # 设置Ollama环境变量
            os.environ['OLLAMA_HOST'] = self.model_config.ollama_host
        elif provider == "deepseek":
            if not self.model_config.deepseek_api_key:
                raise ValueError("使用DeepSeek需要提供API Key")
        elif provider == "qwen":
            if not self.model_config.qwen_api_key:
                raise ValueError("使用通义千问需要提供API Key")
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
    
    def _call_ollama(self, prompt: str) -> tuple:
        """调用Ollama本地模型
        
        Args:
            prompt: 提示词
            
        Returns:
            (模型响应文本, token使用情况字典)
        """
        import ollama
        
        response = ollama.generate(
            model=self.model_config.ollama_model,
            prompt=prompt,
            options={
                "temperature": self.model_config.temperature,
                "num_predict": self.model_config.max_tokens
            }
        )
        
        # 提取token使用情况（Ollama可能不返回精确的token数，使用估算）
        usage = {
            "prompt_tokens": len(prompt) // 4,  # 粗略估算
            "completion_tokens": len(response["response"]) // 4,
            "total_tokens": (len(prompt) + len(response["response"])) // 4
        }
        
        return response["response"], usage
    
    def _call_deepseek(self, prompt: str) -> tuple:
        """调用DeepSeek云服务
        
        Args:
            prompt: 提示词
            
        Returns:
            (模型响应文本, token使用情况字典)
        """
        import requests
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.model_config.deepseek_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model_config.deepseek_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.model_config.temperature,
            "max_tokens": self.model_config.max_tokens
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=self.model_config.timeout)
        response.raise_for_status()
        result = response.json()
        
        # 提取token使用情况
        usage = result.get("usage", {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        })
        
        return result["choices"][0]["message"]["content"], usage
    
    def _call_qwen(self, prompt: str) -> tuple:
        """调用通义千问云服务
        
        Args:
            prompt: 提示词
            
        Returns:
            (模型响应文本, token使用情况字典)
        """
        import requests
        
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        headers = {
            "Authorization": f"Bearer {self.model_config.qwen_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model_config.qwen_model,
            "input": {
                "messages": [{"role": "user", "content": prompt}]
            },
            "parameters": {
                "temperature": self.model_config.temperature,
                "max_tokens": self.model_config.max_tokens,
                "result_format": "message"
            }
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=self.model_config.timeout)
        response.raise_for_status()
        result = response.json()
        
        if "output" in result and "choices" in result["output"]:
            content = result["output"]["choices"][0]["message"]["content"]
            
            # 提取token使用情况（通义千问API格式）
            usage = result.get("usage", {})
            token_usage = {
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            }
            
            return content, token_usage
        else:
            raise ValueError(f"通义千问API返回异常: {result}")
    
    def _call_model(self, prompt: str) -> tuple:
        """根据配置的提供商调用相应的模型
        
        Args:
            prompt: 提示词
            
        Returns:
            (模型响应文本, token使用情况字典)
        """
        provider = self.model_config.provider
        
        if provider == "ollama":
            return self._call_ollama(prompt)
        elif provider == "deepseek":
            return self._call_deepseek(prompt)
        elif provider == "qwen":
            return self._call_qwen(prompt)
        else:
            raise ValueError(f"不支持的模型提供商: {provider}")
    
    def analyze_document(self, file_path, company_name, analysis_dimension, analysis_depth="中层"):
        """分析文档
        
        Args:
            file_path: 文件路径
            company_name: 公司名称
            analysis_dimension: 分析维度
            analysis_depth: 分析深度（浅层/中层/深层）
            
        Returns:
            分析结果（包含token使用情况）
        """
        import time
        
        start_time = time.time()
        
        # 解析文档
        content = self.parser.parse_file(file_path)
        if not content:
            return {"error": "文档解析失败"}
        
        # 添加到向量存储
        doc_id = f"{company_name}_{os.path.basename(file_path)}_{datetime.now().timestamp()}"
        metadata = {
            "company": company_name,
            "file_name": os.path.basename(file_path),
            "analysis_dimension": analysis_dimension,
            "analysis_depth": analysis_depth,
            "timestamp": datetime.now().isoformat()
        }
        self.vector_store.add_document(doc_id, content, metadata)
        
        # 生成Prompt
        prompt = self._generate_prompt(company_name, analysis_dimension, analysis_depth, content)
        
        # 调用AI模型
        try:
            print(f"🤖 使用 {self.model_config.provider} 模型进行分析...")
            result_text, token_usage = self._call_model(prompt)
            
            end_time = time.time()
            analysis_time = end_time - start_time
            
            # 提取图表数据
            chart_data = self._extract_chart_data(result_text)

            # 保存分析结果
            analysis_result = {
                "company": company_name,
                "dimension": analysis_dimension,
                "depth": analysis_depth,
                "file": os.path.basename(file_path),
                "result": result_text,
                "chart_data": chart_data,
                "timestamp": datetime.now().isoformat(),
                "model_provider": self.model_config.provider,
                "model_name": getattr(self.model_config, f"{self.model_config.provider}_model", "unknown"),
                "analysis_time": analysis_time,
                "token_usage": token_usage,
                "prompt_length": len(prompt),
                "result_length": len(result_text)
            }

            return analysis_result
        except Exception as e:
            print(f"AI分析失败: {e}")
            return {"error": f"AI分析失败: {str(e)}"}
    
    def _extract_chart_data(self, result_text: str) -> list:
        """从AI分析结果中提取图表数据

        Args:
            result_text: AI返回的分析文本

        Returns:
            图表数据列表
        """
        import re
        import json

        charts = []

        # 查找JSON代码块
        json_pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(json_pattern, result_text, re.DOTALL)

        for match in matches:
            try:
                data = json.loads(match.strip())
                # 验证图表数据格式
                if 'chart_type' in data and 'labels' in data and 'datasets' in data:
                    charts.append(data)
            except json.JSONDecodeError:
                continue

        return charts

    def _generate_prompt(self, company_name, analysis_dimension, analysis_depth, content):
        """生成分析Prompt

        Args:
            company_name: 公司名称
            analysis_dimension: 分析维度
            analysis_depth: 分析深度
            content: 文档内容

        Returns:
            生成的Prompt
        """
        # 使用PromptConfig生成Prompt
        return self.prompt_config.generate_prompt(
            company_name=company_name,
            analysis_dimension=analysis_dimension,
            analysis_depth=analysis_depth,
            content=content
        )
    
    def analyze_multiple_documents(self, file_paths, company_name, analysis_dimension, analysis_depth="中层"):
        """分析多个文档
        
        Args:
            file_paths: 文件路径列表
            company_name: 公司名称
            analysis_dimension: 分析维度
            analysis_depth: 分析深度
            
        Returns:
            分析结果列表
        """
        results = []
        for file_path in file_paths:
            result = self.analyze_document(file_path, company_name, analysis_dimension, analysis_depth)
            results.append(result)
        return results


def test_analyzer():
    """测试分析器"""
    # 创建模型配置
    config = ModelConfig()
    config.provider = "ollama"
    config.ollama_model = "qwen2.5:7b"
    
    analyzer = AIAnalyzer(model_config=config)
    
    # 测试PDF解析
    test_file = os.path.join(os.path.dirname(__file__), "downloads", "普洛药业_000739", "2024-03-28_普洛药业：2023年年度报告.pdf")
    
    if os.path.exists(test_file):
        print(f"测试文件: {test_file}")
        result = analyzer.analyze_document(test_file, "普洛药业", "战略分析", "中层")
        print("分析结果:")
        print(result.get("result", "分析失败"))
    else:
        print(f"测试文件不存在: {test_file}")


if __name__ == "__main__":
    test_analyzer()
