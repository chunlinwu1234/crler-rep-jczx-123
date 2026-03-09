"""
多市场配置模块
支持A股、港股、美股、印度、瑞士、日本等市场
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MarketConfig:
    """市场配置类"""
    code: str  # 市场代码
    name_cn: str  # 中文名称
    name_en: str  # 英文名称
    currency: str  # 货币代码
    timezone: str  # 时区
    exchange: str  # 主要交易所
    financial_report_format: str  # 财务报告格式
    accounting_standard: str  # 会计准则
    priority: int  # 优先级（数字越小优先级越高）
    supported: bool  # 是否已支持
    
    # 字段映射配置
    field_mapping: Dict[str, str] = None
    
    def __post_init__(self):
        if self.field_mapping is None:
            self.field_mapping = {}


# 市场配置（按优先级排序）
MARKETS = {
    'A股': MarketConfig(
        code='CN',
        name_cn='A股',
        name_en='China A-Share',
        currency='CNY',
        timezone='Asia/Shanghai',
        exchange='SSE/SZSE',
        financial_report_format='CAS',
        accounting_standard='中国企业会计准则',
        priority=1,
        supported=True,
        field_mapping={
            # A股标准字段（无需映射）
            'total_assets': 'total_assets',
            'total_liab': 'total_liab',
            'revenue': 'revenue',
            'n_income_attr_p': 'n_income_attr_p',
        }
    ),
    
    '港股': MarketConfig(
        code='HK',
        name_cn='港股',
        name_en='Hong Kong Stock',
        currency='HKD',
        timezone='Asia/Hong_Kong',
        exchange='HKEX',
        financial_report_format='IFRS/HKFRS',
        accounting_standard='香港财务报告准则',
        priority=2,
        supported=True,
        field_mapping={
            # 港股特有映射
            'total_assets': 'total_assets',
            'total_liab': 'total_liabilities',
            'revenue': 'revenue',
            'n_income_attr_p': 'profit_attributable_to_owners',
            'roe': 'return_on_equity',
        }
    ),
    
    '美股': MarketConfig(
        code='US',
        name_cn='美股',
        name_en='US Stock',
        currency='USD',
        timezone='America/New_York',
        exchange='NYSE/NASDAQ',
        financial_report_format='GAAP',
        accounting_standard='美国公认会计原则',
        priority=3,
        supported=True,
        field_mapping={
            # 美股特有映射
            'total_assets': 'total_assets',
            'total_liab': 'total_liabilities',
            'revenue': 'total_revenue',
            'n_income_attr_p': 'net_income',
            'roe': 'return_on_average_equity',
            'eps': 'basic_earnings_per_share',
        }
    ),
    
    '印度': MarketConfig(
        code='IN',
        name_cn='印度',
        name_en='India Stock',
        currency='INR',
        timezone='Asia/Kolkata',
        exchange='NSE/BSE',
        financial_report_format='IND AS',
        accounting_standard='印度会计准则',
        priority=4,
        supported=False,  # 待开发
        field_mapping={
            'total_assets': 'total_assets',
            'total_liab': 'total_liabilities',
            'revenue': 'total_income',
            'n_income_attr_p': 'net_profit',
        }
    ),
    
    '瑞士': MarketConfig(
        code='CH',
        name_cn='瑞士',
        name_en='Switzerland Stock',
        currency='CHF',
        timezone='Europe/Zurich',
        exchange='SIX',
        financial_report_format='IFRS',
        accounting_standard='国际财务报告准则',
        priority=5,
        supported=False,  # 待开发
        field_mapping={
            'total_assets': 'total_assets',
            'total_liab': 'total_liabilities',
            'revenue': 'net_sales',
            'n_income_attr_p': 'net_income_attributable_to_shareholders',
        }
    ),
    
    '日本': MarketConfig(
        code='JP',
        name_cn='日本',
        name_en='Japan Stock',
        currency='JPY',
        timezone='Asia/Tokyo',
        exchange='TSE',
        financial_report_format='JGAAP',
        accounting_standard='日本公认会计原则',
        priority=6,
        supported=False,  # 待开发
        field_mapping={
            'total_assets': 'total_assets',
            'total_liab': 'total_liabilities',
            'revenue': 'net_sales',
            'n_income_attr_p': 'profit_attributable_to_owners_of_parent',
        }
    ),
}


def get_market_by_code(code: str) -> Optional[MarketConfig]:
    """根据代码获取市场配置"""
    for market in MARKETS.values():
        if market.code == code:
            return market
    return None


def get_market_by_name(name: str) -> Optional[MarketConfig]:
    """根据名称获取市场配置"""
    return MARKETS.get(name)


def get_supported_markets() -> List[MarketConfig]:
    """获取已支持的市场列表（按优先级排序）"""
    supported = [m for m in MARKETS.values() if m.supported]
    return sorted(supported, key=lambda x: x.priority)


def get_all_markets() -> List[MarketConfig]:
    """获取所有市场列表（按优先级排序）"""
    return sorted(MARKETS.values(), key=lambda x: x.priority)


def get_market_options() -> List[str]:
    """获取市场选项列表（用于下拉框）"""
    markets = get_all_markets()
    return [f"{m.name_cn} ({m.code})" for m in markets]


def get_supported_market_options() -> List[str]:
    """获取已支持的市场选项列表"""
    markets = get_supported_markets()
    return [f"{m.name_cn} ({m.code})" for m in markets]


def map_field_to_standard(market_code: str, local_field: str) -> str:
    """
    将本地字段映射到标准字段
    
    Args:
        market_code: 市场代码
        local_field: 本地字段名
        
    Returns:
        标准字段名
    """
    market = get_market_by_code(market_code)
    if market and market.field_mapping:
        return market.field_mapping.get(local_field, local_field)
    return local_field


def get_market_currency_symbol(market_code: str) -> str:
    """获取市场货币符号"""
    currency_symbols = {
        'CNY': '¥',
        'HKD': 'HK$',
        'USD': '$',
        'INR': '₹',
        'CHF': 'CHF',
        'JPY': '¥',
    }
    market = get_market_by_code(market_code)
    if market:
        return currency_symbols.get(market.currency, market.currency)
    return ''


# 会计准则对照表
ACCOUNTING_STANDARDS = {
    'CAS': {
        'name_cn': '中国企业会计准则',
        'name_en': 'China Accounting Standards',
        'description': '适用于A股市场',
    },
    'IFRS': {
        'name_cn': '国际财务报告准则',
        'name_en': 'International Financial Reporting Standards',
        'description': '适用于港股、瑞士等市场',
    },
    'GAAP': {
        'name_cn': '美国公认会计原则',
        'name_en': 'Generally Accepted Accounting Principles',
        'description': '适用于美股市场',
    },
    'HKFRS': {
        'name_cn': '香港财务报告准则',
        'name_en': 'Hong Kong Financial Reporting Standards',
        'description': '适用于港股市场',
    },
    'IND AS': {
        'name_cn': '印度会计准则',
        'name_en': 'Indian Accounting Standards',
        'description': '适用于印度市场',
    },
    'JGAAP': {
        'name_cn': '日本公认会计原则',
        'name_en': 'Japanese GAAP',
        'description': '适用于日本市场',
    },
}


def get_accounting_standard_info(standard_code: str) -> dict:
    """获取会计准则信息"""
    return ACCOUNTING_STANDARDS.get(standard_code, {})


if __name__ == "__main__":
    print("=" * 80)
    print("多市场配置信息")
    print("=" * 80)
    
    print("\n【市场优先级列表】")
    for market in get_all_markets():
        status = "✅ 已支持" if market.supported else "🚧 待开发"
        print(f"  优先级{market.priority}: {market.name_cn} ({market.code}) - {status}")
        print(f"    货币: {market.currency}, 交易所: {market.exchange}")
        print(f"    会计准则: {market.accounting_standard}")
        print()
    
    print("\n【已支持市场】")
    for market in get_supported_markets():
        print(f"  - {market.name_cn} ({market.code}): {market.name_en}")
    
    print("\n【市场选项】")
    for option in get_market_options():
        print(f"  - {option}")
