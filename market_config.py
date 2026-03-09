"""
市场配置模块
定义支持的市场及其优先级
"""

from enum import Enum
from typing import List, Dict


class MarketType(Enum):
    """市场类型枚举"""
    A_SHARE = "a_share"      # A股
    HK_STOCK = "hk_stock"    # 港股
    US_STOCK = "us_stock"    # 美股
    INDIA = "india"          # 印度
    SWISS = "swiss"          # 瑞士
    JAPAN = "japan"          # 日本


# 市场优先级配置（按优先级排序）
MARKET_PRIORITY = [
    MarketType.A_SHARE,   # 1. A股（必须）
    MarketType.HK_STOCK,  # 2. 港股
    MarketType.US_STOCK,  # 3. 美股
    MarketType.INDIA,     # 4. 印度
    MarketType.SWISS,     # 5. 瑞士
    MarketType.JAPAN,     # 6. 日本
]

# 市场详细信息
MARKET_CONFIG: Dict[MarketType, Dict] = {
    MarketType.A_SHARE: {
        "name": "A股",
        "name_en": "A-Share",
        "currency": "CNY",
        "exchanges": ["SSE", "SZSE"],
        "reporting_standard": "CAS",  # 中国会计准则
        "required": True,  # 必须支持
    },
    MarketType.HK_STOCK: {
        "name": "港股",
        "name_en": "Hong Kong",
        "currency": "HKD",
        "exchanges": ["HKEX"],
        "reporting_standard": "IFRS",  # 国际财务报告准则
        "required": False,
    },
    MarketType.US_STOCK: {
        "name": "美股",
        "name_en": "US Stocks",
        "currency": "USD",
        "exchanges": ["NYSE", "NASDAQ"],
        "reporting_standard": "US GAAP",
        "required": False,
    },
    MarketType.INDIA: {
        "name": "印度",
        "name_en": "India",
        "currency": "INR",
        "exchanges": ["NSE", "BSE"],
        "reporting_standard": "IND AS",  # 印度会计准则
        "required": False,
    },
    MarketType.SWISS: {
        "name": "瑞士",
        "name_en": "Switzerland",
        "currency": "CHF",
        "exchanges": ["SIX"],
        "reporting_standard": "Swiss GAAP",
        "required": False,
    },
    MarketType.JAPAN: {
        "name": "日本",
        "name_en": "Japan",
        "currency": "JPY",
        "exchanges": ["TSE"],
        "reporting_standard": "JGAAP",  # 日本会计准则
        "required": False,
    },
}


def get_market_priority() -> List[MarketType]:
    """获取按优先级排序的市场列表"""
    return MARKET_PRIORITY


def get_market_config(market: MarketType) -> Dict:
    """获取市场配置信息"""
    return MARKET_CONFIG.get(market, {})


def get_market_by_code(code: str) -> MarketType:
    """根据代码前缀获取市场类型"""
    code = code.upper()
    if code.startswith(('6', '0', '3', '68', '8', '4')):
        return MarketType.A_SHARE
    elif code.isdigit() and len(code) <= 5:
        return MarketType.HK_STOCK
    elif code.isalpha():
        return MarketType.US_STOCK
    return MarketType.A_SHARE  # 默认A股


def get_all_markets() -> List[Dict]:
    """获取所有市场信息列表"""
    return [
        {
            "type": market,
            "code": market.value,
            **MARKET_CONFIG[market]
        }
        for market in MARKET_PRIORITY
    ]


# 报表类型映射（不同市场的报表类型名称）
REPORT_TYPE_MAPPING = {
    MarketType.A_SHARE: {
        "annual": "年报",
        "semi_annual": "半年报",
        "q1": "第一季度季报",
        "q3": "第三季度季报",
    },
    MarketType.HK_STOCK: {
        "annual": "Annual Report",
        "interim": "Interim Report",
        "q1": "First Quarterly Report",
        "q3": "Third Quarterly Report",
    },
    MarketType.US_STOCK: {
        "annual": "10-K",
        "interim": "10-Q",
        "current": "8-K",
    },
    MarketType.INDIA: {
        "annual": "Annual Report",
        "interim": "Half-Yearly Report",
    },
    MarketType.SWISS: {
        "annual": "Annual Report",
        "interim": "Half-Year Report",
    },
    MarketType.JAPAN: {
        "annual": "有価証券報告書",
        "interim": "四半期報告書",
    },
}


def get_report_type_name(market: MarketType, report_type: str) -> str:
    """获取报表类型的本地化名称"""
    mapping = REPORT_TYPE_MAPPING.get(market, {})
    return mapping.get(report_type, report_type)
