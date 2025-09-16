# Market cap formatting
        market_cap_str = self.format_market_cap(company_info.get('market_cap'))
        
        # Data source info
        data_source = stock_data.get('source', 'Unknown')
        analysis_time = analysis.get('analysis_time', 0)
        
        # Base technical analysis - same for all tiers
        technical_analysis = f"""📈 完整技術分析 (所有用戶)
📊 RSI指標: {indicators.get('rsi', 50):.1f}
📏 MA20: ${indicators.get('ma20', current_price):.2f}
📏 MA50: ${indicators.get('ma50', current_price):.2f}
📊 MACD: {indicators.get('macd', 0):.3f}
📈 MACD信號: {indicators.get('macd_signal', 0):.3f}
📊 MACD柱狀: {indicators.get('macd_histogram', 0):.3f}
📊 布林帶上軌: ${indicators.get('bb_upper', current_price * 1.02):.2f}
📊 布林帶中軌: ${indicators.get('bb_middle', current_price):.2f}
📊 布林帶下軌: ${indicators.get('bb_lower', current_price * 0.98):.2f}
📦 成交量比率: {indicators.get('volume_ratio', 1):.2f}x ({indicators.get('volume_trend', 'Normal')})
🛡️ 支撐位: ${indicators.get('support_level', current_price * 0.95):.2f}
🚧 阻力位: ${indicators.get('resistance_level', current_price * 1.05):.2f}
📊 52週區間: ${indicators.get('low_52w', current_price * 0.8):.2f} - ${indicators.get('high_52w', current_price * 1.2):.2f}"""

        # Market Maker analysis - same for all tiers
        mm_analysis_text = f"""🧲 Max Pain 磁吸分析 (所有用戶)
{mm_analysis.get('mm_magnetism', '🟡 中等磁吸')} 目標: ${mm_analysis.get('max_pain_price', current_price):.2f}
📏 距離: ${mm_analysis.get('distance_to_max_pain', 0):.2f}
⚠️ 風險等級: {mm_analysis.get('risk_level', '中')}

⚡ Gamma 支撐阻力地圖 (所有用戶)
🛡️ Gamma支撐: ${mm_analysis.get('support_level', current_price * 0.95):.2f}
🚧 Gamma阻力: ${mm_analysis.get('resistance_level', current_price * 1.05):.2f}
💪 Gamma 強度: {mm_analysis.get('gamma_strength', '⚡ 中等')}
📊 交易區間: ${mm_analysis.get('support_level', current_price * 0.95):.2f} - ${mm_analysis.get('resistance_level', current_price * 1.05):.2f}

💨 IV Crush 風險評估 (所有用戶)
📊 當前 IV: {mm_analysis.get('current_iv', 30):.1f}%
📈 IV 百分位: {mm_analysis.get('iv_percentile', 50)}%
⚠️ 風險等級: {'🟢 低風險' if mm_analysis.get('iv_percentile', 50) < 70 else '🔴 高風險'}
💡 期權建議: {'適合買入期權' if mm_analysis.get('iv_percentile', 50) < 30 else '謹慎期權操作'}"""

        if user_tier == "vic":
            # VIC version - unlimited queries + weekly reports
            report = f"""🔥 {symbol} Market Maker 專業分析 (VIC頂級版)
📅 {analysis['timestamp']}
🔗 數據來源: {data_source}
⏱️ 分析耗時: {analysis_time:.1f}秒

📊 股價資訊
💰 當前價格: ${current_price:.2f}
{change_emoji} 變化: {change_sign}{abs(change):.2f} ({change_sign}{abs(change_percent):.2f}%)
📦 成交量: {stock_data.get('volume', 'N/A'):,}
🏢 市值: {market_cap_str}

{mm_analysis_text}

{technical_analysis}

🏢 公司資訊
🏭 行業: {company_info.get('industry', 'Unknown')}
📊 P/E比率: {company_info.get('pe_ratio', 'N/A')}
📊 Beta係數: {company_info.get('beta', 'N/A')}

🤖 Maggie AI VIC頂級分析
🎯 趨勢判斷: {ai_analysis['trend']}
📊 RSI信號: {ai_analysis['rsi_signal']}
💡 操作建議: {ai_analysis['suggestion']}
🎯 信心等級: {ai_analysis['confidence']}%
🔥 核心策略: {ai_analysis['strategy']}

🔥 Market Maker 行為預測
MM 目標價位: ${mm_analysis.get('max_pain_price', current_price):.2f}
預計操控強度: {mm_analysis.get('mm_magnetism', '🟡 中等磁吸')}
⚖️ 風險評估: {mm_analysis.get('risk_level', '中')}

📧 VIC頂級特權
✅ **無限查詢** - 想查多少查多少
✅ **24/7全天候** - 隨時隨地分析
✅ **每週美股報告** - 專業投資策略
✅ **專屬客服** - 優先技術支持

📅 下週投資重點預告
• 科技股財報季分析
• Fed政策影響評估  
• 新興市場機會挖掘
• 個人化投資組合建議

---
⏰ 分析時間: 2分鐘VIC頂級版
🤖 分析師: {ai_analysis['analyst']}
🔥 VIC頂級版用戶，感謝您的信任！
📧 每週報告將發送至您的信箱"""

        elif user_tier == "vip":
            # VIP version - 24/7 access, 50 queries per day
            can_query, current_count = self.check_user_query_limit(user_id)
            remaining_queries = 50 - current_count
            
            report = f"""💎 {symbol} Market Maker 專業分析 (VIP版)
📅 {analysis['timestamp']}
🔗 數據來源: {data_source}
⏱️ 分析耗時: {analysis_time:.1f}秒

📊 股價資訊
💰 當前價格: ${current_price:.2f}
{change_emoji} 變化: {change_sign}{abs(change):.2f} ({change_sign}{abs(change_percent):.2f}%)
📦 成交量: {stock_data.get('volume', 'N/A'):,}
🏢 市值: {market_cap_str}

{mm_analysis_text}

{technical_analysis}

🏢 公司資訊
🏭 行業: {company_info.get('industry', 'Unknown')}
📊 P/E比率: {company_info.get('pe_ratio', 'N/A')}

🤖 Maggie AI VIP專業分析
🎯 趨勢判斷: {ai_analysis['trend']}
📊 RSI信號: {ai_analysis['rsi_signal']}
💡 操作建議: {ai_analysis['suggestion']}
🎯 信心等級: {ai_analysis['confidence']}%
🔥 核心策略: {ai_analysis['strategy']}

🔥 Market Maker 行為預測
MM 目標價位: ${mm_analysis.get('max_pain_price', current_price):.2f}
預計操控強度: {mm_analysis.get('mm_magnetism', '🟡 中等磁吸')}
⚖️ 風險評估: {mm_analysis.get('risk_level', '中')}

📊 VIP版查詢狀態
🔍 今日剩餘查詢: {remaining_queries}/50
⏰ 重置時間: 明日00:00

---
⏰ 分析時間: 3分鐘VIP版專業分析
🤖 分析師: {ai_analysis['analyst']}

🚀 **考慮升級VIC頂級版？**
✅ **無限查詢** (vs VIP每日50次)
✅ **每週美股報告** (專業投資策略)
✅ **個人化建議** (基於您的投資偏好)
📞 **升級聯繫:** @maggie_investment"""

        else:  # Free version
            can_query, current_count = self.check_user_query_limit(user_id)
            remaining_queries = 3 - current_count
            
            report = f"""🎯 {company_info.get('name', symbol)} ({symbol}) 免費版分析
📅 {analysis['timestamp']}
🔗 數據來源: {data_source}
⏱️ 分析耗時: {analysis_time:.1f}秒

📊 股價資訊
💰 當前價格: ${current_price:.2f}
{change_emoji} 變化: {change_sign}{abs(change):.2f} ({change_sign}{abs(change_percent):.2f}%)
📦 成交量: {stock_data.get('volume', 'N/A'):,}
🏢 市值: {market_cap_str}

{mm_analysis_text}

{technical_analysis}

🤖 Maggie AI 專業分析
🎯 趨勢判斷: {ai_analysis['trend']}
📊 RSI信號: {ai_analysis['rsi_signal']}
💡 操作建議: {ai_analysis['suggestion']}
🎯 信心等級: {ai_analysis['confidence']}%

📊 免費版查詢狀態
🔍 今日剩餘查詢: {remaining_queries}/3
⏰ 查詢窗口: 開盤前15分鐘 (9:15-9:30 AM EST)

---
⏰ 分析時間: 10分鐘免費版完整報告
🤖 分析師: {ai_analysis['analyst']}

🔥 **升級享受更多便利！**

**📊 功能對比表格**

| 功能特色 | 🆓 免費版 | 💎 VIP版 | 🔥 VIC版 |
|---------|---------|---------|----------|
| 📊 技術指標 | ✅ 完整 | ✅ 完整 | ✅ 完整 |
| #!/usr/bin/env python3
import os
import logging
import requests
import yfinance as yf
from datetime import datetime, timedelta, time
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import json
import random
import aiohttp
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN', '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE')
PORT = int(os.getenv('PORT', 8080))

class VIPStockBot:
    def __init__(self):
        # API Keys
        self.finnhub_key = "d33ke01r01qib1p1dvu0d33ke01r01qib1p1dvug"
        self.polygon_key = "u2_7EiBlQG9CBqpB1AWDnzQ5TSl6zK4l"
        self.alpha_vantage_key = "NBWPE7OFZHTT3OFI"
        
        # Three-tier User management: Free, VIP, VIC
        self.vip_users = set()  # VIP tier
        self.vic_users = set()  # VIC tier (highest)
        self.user_queries = {}
        self.user_daily_vip_queries = {}  # Track VIP daily queries
        self.user_languages = {}
        self.vic_emails = {}  # Store VIC user emails for weekly reports
        
        # Time zones
        self.est = pytz.timezone('America/New_York')
        self.taipei = pytz.timezone('Asia/Taipei')
        
        # Stock symbols
        self.sp500_symbols = None
        self.mag7 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
        
        # Multilingual support
        self.texts = self._init_multilingual_texts()
        
        # Daily reset management
        self.daily_reset_time = self._get_next_reset_time()
    
    def _init_multilingual_texts(self) -> Dict:
        return {
            'zh-TW': {
                'welcome': '歡迎使用 Maggie Stock AI',
                'current_price': '當前價格',
                'change': '變化',
                'volume': '成交量',
                'market_cap': '市值',
                'company_intro': '公司簡介',
                'sector_analysis': '板塊分析',
                'technical_analysis': '技術分析',
                'institutional_tracking': '機構追蹤',
                'upgrade_vip': '升級VIP享受更多功能',
                'analyzing': '正在分析',
                'estimated_time': '預計時間',
                'query_limit_reached': '每日查詢限制已達上限',
                'window_closed': '查詢窗口已關閉',
                'stock_not_supported': '不在支援清單',
                'analysis_failed': '無法分析',
                'system_error': '系統錯誤'
            },
            'zh-CN': {
                'welcome': '欢迎使用 Maggie Stock AI',
                'current_price': '当前价格',
                'change': '变化',
                'volume': '成交量',
                'market_cap': '市值',
                'company_intro': '公司简介',
                'sector_analysis': '板块分析',
                'technical_analysis': '技术分析',
                'institutional_tracking': '机构追踪',
                'upgrade_vip': '升级VIP享受更多功能',
                'analyzing': '正在分析',
                'estimated_time': '预计时间',
                'query_limit_reached': '每日查询限制已达上限',
                'window_closed': '查询窗口已关闭',
                'stock_not_supported': '不在支援清单',
                'analysis_failed': '无法分析',
                'system_error': '系统错误'
            },
            'en': {
                'welcome': 'Welcome to Maggie Stock AI',
                'current_price': 'Current Price',
                'change': 'Change',
                'volume': 'Volume',
                'market_cap': 'Market Cap',
                'company_intro': 'Company Overview',
                'sector_analysis': 'Sector Analysis',
                'technical_analysis': 'Technical Analysis',
                'institutional_tracking': 'Institutional Tracking',
                'upgrade_vip': 'Upgrade to VIP for more features',
                'analyzing': 'Analyzing',
                'estimated_time': 'Estimated Time',
                'query_limit_reached': 'Daily query limit reached',
                'window_closed': 'Query window closed',
                'stock_not_supported': 'Stock not supported',
                'analysis_failed': 'Analysis failed',
                'system_error': 'System error'
            }
        }
    
    def _get_next_reset_time(self) -> datetime:
        """Get next daily reset time"""
        now = datetime.now(self.taipei)
        next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        return next_reset
    
    def get_user_language(self, user_id: int) -> str:
        """Get user language setting, default to Traditional Chinese"""
        return self.user_languages.get(user_id, 'zh-TW')
    
    def get_text(self, user_id: int, key: str) -> str:
        """Get text based on user language"""
        lang = self.get_user_language(user_id)
        return self.texts[lang].get(key, self.texts['zh-TW'][key])
    
    def check_user_tier(self, user_id: int) -> str:
        """Check user tier - Free, VIP, or VIC"""
        if user_id in self.vic_users:
            return "vic"
        elif user_id in self.vip_users:
            return "vip"
        else:
            return "free"
    
    def add_vip_user(self, user_id: int, tier: str, email: str = None) -> bool:
        """Add VIP/VIC user"""
        try:
            if tier == "vip":
                self.vip_users.add(user_id)
                self.vic_users.discard(user_id)  # Remove from higher tier
                logger.info(f"Added user {user_id} to VIP")
                return True
            elif tier == "vic":
                self.vic_users.add(user_id)
                self.vip_users.discard(user_id)  # Remove from lower tier
                if email:
                    self.vic_emails[user_id] = email
                    logger.info(f"Added user {user_id} to VIC with email {email}")
                else:
                    logger.info(f"Added user {user_id} to VIC without email")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to add user {user_id} to {tier}: {e}")
            return False
    
    def remove_user(self, user_id: int) -> bool:
        """Remove user from all paid tiers"""
        try:
            self.vip_users.discard(user_id)
            self.vic_users.discard(user_id)
            self.vic_emails.pop(user_id, None)
            logger.info(f"Removed user {user_id} from all tiers")
            return True
        except Exception as e:
            logger.error(f"Failed to remove user {user_id}: {e}")
            return False
    
    def check_user_query_limit(self, user_id: int) -> Tuple[bool, int]:
        """Check user query limit"""
        user_tier = self.check_user_tier(user_id)
        
        # VIP users have no limit
        if user_tier in ["basic", "vic"]:
            return True, 0
        
        # Reset if needed
        if datetime.now(self.taipei) >= self.daily_reset_time:
            self.reset_daily_queries()
        
        current_count = self.user_queries.get(user_id, 0)
        return current_count < 3, current_count
    
    def increment_user_query(self, user_id: int):
        """Increment user query count"""
        user_tier = self.check_user_tier(user_id)
        if user_tier == "free":
            self.user_queries[user_id] = self.user_queries.get(user_id, 0) + 1
    
    def reset_daily_queries(self):
        """Reset daily query counts"""
        self.user_queries = {}
        self.daily_reset_time = self._get_next_reset_time()
        logger.info("Daily query limits reset")
    
    def is_query_allowed(self, user_id: int) -> Tuple[bool, str]:
        """Check if user can query (time window + tier)"""
        user_tier = self.check_user_tier(user_id)
        
        # VIP users can query anytime
        if user_tier in ["basic", "vic"]:
            return True, "vip_access"
        
        # Free users need to check time window
        now_est = datetime.now(self.est)
        current_time = now_est.time()
        current_weekday = now_est.weekday()
        
        if current_weekday >= 5:  # Weekend
            return False, "weekend"
        
        if time(9, 15) <= current_time <= time(9, 30):
            return True, "free_window"
        elif current_time < time(9, 15):
            return False, "too_early"
        else:
            return False, "too_late"
    
    def get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 + popular stocks for free users"""
        if self.sp500_symbols:
            return self.sp500_symbols
        
        # S&P 500 major stocks + popular IPOs
        symbols = [
            # Tech giants
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'ORCL', 'CRM',
            'NFLX', 'AMD', 'INTC', 'QCOM', 'CSCO', 'IBM', 'NOW', 'INTU', 'AMAT', 'ADI',
            # Financial
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'USB', 'PNC',
            # Healthcare
            'UNH', 'JNJ', 'PFE', 'ABBV', 'LLY', 'TMO', 'ABT', 'MDT', 'BMY', 'MRK',
            # Consumer
            'PG', 'KO', 'PEP', 'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW',
            # Industrial
            'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'RTX', 'LMT', 'NOC', 'GD',
            # Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'HES', 'DVN',
            # Popular IPOs and growth stocks
            'ARM', 'RBLX', 'COIN', 'HOOD', 'AFRM', 'SOFI', 'UPST', 'LCID', 'RIVN',
            'NIO', 'XPEV', 'LI', 'PLTR', 'SNOW', 'CRWD', 'ZM', 'PTON',
            # ETFs
            'SPY', 'QQQ', 'ARKK', 'VTI', 'VOO'
        ]
        
        self.sp500_symbols = sorted(list(set(symbols)))
        logger.info(f"Loaded {len(self.sp500_symbols)} symbols for free users")
        return self.sp500_symbols
    
    def get_all_symbols(self) -> List[str]:
        """Get all symbols for VIP users (simplified for demo)"""
        # In production, this would be a much larger list
        basic_symbols = self.get_sp500_symbols()
        additional_symbols = [
            # Small cap growth
            'ROKU', 'TWLO', 'OKTA', 'DDOG', 'NET', 'FSLY', 'ESTC', 'MDB', 'TEAM',
            # Biotech
            'MRNA', 'BNTX', 'NVAX', 'OCGN', 'INO', 'VXRT', 'SAVA', 'BIIB', 'GILD',
            # International
            'BABA', 'JD', 'PDD', 'BIDU', 'TSM', 'ASML', 'SAP', 'TM', 'SNY',
            # Additional ETFs
            'IWM', 'VXX', 'SQQQ', 'ARKQ', 'ARKG', 'ARKW'
        ]
        return basic_symbols + additional_symbols
    
    async def get_stock_data_multi_source(self, symbol: str) -> Optional[Dict]:
        """Get stock data with multiple API fallbacks"""
        data_sources = [
            self._get_finnhub_data,
            self._get_polygon_data,
            self._get_yahoo_data,
            self._get_alpha_vantage_data
        ]
        
        for i, source_func in enumerate(data_sources):
            try:
                logger.info(f"Trying data source {i+1} for {symbol}")
                data = await source_func(symbol)
                if data:
                    logger.info(f"Successfully got data from source {i+1}")
                    return data
            except Exception as e:
                logger.warning(f"Data source {i+1} failed for {symbol}: {e}")
                continue
        
        logger.error(f"All data sources failed for {symbol}")
        return None
    
    async def _get_finnhub_data(self, symbol: str) -> Optional[Dict]:
        """Get data from Finnhub API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.finnhub_key}"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('c'):  # Current price exists
                            return {
                                'source': 'Finnhub',
                                'current_price': float(data['c']),
                                'change': float(data['d']),
                                'change_percent': float(data['dp']),
                                'high': float(data['h']),
                                'low': float(data['l']),
                                'open': float(data['o']),
                                'previous_close': float(data['pc']),
                                'timestamp': datetime.now()
                            }
        except Exception as e:
            logger.error(f"Finnhub API error: {e}")
        return None
    
    async def _get_polygon_data(self, symbol: str) -> Optional[Dict]:
        """Get data from Polygon API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?adjusted=true&apikey={self.polygon_key}"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('results') and len(data['results']) > 0:
                            result = data['results'][0]
                            current_price = float(result['c'])
                            open_price = float(result['o'])
                            return {
                                'source': 'Polygon',
                                'current_price': current_price,
                                'change': current_price - open_price,
                                'change_percent': ((current_price - open_price) / open_price) * 100,
                                'high': float(result['h']),
                                'low': float(result['l']),
                                'open': open_price,
                                'volume': int(result['v']),
                                'timestamp': datetime.now()
                            }
        except Exception as e:
            logger.error(f"Polygon API error: {e}")
        return None
    
    async def _get_yahoo_data(self, symbol: str) -> Optional[Dict]:
        """Get data from Yahoo Finance (fallback)"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                previous_close = float(hist['Close'].iloc[-2]) if len(hist) > 1 else current_price
                change = current_price - previous_close
                return {
                    'source': 'Yahoo Finance',
                    'current_price': current_price,
                    'change': change,
                    'change_percent': (change / previous_close) * 100 if previous_close != 0 else 0,
                    'high': float(hist['High'].iloc[-1]),
                    'low': float(hist['Low'].iloc[-1]),
                    'open': float(hist['Open'].iloc[-1]),
                    'volume': int(hist['Volume'].iloc[-1]),
                    'timestamp': datetime.now()
                }
        except Exception as e:
            logger.error(f"Yahoo Finance error: {e}")
        return None
    
    async def _get_alpha_vantage_data(self, symbol: str) -> Optional[Dict]:
        """Get data from Alpha Vantage API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}"
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        quote = data.get('Global Quote', {})
                        if quote:
                            current_price = float(quote.get('05. price', 0))
                            change = float(quote.get('09. change', 0))
                            if current_price > 0:
                                return {
                                    'source': 'Alpha Vantage',
                                    'current_price': current_price,
                                    'change': change,
                                    'change_percent': float(quote.get('10. change percent', '0%').replace('%', '')),
                                    'high': float(quote.get('03. high', 0)),
                                    'low': float(quote.get('04. low', 0)),
                                    'open': float(quote.get('02. open', 0)),
                                    'volume': int(quote.get('06. volume', 0)),
                                    'timestamp': datetime.now()
                                }
        except Exception as e:
            logger.error(f"Alpha Vantage API error: {e}")
        return None
    
    def calculate_technical_indicators(self, symbol: str, user_tier: str) -> Dict:
        """Calculate ALL technical indicators for ALL tiers - same analysis quality"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="50d")
            
            if hist.empty:
                return {}
            
            # All indicators for all users - no differentiation in analysis quality
            close_prices = hist['Close']
            volume = hist['Volume']
            high_prices = hist['High']
            low_prices = hist['Low']
            
            # RSI calculation
            delta = close_prices.diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Moving averages
            ma20 = close_prices.rolling(window=20).mean()
            ma50 = close_prices.rolling(window=50).mean()
            
            # MACD calculation
            ema12 = close_prices.ewm(span=12).mean()
            ema26 = close_prices.ewm(span=26).mean()
            macd = ema12 - ema26
            macd_signal = macd.ewm(span=9).mean()
            
            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            bb_middle = close_prices.rolling(window=bb_period).mean()
            bb_std_dev = close_prices.rolling(window=bb_period).std()
            bb_upper = bb_middle + (bb_std_dev * bb_std)
            bb_lower = bb_middle - (bb_std_dev * bb_std)
            
            # Volume analysis
            volume_ma = volume.rolling(window=20).mean()
            volume_ratio = volume.iloc[-1] / volume_ma.iloc[-1] if not volume_ma.empty else 1
            
            # Support and Resistance levels
            recent_high = high_prices.rolling(window=20).max()
            recent_low = low_prices.rolling(window=20).min()
            
            indicators = {
                'rsi': float(rsi.iloc[-1]) if not rsi.empty else 50,
                'ma20': float(ma20.iloc[-1]) if not ma20.empty else 0,
                'ma50': float(ma50.iloc[-1]) if not ma50.empty else 0,
                'high_52w': float(hist['High'].max()),
                'low_52w': float(hist['Low'].min()),
                
                # MACD indicators
                'macd': float(macd.iloc[-1]) if not macd.empty else 0,
                'macd_signal': float(macd_signal.iloc[-1]) if not macd_signal.empty else 0,
                'macd_histogram': float((macd - macd_signal).iloc[-1]) if not macd.empty else 0,
                
                # Bollinger Bands
                'bb_upper': float(bb_upper.iloc[-1]) if not bb_upper.empty else 0,
                'bb_lower': float(bb_lower.iloc[-1]) if not bb_lower.empty else 0,
                'bb_middle': float(bb_middle.iloc[-1]) if not bb_middle.empty else 0,
                'bb_squeeze': float(bb_upper.iloc[-1] - bb_lower.iloc[-1]) if not bb_upper.empty else 0,
                
                # Volume indicators
                'volume_ma': float(volume_ma.iloc[-1]) if not volume_ma.empty else 0,
                'volume_ratio': float(volume_ratio) if volume_ratio else 1,
                'volume_trend': 'High' if volume_ratio > 1.5 else 'Normal' if volume_ratio > 0.5 else 'Low',
                
                # Support/Resistance
                'resistance_level': float(recent_high.iloc[-1]) if not recent_high.empty else 0,
                'support_level': float(recent_low.iloc[-1]) if not recent_low.empty else 0
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"Failed to calculate technical indicators for {symbol}: {e}")
            return {}
    
    def generate_market_maker_analysis(self, symbol: str, price: float, user_tier: str) -> Dict:
        """Generate Market Maker analysis (simplified for demo)"""
        # This would be more sophisticated in production
        max_pain_price = price * random.uniform(0.94, 1.06)
        distance_to_max_pain = abs(price - max_pain_price)
        
        # Gamma levels
        support_level = price * random.uniform(0.90, 0.96)
        resistance_level = price * random.uniform(1.04, 1.10)
        
        # IV analysis
        current_iv = random.uniform(25, 45)
        iv_percentile = random.randint(30, 70)
        
        # MM magnetism assessment
        if abs(distance_to_max_pain / price) < 0.03:
            mm_magnetism = "🔴 極強磁吸"
            risk_level = "高"
        elif abs(distance_to_max_pain / price) < 0.05:
            mm_magnetism = "🟡 中等磁吸"
            risk_level = "中"
        else:
            mm_magnetism = "🟢 弱磁吸"
            risk_level = "低"
        
        return {
            'max_pain_price': max_pain_price,
            'distance_to_max_pain': distance_to_max_pain,
            'mm_magnetism': mm_magnetism,
            'support_level': support_level,
            'resistance_level': resistance_level,
            'current_iv': current_iv,
            'iv_percentile': iv_percentile,
            'risk_level': risk_level,
            'gamma_strength': random.choice(["⚡ 強", "⚡ 中等", "⚡ 弱"])
        }
    
    def generate_ai_analysis(self, symbol: str, data: Dict, indicators: Dict, user_tier: str) -> Dict:
        """Generate Maggie AI analysis"""
        current_price = data['current_price']
        change_percent = data['change_percent']
        rsi = indicators.get('rsi', 50)
        ma20 = indicators.get('ma20', current_price)
        ma50 = indicators.get('ma50', current_price)
        
        # Trend analysis
        if current_price > ma20 > ma50:
            trend = "強勢上漲趨勢"
            trend_confidence = "高"
        elif current_price > ma20:
            trend = "短期上漲"
            trend_confidence = "中"
        elif current_price < ma20 < ma50:
            trend = "弱勢下跌趨勢"
            trend_confidence = "高"
        else:
            trend = "盤整震盪"
            trend_confidence = "中"
        
        # RSI analysis
        if rsi > 70:
            rsi_signal = "超買警告，注意回調風險"
        elif rsi < 30:
            rsi_signal = "超賣機會，可考慮逢低買入"
        else:
            rsi_signal = "RSI正常範圍"
        
        # Generate suggestion
        if trend_confidence == "高" and "上漲" in trend and rsi < 70:
            suggestion = "建議持有或適度加倉"
            confidence = random.randint(75, 90)
            strategy = "🔥 多頭趨勢，關注阻力突破"
        elif "下跌" in trend and rsi > 30:
            suggestion = "建議減倉或觀望"
            confidence = random.randint(60, 80)
            strategy = "❄️ 空頭趨勢，等待反彈"
        else:
            suggestion = "建議保持現有倉位，密切關注"
            confidence = random.randint(50, 75)
            strategy = "⚖️ 震盪行情，區間操作"
        
        return {
            'trend': trend,
            'trend_confidence': trend_confidence,
            'rsi_signal': rsi_signal,
            'suggestion': suggestion,
            'confidence': confidence,
            'strategy': strategy,
            'analyst': f'Maggie AI {user_tier.upper()}'
        }
    
    async def analyze_stock(self, symbol: str, user_id: int) -> Optional[Dict]:
        """Main stock analysis function"""
        user_tier = self.check_user_tier(user_id)
        start_time = datetime.now()
        
        try:
            # Get stock data from multiple sources
            stock_data = await self.get_stock_data_multi_source(symbol)
            if not stock_data:
                return None
            
            # Calculate technical indicators
            indicators = self.calculate_technical_indicators(symbol, user_tier)
            
            # Get company info for VIP users
            company_info = {}
            if user_tier in ["basic", "vic"]:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    company_info = {
                        'name': info.get('shortName', symbol),
                        'sector': info.get('sector', 'Unknown'),
                        'industry': info.get('industry', 'Unknown'),
                        'market_cap': info.get('marketCap'),
                        'pe_ratio': info.get('trailingPE'),
                        'beta': info.get('beta')
                    }
                except Exception as e:
                    logger.warning(f"Failed to get company info for {symbol}: {e}")
            
            # Generate AI analysis
            ai_analysis = self.generate_ai_analysis(symbol, stock_data, indicators, user_tier)
            
            # Generate Market Maker analysis for VIP users
            mm_analysis = {}
            if user_tier in ["basic", "vic"]:
                mm_analysis = self.generate_market_maker_analysis(symbol, stock_data['current_price'], user_tier)
            
            # Calculate analysis time
            analysis_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'symbol': symbol,
                'user_tier': user_tier,
                'stock_data': stock_data,
                'indicators': indicators,
                'company_info': company_info,
                'ai_analysis': ai_analysis,
                'mm_analysis': mm_analysis,
                'analysis_time': analysis_time,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Stock analysis failed for {symbol}: {e}")
            return None
    
    def format_market_cap(self, market_cap: Optional[int]) -> str:
        """Format market cap for display"""
        if not market_cap:
            return "N/A"
        
        if market_cap > 1e12:
            return f"${market_cap/1e12:.1f}T"
        elif market_cap > 1e9:
            return f"${market_cap/1e9:.1f}B"
        elif market_cap > 1e6:
            return f"${market_cap/1e6:.1f}M"
        else:
            return f"${market_cap:,}"
    
    def format_analysis_report(self, analysis: Dict, user_id: int) -> str:
        """Format the analysis report based on user tier"""
        if not analysis:
            return self.get_text(user_id, 'analysis_failed')
        
        symbol = analysis['symbol']
        user_tier = analysis['user_tier']
        stock_data = analysis['stock_data']
        indicators = analysis['indicators']
        company_info = analysis['company_info']
        ai_analysis = analysis['ai_analysis']
        mm_analysis = analysis['mm_analysis']
        
        # Basic formatting
        current_price = stock_data['current_price']
        change = stock_data['change']
        change_percent = stock_data['change_percent']
        
        change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        change_sign = "+" if change > 0 else ""
        
        # Market cap formatting
        market_cap_str = self.format_market_cap(company_info.get('market_cap'))
        
        # Data source info
        data_source = stock_data.get('source', 'Unknown')
        analysis_time = analysis.get('analysis_time', 0)
        
        if user_tier == "vip":
            # VIP version with full Market Maker analysis
            report = f"""🔥 {symbol} Market Maker 專業分析 (VIP專享)
📅 {analysis['timestamp']}
🔗 數據來源: {data_source}
⏱️ 分析耗時: {analysis_time:.1f}秒

📊 股價資訊
💰 當前價格: ${current_price:.2f}
{change_emoji} 變化: {change_sign}{abs(change):.2f} ({change_sign}{abs(change_percent):.2f}%)
📦 成交量: {stock_data.get('volume', 'N/A'):,}
🏢 市值: {market_cap_str}

🧲 Max Pain 磁吸分析 (VIP專享)
{mm_analysis.get('mm_magnetism', '🟡 中等磁吸')} 目標: ${mm_analysis.get('max_pain_price', current_price):.2f}
📏 距離: ${mm_analysis.get('distance_to_max_pain', 0):.2f}
⚠️ 風險等級: {mm_analysis.get('risk_level', '中')}

⚡ Gamma 支撐阻力地圖 (VIP專享)
🛡️ 最近支撐: ${mm_analysis.get('support_level', current_price * 0.95):.2f}
🚧 最近阻力: ${mm_analysis.get('resistance_level', current_price * 1.05):.2f}
💪 Gamma 強度: {mm_analysis.get('gamma_strength', '⚡ 中等')}
📊 交易區間: ${mm_analysis.get('support_level', current_price * 0.95):.2f} - ${mm_analysis.get('resistance_level', current_price * 1.05):.2f}

💨 IV Crush 風險評估 (VIP專享)
📊 當前 IV: {mm_analysis.get('current_iv', 30):.1f}%
📈 IV 百分位: {mm_analysis.get('iv_percentile', 50)}%
⚠️ 風險等級: {'🟢 低風險' if mm_analysis.get('iv_percentile', 50) < 70 else '🔴 高風險'}

📈 VIP專業技術分析
📊 RSI指標: {indicators.get('rsi', 50):.1f}
📏 MA20: ${indicators.get('ma20', current_price):.2f}
📏 MA50: ${indicators.get('ma50', current_price):.2f}
📊 MACD: {indicators.get('macd', 0):.3f}
📈 MACD信號: {indicators.get('macd_signal', 0):.3f}
📊 MACD柱狀: {indicators.get('macd_histogram', 0):.3f}"""

            if 'bb_upper' in indicators:
                report += f"""
📊 布林帶上軌: ${indicators['bb_upper']:.2f}
📊 布林帶中軌: ${indicators['bb_middle']:.2f}
📊 布林帶下軌: ${indicators['bb_lower']:.2f}
📊 成交量MA: {indicators.get('volume_ma', 0):,.0f}"""

            report += f"""
📊 52週區間: ${indicators.get('low_52w', current_price * 0.8):.2f} - ${indicators.get('high_52w', current_price * 1.2):.2f}

🏢 VIP公司資訊
🏭 行業: {company_info.get('industry', 'Unknown')}
📊 P/E比率: {company_info.get('pe_ratio', 'N/A')}
📊 Beta係數: {company_info.get('beta', 'N/A')}

🤖 Maggie AI VIP專業分析
🎯 趨勢判斷: {ai_analysis['trend']}
📊 RSI信號: {ai_analysis['rsi_signal']}
💡 操作建議: {ai_analysis['suggestion']}
🎯 信心等級: {ai_analysis['confidence']}%
🔥 核心策略: {ai_analysis['strategy']}

🔥 Market Maker 行為預測 (VIP專享)
MM 目標價位: ${mm_analysis.get('max_pain_price', current_price):.2f}
預計操控強度: {mm_analysis.get('mm_magnetism', '🟡 中等磁吸')}
⚖️ 風險評估: {mm_analysis.get('risk_level', '中')}

📅 VIP專屬投資策略
• 本週熱門股: NVDA, TSLA, AAPL
• 下週關注: 科技股財報季  
• 專屬配置: 60%成長股 + 40%價值股
• 風險提醒: 留意Fed政策變化

---
⏰ 分析時間: 3分鐘VIP專業版分析
🤖 分析師: {ai_analysis['analyst']}
🔥 VIP專業版用戶專享！感謝您的支持！
📞 技術支持: @maggie_investment"""

        else:  # Free version
            report = f"""🎯 {company_info.get('name', symbol)} ({symbol}) 免費版分析
📅 {analysis['timestamp']}
🔗 數據來源: {data_source}
⏱️ 分析耗時: {analysis_time:.1f}秒

📊 基礎股價資訊
💰 當前價格: ${current_price:.2f}
{change_emoji} 變化: {change_sign}{abs(change):.2f} ({change_sign}{abs(change_percent):.2f}%)
📦 成交量: {stock_data.get('volume', 'N/A'):,}
🏢 市值: {market_cap_str}

📈 基礎技術分析
📊 RSI指標: {indicators.get('rsi', 50):.1f}
📏 MA20: ${indicators.get('ma20', current_price):.2f}
📏 MA50: ${indicators.get('ma50', current_price):.2f}
📊 52週區間: ${indicators.get('low_52w', current_price * 0.8):.2f} - ${indicators.get('high_52w', current_price * 1.2):.2f}

🤖 Maggie AI 基礎分析
🎯 趨勢判斷: {ai_analysis['trend']}
📊 RSI信號: {ai_analysis['rsi_signal']}
💡 操作建議: {ai_analysis['suggestion']}
🎯 信心等級: {ai_analysis['confidence']}%

---
⏰ 分析時間: 10分鐘免費版深度報告
🤖 分析師: {ai_analysis['analyst']}

🔥 **升級VIP享受Market Maker專業分析！**

**🆓 免費版 vs 💎 VIP版 對比**

| 功能 | 免費版 | VIP版 |
|------|-------|--------|
| 📊 股票覆蓋 | 500支 | 8000+支 |
| 🔍 查詢限制 | 每日3次 | 無限制 |
| ⏰ 查詢時間 | 15分鐘窗口 | 24/7全天候 |
| 📈 分析深度 | 基礎指標 | 專業指標 |
| 🎯 分析時間 | 10分鐘 | 3分鐘 |
| 🧲 Max Pain | ❌ | ✅ |
| ⚡ Gamma地圖 | ❌ | ✅ |
| 📊 MACD | ❌ | ✅ |
| 📊 布林帶 | ❌ | ✅ |
| 💨 IV評估 | ❌ | ✅ |

**VIP版專業功能:**
✅ **Max Pain磁吸分析** - 期權玩家必備
✅ **Gamma支撐阻力地圖** - 精準進出點
✅ **完整技術指標** - MACD + 布林帶
✅ **IV風險評估** - 期權策略必備
✅ **Market Maker分析** - 主力行為預測
✅ **24/7全天候查詢** - 不受時間限制

🎁 **VIP特價方案:**
• 🏷️ **月費:** ~~$29.99~~ **$19.99/月** (限時33%折扣)
• 💰 **年費:** ~~$299~~ **$199/年** (省$100，平均$16.58/月)

💡 **升級理由:**
不要因為工具限制錯過投資機會！
免費版只能在固定時間查詢固定股票，
VIP版讓你隨時掌握全市場投資機會。

📞 **立即升級:** @maggie_investment
⭐ **不滿意30天退款保證**"""
        
        return report標價位: ${mm_analysis.get('max_pain_price', current_price):.2f}
預計操控強度: {mm_analysis.get('mm_magnetism', '🟡 中等磁吸')}

⚖️ 風險評估: {mm_analysis.get('risk_level', '中')}

---
⏰ 分析時間: 30秒VIC專業版極速分析
🤖 分析師: {ai_analysis['analyst']}
🔥 VIC專業版用戶專享！感謝您的支持！"""

        elif user_tier == "basic":
            # VIP Basic version with Market Maker analysis
            report = f"""💎 {symbol} Market Maker 專業分析 (VIP基礎版)
📅 {analysis['timestamp']}
🔗 數據來源: {data_source}
⏱️ 分析耗時: {analysis_time:.1f}秒

📊 股價資訊
💰 當前價格: ${current_price:.2f}
{change_emoji} 變化: {change_sign}{abs(change):.2f} ({change_sign}{abs(change_percent):.2f}%)
📦 成交量: {stock_data.get('volume', 'N/A'):,}
🏢 市值: {market_cap_str}

🧲 Max Pain 磁吸分析 (VIP功能)
{mm_analysis.get('mm_magnetism', '🟡 中等磁吸')} 目標: ${mm_analysis.get('max_pain_price', current_price):.2f}
📏 距離: ${mm_analysis.get('distance_to_max_pain', 0):.2f}
⚠️ 風險等級: {mm_analysis.get('risk_level', '中')}

⚡ Gamma 支撐阻力地圖 (VIP功能)
🛡️ 最近支撐: ${mm_analysis.get('support_level', current_price * 0.95):.2f}
🚧 最近阻力: ${mm_analysis.get('resistance_level', current_price * 1.05):.2f}
💪 Gamma 強度: {mm_analysis.get('gamma_strength', '⚡ 中等')}

📈 技術分析 (VIP功能)
📊 RSI指標: {indicators.get('rsi', 50):.1f}
📏 MA20: ${indicators.get('ma20', current_price):.2f}
📏 MA50: ${indicators.get('ma50', current_price):.2f}
📊 MACD: {indicators.get('macd', 0):.3f}
📈 MACD信號: {indicators.get('macd_signal', 0):.3f}
📊 52週區間: ${indicators.get('low_52w', current_price * 0.8):.2f} - ${indicators.get('high_52w', current_price * 1.2):.2f}

🏢 基本面資訊 (VIP功能)
🏭 行業: {company_info.get('industry', 'Unknown')}
📊 P/E比率: {company_info.get('pe_ratio', 'N/A')}

🤖 Maggie AI VIP基礎版分析
🎯 趨勢判斷: {ai_analysis['trend']}
📊 RSI信號: {ai_analysis['rsi_signal']}
💡 操作建議: {ai_analysis['suggestion']}
🎯 信心等級: {ai_analysis['confidence']}%
🔥 核心策略: {ai_analysis['strategy']}

⚖️ 風險評估: {mm_analysis.get('risk_level', '中')}

---
⏰ 分析時間: 5分鐘VIP基礎版快速分析
🤖 分析師: {ai_analysis['analyst']}

🔥 **升級VIC專業版享受頂級服務！**
**VIC專業版特色:**
✅ **30秒極速分析** (比基礎版快10倍)
✅ **布林帶進階指標** (專業交易必備)
✅ **IV風險評估** (期權策略專用)
✅ **完整公司資訊** (PE/Beta/市值分析)

🎁 **限時優惠:** 原價$29.99 → **$19.99/月**
📞 **立即升級:** @maggie_investment"""

        else:  # Free version
            report = f"""🎯 {company_info.get('name', symbol)} ({symbol}) 免費版分析
📅 {analysis['timestamp']}
🔗 數據來源: {data_source}
⏱️ 分析耗時: {analysis_time:.1f}秒

📊 基礎股價資訊
💰 當前價格: ${current_price:.2f}
{change_emoji} 變化: {change_sign}{abs(change):.2f} ({change_sign}{abs(change_percent):.2f}%)
📦 成交量: {stock_data.get('volume', 'N/A'):,}
🏢 市值: {market_cap_str}

📈 基礎技術分析
📊 RSI指標: {indicators.get('rsi', 50):.1f}
📏 MA20: ${indicators.get('ma20', current_price):.2f}
📏 MA50: ${indicators.get('ma50', current_price):.2f}
📊 52週區間: ${indicators.get('low_52w', current_price * 0.8):.2f} - ${indicators.get('high_52w', current_price * 1.2):.2f}

🤖 Maggie AI 基礎分析
🎯 趨勢判斷: {ai_analysis['trend']}
📊 RSI信號: {ai_analysis['rsi_signal']}
💡 操作建議: {ai_analysis['suggestion']}
🎯 信心等級: {ai_analysis['confidence']}%

---
⏰ 分析時間: 10分鐘免費版深度報告
🤖 分析師: {ai_analysis['analyst']}

💎 **升級VIP享受Market Maker專業分析！**
**VIP基礎版特色:**
✅ **24/7全天候查詢** (不受時間限制)
✅ **全美股8000+支** (vs 免費版500支)
✅ **無限次數查詢** (vs 免費版每日3次)
✅ **5分鐘快速分析** (vs 免費版10分鐘)
✅ **Max Pain分析** (期權玩家必備)
✅ **Gamma支撐阻力** (精準進出點)

🎁 **限時優惠半價:** 原價$19.99 → **$9.99/月**
📞 **立即升級:** @maggie_investment"""
        
        return report
    
    async def generate_mag7_report(self) -> str:
        """Generate MAG7 report"""
        try:
            taipei_time = datetime.now(self.taipei)
            
            # Determine session
            hour = taipei_time.hour
            if hour == 8:
                session = "🌅 晨間報告"
            elif hour == 12:
                session = "☀️ 午間報告" 
            elif hour == 16:
                session = "🌇 黃昏報告"
            elif hour == 20:
                session = "🌙 深夜守望"
            else:
                session = "📊 即時報告"
            
            # Get MAG7 data
            mag7_data = []
            for symbol in self.mag7:
                try:
                    stock_data = await self.get_stock_data_multi_source(symbol)
                    if stock_data:
                        mag7_data.append({
                            'symbol': symbol,
                            'name': self.get_stock_name(symbol),
                            'price': stock_data['current_price'],
                            'change': stock_data['change'],
                            'change_percent': stock_data['change_percent']
                        })
                except Exception as e:
                    logger.error(f"Failed to get MAG7 data for {symbol}: {e}")
                    continue
            
            if not mag7_data:
                return "暫時無法生成七巨頭報告，請稍後再試"
            
            # Sort by performance
            mag7_data.sort(key=lambda x: x['change_percent'], reverse=True)
            
            # Calculate overall performance
            avg_change = sum(d['change_percent'] for d in mag7_data) / len(mag7_data)
            strongest = mag7_data[0]
            weakest = mag7_data[-1]
            
            # Generate report
            report = f"""🎯 美股七巨頭追蹤 {session}
📅 {taipei_time.strftime('%Y-%m-%d %H:%M')} 台北時間

📊 實時表現排行"""
            
            # Top performers
            for i, stock in enumerate(mag7_data[:5]):
                emoji = self.get_stock_emoji(stock['symbol'])
                trend_emoji = "📈" if stock['change_percent'] > 0 else "📉" if stock['change_percent'] < 0 else "➡️"
                sign = "+" if stock['change'] > 0 else ""
                
                report += f"\n{i+1}️⃣ {trend_emoji} {emoji} {stock['name']} ${stock['price']:.2f}"
                report += f"\n📊 {sign}{stock['change']:.2f} ({sign}{stock['change_percent']:.2f}%)"
                
                if i == 0 and stock['change_percent'] > 2:
                    report += " | 🚀 強勢突破"
                elif stock['change_percent'] > 0:
                    report += " | 📈 溫和上漲"
            
            # Weak performers
            weak_stocks = [s for s in mag7_data if s['change_percent'] < 0]
            if weak_stocks:
                report += f"\n\n⚠️ 弱勢股票"
                for stock in weak_stocks[:2]:
                    emoji = self.get_stock_emoji(stock['symbol'])
                    report += f"\n📉 {emoji} {stock['name']} ${stock['price']:.2f} ({stock['change_percent']:.2f}%)"
            
            # Overall analysis
            report += f"\n\n🏛️ 七巨頭整體表現"
            report += f"\n📈 平均漲跌: {avg_change:+.2f}%"
            report += f"\n🔥 最強: {self.get_stock_emoji(strongest['symbol'])} {strongest['name']} ({strongest['change_percent']:+.2f}%)"
            report += f"\n❄️ 最弱: {self.get_stock_emoji(weakest['symbol'])} {weakest['name']} ({weakest['change_percent']:+.2f}%)"
            
            # AI recommendations
            report += f"\n\n💡 AI智能建議"
            if avg_change > 1:
                report += f"\n🟢 長線持有: 💻 Microsoft, 🍎 Apple, 🔍 Alphabet"
                if strongest['change_percent'] > 5:
                    report += f"\n🟡 短線觀望: {self.get_stock_emoji(strongest['symbol'])} {strongest['name']}"
                report += f"\n🔴 風險警示: 風險可控"
            elif avg_change > -1:
                report += f"\n🟡 均衡配置: 維持現有倉位，觀察市場動向"
                report += f"\n🔴 風險警示: 注意短期波動"
            else:
                report += f"\n🔴 謹慎操作: 考慮適當避險，等待市場明確方向"
            
            report += f"\n\n🕐 下次更新: 6小時後"
            report += f"\n\n---"
            report += f"\n📊 免費版 | 每日4次自動報告"
            report += f"\n🔄 每6小時自動更新 (08:00/12:00/16:00/20:00)"
            report += f"\n💎 升級VIP享受更多功能"
            report += f"\n📞 升級聯繫: @maggie_investment"
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate MAG7 report: {e}")
            return "暫時無法生成七巨頭報告，請稍後再試"
    
    def get_stock_emoji(self, symbol: str) -> str:
        """Get emoji for stock symbol"""
        emoji_map = {
            'AAPL': '🍎',
            'MSFT': '💻', 
            'GOOGL': '🔍',
            'AMZN': '📦',
            'TSLA': '🚗',
            'META': '👥',
            'NVDA': '🚀'
        }
        return emoji_map.get(symbol, '📊')
    
    def get_stock_name(self, symbol: str) -> str:
        """Get stock name for symbol"""
        name_map = {
            'AAPL': 'Apple',
            'MSFT': 'Microsoft',
            'GOOGL': 'Alphabet',
            'AMZN': 'Amazon', 
            'TSLA': 'Tesla',
            'META': 'Meta',
            'NVDA': 'NVIDIA'
        }
        return name_map.get(symbol, symbol)
    
    def get_upgrade_prompt(self, prompt_type: str, symbol: str = None) -> str:
        """Get upgrade prompts for different scenarios"""
        if prompt_type == "query_limit":
            return """⏰ **每日查詢限制已達上限**

🔍 **免費版限制:** 3/3 次已用完
⏰ **重置時間:** 明日 00:00

💎 **立即升級解除限制！**

**VIP基礎版** 限時特價 **$9.99/月**
✅ 全美股8000+支 **無限查詢**
✅ Max Pain期權分析
✅ 5分鐘快速分析
✅ 24/7全天候使用

🎯 **今日升級享50%折扣**
原價 $19.99 → 特價 $9.99

📞 **升級聯繫:** @maggie_investment"""

        elif prompt_type == "window_closed":
            return """🔒 **查詢窗口已關閉**

⏰ **免費版限制:** 僅開盤前15分鐘可查詢
📅 **下次開放:** 明日 9:15 AM EST

💎 **VIP用戶全天候查詢！**

**VIP基礎版特色:**
✅ **24/7全天候查詢** (不受時間限制)
✅ **全美股8000+支** (vs 免費版500支)
✅ **無限次數查詢** (vs 免費版每日3次)
✅ **5分鐘分析** (vs 免費版10分鐘)

🎁 **限時特價:** ~~$19.99~~ **$9.99/月**

📞 **立即升級:** @maggie_investment
⭐ **不滿意30天退款保證**"""

        elif prompt_type == "stock_not_supported":
            return f"""❌ **'{symbol}' 不在免費版支援清單**

🔍 **免費版限制:** 僅支援500支股票 (S&P 500 + 主流IPO)
💎 **VIP版覆蓋:** 全美股8000+支股票

**你可能錯過的機會:**
📈 小盤成長股 (Russell 2000)
🚀 科技新創股 (NASDAQ全覆蓋) 
💼 生技醫療股 (FDA相關股票)
🏭 工業材料股 (供應鏈相關)

**VIP基礎版 - 特價 $9.99/月:**
✅ **全美股8000+支** 完整覆蓋
✅ **Max Pain分析** (期權必備)
✅ **無限次查詢**
✅ **專業技術分析**

🎯 **立即升級查詢 {symbol}**
📞 **聯繫:** @maggie_investment"""

        return "升級VIP享受更多功能！"


# Initialize bot instance
bot = VIPStockBot()

# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user_id = update.effective_user.id
    user_tier = bot.check_user_tier(user_id)
    can_query, current_count = bot.check_user_query_limit(user_id)
    
    if user_tier == "vic":
        welcome_message = f"""🔥 **歡迎回來，VIC專業版用戶！**

您正在使用最高等級的股票分析服務。

📊 **您的VIC專業版權益**
• **股票覆蓋:** 全美股8000+支股票
• **查詢限制:** 無限制，24/7全天候
• **分析速度:** 30秒極速分析
• **專業功能:** Market Maker分析 + 布林帶指標
• **獨家服務:** IV風險評估 + 完整技術指標

💡 **VIC專業命令**
• `/stock [代號]` - 30秒極速專業分析
• `/mag7` - 七巨頭實時報告
• `/status` - 查看VIC狀態

🎯 **核心價值**
"專業投資者的必備工具"

感謝您選擇Maggie Stock AI VIC專業版！"""
    
    elif user_tier == "basic":
        welcome_message = f"""💎 **歡迎回來，VIP基礎版用戶！**

您正在享受專業級股票分析服務。

📊 **您的VIP基礎版權益**
• **股票覆蓋:** 全美股8000+支股票
• **查詢限制:** 無限制，24/7全天候
• **分析速度:** 5分鐘快速分析
• **專業功能:** Max Pain分析 + Gamma地圖
• **特色服務:** MACD指標 + 專業建議

💡 **VIP基礎版命令**
• `/stock [代號]` - 5分鐘專業分析
• `/mag7` - 七巨頭實時報告
• `/upgrade` - 升級到VIC專業版

🚀 **考慮升級VIC專業版？**
享受30秒分析 + 布林帶指標 + IV評估

感謝您選擇Maggie Stock AI VIP基礎版！"""
    
    else:  # free
        welcome_message = f"""🤖 **歡迎使用 Maggie Stock AI 免費版!**

我是您的專業股票分析助手，提供深度市場洞察。

📊 **免費版功能**
• **股票覆蓋:** 500+支股票 (S&P 500 + 熱門IPO)
• **查詢限制:** 每日3次主動查詢 ({current_count}/3 已使用)
• **分析深度:** 10分鐘專業報告
• **查詢時間:** 開盤前15分鐘 (9:15-9:30 AM EST)

🎁 **免費福利**
• **七巨頭報告:** 每日4次自動發送
• **專業分析:** Maggie AI 個人化建議
• **風險評估:** 完整風險等級分析

💡 **快速開始**
• `/stock AAPL` - 分析蘋果公司
• `/mag7` - 立即查看七巨頭報告
• `/upgrade` - 了解VIP功能

💎 **升級VIP享受更多！**
• VIP基礎版 ($9.99): 8000+股票 + 無限查詢
• VIC專業版 ($19.99): 30秒分析 + Market Maker分析

⭐ **核心價值**
"讓每個散戶都能享受專業級投資分析"

📞 升級聯繫: @maggie_investment"""
    
    await update.message.reply_text(welcome_message)

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stock analysis command handler"""
    try:
        user_id = update.effective_user.id
        user_tier = bot.check_user_tier(user_id)
        
        if not context.args:
            # Show status and usage
            supported_symbols = bot.get_sp500_symbols() if user_tier == "free" else bot.get_all_symbols()
            can_query, current_count = bot.check_user_query_limit(user_id)
            
            status_msg = f"🎯 **Maggie Stock AI {user_tier.upper()}版**\n\n"
            
            if user_tier == "free":
                status_msg += f"📊 **股票覆蓋:** {len(supported_symbols)}支股票\n"
                status_msg += f"🔍 **每日查詢:** {current_count}/3 次已使用\n"
                status_msg += f"⏰ **分析時間:** 10分鐘深度報告\n"
            elif user_tier == "basic":
                status_msg += f"💎 **VIP基礎版** - 全美股{len(supported_symbols)}+支股票\n"
                status_msg += f"🔍 **查詢限制:** 無限制\n"
                status_msg += f"⏰ **分析時間:** 5分鐘快速分析\n"
            else:  # vic
                status_msg += f"🔥 **VIC專業版** - 全美股{len(supported_symbols)}+支股票\n"
                status_msg += f"🔍 **查詢限制:** 無限制\n"
                status_msg += f"⏰ **分析時間:** 30秒極速分析\n"
            
            status_msg += f"\n**熱門範例:**\n"
            status_msg += f"• `/stock AAPL` - 蘋果公司\n"
            status_msg += f"• `/stock TSLA` - 特斯拉\n" 
            status_msg += f"• `/stock NVDA` - 輝達\n"
            
            await update.message.reply_text(status_msg)
            return
        
        symbol = context.args[0].upper().strip()
        
        # Check query limits
        can_query, current_count = bot.check_user_query_limit(user_id)
        if not can_query:
            upgrade_prompt = bot.get_upgrade_prompt("query_limit")
            await update.message.reply_text(upgrade_prompt)
            return
        
        # Check query time window
        allowed, reason = bot.is_query_allowed(user_id)
        if not allowed and user_tier == "free":
            upgrade_prompt = bot.get_upgrade_prompt("window_closed")
            await update.message.reply_text(upgrade_prompt)
            return
        
        # Check if stock is supported
        supported_symbols = bot.get_sp500_symbols() if user_tier == "free" else bot.get_all_symbols()
        if symbol not in supported_symbols:
            if user_tier == "free":
                upgrade_prompt = bot.get_upgrade_prompt("stock_not_supported", symbol)
                await update.message.reply_text(upgrade_prompt)
            else:
                await update.message.reply_text(f"股票 {symbol} 暫時不支援，請稍後再試")
            return
        
        # Increment query count
        bot.increment_user_query(user_id)
        
        # Send processing message with tier-specific timing
        tier_info = {
            "free": {"time": "10分鐘深度分析", "badge": "🎯"},
            "basic": {"time": "5分鐘快速分析", "badge": "💎"}, 
            "vic": {"time": "30秒極速分析", "badge": "🔥"}
        }
        
        info = tier_info[user_tier]
        processing_msg = await update.message.reply_text(
            f"{info['badge']} **正在分析 {symbol}...**\n"
            f"⏰ **預計時間:** {info['time']}\n"
            f"🤖 **Maggie AI {user_tier.upper()}:** 準備專業建議"
        )
        
        # Simulate analysis time based on tier
        if user_tier == "free":
            await asyncio.sleep(2)  # 2 seconds for demo
        elif user_tier == "basic":
            await asyncio.sleep(1)  # 1 second for demo
        else:  # vic
            await asyncio.sleep(0.5)  # 0.5 seconds for demo
        
        # Perform analysis
        analysis = await bot.analyze_stock(symbol, user_id)
        
        if analysis:
            final_message = bot.format_analysis_report(analysis, user_id)
            await processing_msg.edit_text(final_message)
        else:
            error_msg = f"❌ **無法分析 {symbol}**\n\n"
            error_msg += "可能原因:\n"
            error_msg += "• 股票暫停交易\n"
            error_msg += "• 數據源暫時不可用\n"
            error_msg += "• 網路連線問題\n\n"
            error_msg += "💡 **建議:** 稍後再試或查詢其他股票"
            await processing_msg.edit_text(error_msg)
            
    except Exception as e:
        logger.error(f"Error in stock command: {e}")
        await update.message.reply_text("❌ **系統錯誤**\n\n請稍後再試，如問題持續請聯繫客服")

async def mag7_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """MAG7 report command handler"""
    processing_msg = await update.message.reply_text(
        "📊 **正在生成七巨頭報告...**\n"
        "⏰ 預計30秒，請稍候"
    )
    
    report = await bot.generate_mag7_report()
    await processing_msg.edit_text(report)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User status command handler"""
    user_id = update.effective_user.id
    user_tier = bot.check_user_tier(user_id)
    can_query, current_count = bot.check_user_query_limit(user_id)
    allowed, reason = bot.is_query_allowed(user_id)
    
    est_time = datetime.now(bot.est)
    taipei_time = datetime.now(bot.taipei)
    
    if user_tier == "vic":
        status_msg = f"""🔥 **VIC專業版用戶狀態**

👤 **用戶等級:** VIC專業版
🔍 **查詢限制:** 無限制
⏰ **查詢時間:** 24/7全天候
🚀 **分析速度:** 30秒極速

📊 **VIC專業版特權**
• 全美股8000+支股票
• Market Maker專業分析
• 布林帶進階指標
• IV風險評估

🕐 **時間資訊**
• **美東時間:** {est_time.strftime('%H:%M EST')}
• **台北時間:** {taipei_time.strftime('%H:%M')}

感謝您選擇VIC專業版服務！"""
        
    elif user_tier == "basic":
        status_msg = f"""💎 **VIP基礎版用戶狀態**

👤 **用戶等級:** VIP基礎版
🔍 **查詢限制:** 無限制
⏰ **查詢時間:** 24/7全天候
⚡ **分析速度:** 5分鐘快速

📊 **VIP基礎版特權**
• 全美股8000+支股票
• Max Pain分析
• Gamma支撐阻力地圖
• MACD專業指標

🔥 **考慮升級VIC專業版？**
享受30秒分析 + 布林帶指標

🕐 **時間資訊**
• **美東時間:** {est_time.strftime('%H:%M EST')}
• **台北時間:** {taipei_time.strftime('%H:%M')}"""
        
    else:  # free
        status_msg = f"""📊 **免費版用戶狀態**

👤 **用戶等級:** 免費版
🔍 **查詢狀態:** {current_count}/3 次已使用
⏰ **查詢窗口:**"""
        
        if allowed:
            remaining_min = 30 - est_time.minute + 15
            status_msg += f" 🟢 **目前開放** (剩餘 {remaining_min} 分鐘)"
        elif reason == "weekend":
            status_msg += f" 🔴 **週末關閉**"
        elif reason == "too_early":
            status_msg += f" 🟡 **尚未開放** (9:15 AM EST)"
        else:
            status_msg += f" 🔴 **今日已關閉**"
        
        status_msg += f"""

🕐 **時間資訊**
• **美東時間:** {est_time.strftime('%H:%M EST')}
• **台北時間:** {taipei_time.strftime('%H:%M')}

🎁 **免費服務**
• **七巨頭報告:** 每日4次自動發送
• **股票覆蓋:** 500+支 (S&P 500 + IPO)

💎 **升級享受更多！**
VIP基礎版: 8000+股票 + 無限查詢"""
    
    await update.message.reply_text(status_msg)

async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Upgrade information command handler"""
    user_id = update.effective_user.id
    user_tier = bot.check_user_tier(user_id)
    
    if user_tier == "vic":
        await update.message.reply_text(
            "🔥 **您已經是VIC專業版用戶！**\n\n"
            "您正在享受最高等級的服務。\n"
            "感謝您的支持！如有任何問題請聯繫客服。"
        )
    elif user_tier == "basic":
        upgrade_message = """💎 **升級到VIC專業版**

您目前是VIP基礎版用戶，考慮升級到專業版嗎？

🆚 **版本對比**

**💎 VIP基礎版 (當前)**
• 全美股8000+支股票
• 無限查詢
• 5分鐘快速分析
• Max Pain + Gamma分析

**🔥 VIC專業版**
• 包含基礎版所有功能
• **30秒極速分析** (快10倍)
• **布林帶進階指標** (專業必備)
• **IV風險評估** (期權策略)
• **完整技術指標** (MACD + 布林帶)

💰 **升級價格:** $19.99/月 (差價$10)

📞 **升級聯繫:** @maggie_investment"""
        
        await update.message.reply_text(upgrade_message)
    else:  # free
        upgrade_message = """💎 **Maggie Stock AI VIP 升級方案**

🆚 **版本對比詳細功能**

**🆓 免費版 (當前使用)**
• 500+支股票 (僅S&P 500 + 熱門IPO)
• 每日3次查詢限制
• 10分鐘分析報告
• 開盤前15分鐘查詢窗口

**💎 VIP基礎版 - 限時特價 $9.99/月**
*原價 $19.99，現省 $10*
• ✅ **全美股8000+支** 無限查詢
• ✅ **Max Pain分析** 期權必備
• ✅ **5分鐘快速分析** (比免費版快2倍)
• ✅ **Gamma支撐阻力地圖** (精準進出點)
• ✅ **MACD專業指標** (趨勢判斷)
• ✅ **24/7全天候查詢** (不受時間限制)

**🔥 VIC專業版 - $19.99/月**
*包含基礎版所有功能，再加上：*
• 🚀 **30秒極速分析** (比基礎版快10倍)
• 🚀 **布林帶進階指標** (專業交易必備)
• 🚀 **IV風險評估** (期權策略專用)
• 🚀 **完整技術分析** (所有指標覆蓋)

💰 **限時優惠**
🎯 **VIP基礎版**: ~~$19.99~~ **$9.99/月** (省50%)
🎯 **VIC專業版**: **$19.99/月** (包含所有功能)

📈 **為什麼選擇升級？**
• 免費版只能看標普500，錯過小盤成長股機會
• 每日3次限制，無法深度研究多支股票
• 時間窗口限制，錯過盤中投資機會

📞 **立即升級聯繫:** @maggie_investment
🎯 **限時優惠只到月底！**"""
        
        await update.message.reply_text(upgrade_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help command handler"""
    user_id = update.effective_user.id
    user_tier = bot.check_user_tier(user_id)
    
    if user_tier == "vic":
        help_message = """📚 **VIC專業版使用指南**

**🔧 VIC專業版命令**
• `/start` - VIC專業版歡迎頁面
• `/stock [代號]` - 30秒極速專業分析
• `/mag7` - 七巨頭實時報告
• `/status` - 查看VIC狀態
• `/help` - 使用指南

**🔥 VIC專業版特色**
• **極速分析:** 30秒完成深度分析
• **Market Maker分析:** 專業期權分析
• **布林帶指標:** 精準支撐阻力
• **IV風險評估:** 期權策略必備

**🆘 VIC專業版客服**
@maggie_investment"""
        
    elif user_tier == "basic":
        help_message = """📚 **VIP基礎版使用指南**

**🔧 VIP基礎版命令**
• `/start` - VIP歡迎頁面
• `/stock [代號]` - 5分鐘專業分析
• `/mag7` - 七巨頭實時報告
• `/upgrade` - 升級到VIC專業版
• `/status` - 查看VIP狀態

**💎 VIP基礎版特色**
• **無限查詢:** 24/7全天候使用
• **Max Pain分析:** 期權磁吸效應
• **Gamma地圖:** 支撐阻力位計算
• **MACD指標:** 專業趨勢分析

**🆘 VIP客服**
@maggie_investment"""
        
    else:  # free
        help_message = """📚 **免費版使用指南**

**🔧 基本命令**
• `/start` - 歡迎頁面與功能介紹
• `/stock [代號]` - 股票深度分析
• `/mag7` - 七巨頭實時報告
• `/upgrade` - VIP升級說明
• `/status` - 查詢使用狀態

**📊 免費版功能**
• **深度報告:** 10分鐘專業分析
• **技術指標:** RSI, 移動平均線
• **AI建議:** Maggie 個人化建議

**⏰ 使用限制**
• **查詢時間:** 開盤前15分鐘 (9:15-9:30 AM EST)
• **每日限制:** 3次主動查詢
• **股票範圍:** S&P 500 + 熱門IPO (500+支)

**💎 升級VIP享受**
• 8000+股票 + 無限查詢
• 24/7全天候使用
• 5分鐘/30秒快速分析

**🆘 技術支持**
@maggie_investment"""
    
    await update.message.reply_text(help_message)

# Admin commands
async def admin_add_vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to add VIP users"""
    admin_ids = [981883005]  # Maggie.L's admin ID
    
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ 權限不足")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "**用法:** /admin_add_vip [用戶ID] [basic/vic]\n"
            "**例如:** /admin_add_vip 123456789 basic"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        tier = context.args[1].lower()
        
        if tier not in ["basic", "vic"]:
            await update.message.reply_text("❌ 等級必須是 basic 或 vic")
            return
        
        if bot.add_vip_user(target_user_id, tier):
            await update.message.reply_text(
                f"✅ **VIP用戶添加成功**\n"
                f"👤 **用戶ID:** {target_user_id}\n"
                f"💎 **等級:** {tier.upper()}"
            )
        else:
            await update.message.reply_text("❌ 添加失敗")
        
    except ValueError:
        await update.message.reply_text("❌ 用戶ID必須是數字")
    except Exception as e:
        await update.message.reply_text(f"❌ 添加失敗: {e}")

async def admin_remove_vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to remove VIP users"""
    admin_ids = [981883005]  # Maggie.L's admin ID
    
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ 權限不足")
        return
    
    if len(context.args) < 1:
        await update.message.reply_text(
            "**用法:** /admin_remove_vip [用戶ID]\n"
            "**例如:** /admin_remove_vip 123456789"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        
        if bot.remove_vip_user(target_user_id):
            await update.message.reply_text(
                f"✅ **VIP用戶移除成功**\n"
                f"👤 **用戶ID:** {target_user_id}"
            )
        else:
            await update.message.reply_text("❌ 移除失敗")
        
    except ValueError:
        await update.message.reply_text("❌ 用戶ID必須是數字")
    except Exception as e:
        await update.message.reply_text(f"❌ 移除失敗: {e}")

async def admin_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to check system status"""
    admin_ids = [981883005]  # Maggie.L's admin ID
    
    if update.effective_user.id not in admin_ids:
        await update.message.reply_text("❌ 權限不足")
        return
    
    try:
        status_msg = f"""🔧 **系統狀態報告**

📊 **用戶統計**
• VIC專業版用戶: {len(bot.vic_pro_users)}人
• VIP基礎版用戶: {len(bot.vip_basic_users)}人
• 今日查詢記錄: {len(bot.user_queries)}筆

🕐 **系統時間**
• 台北時間: {datetime.now(bot.taipei).strftime('%Y-%m-%d %H:%M:%S')}
• 美東時間: {datetime.now(bot.est).strftime('%Y-%m-%d %H:%M:%S')}
• 下次重置: {bot.daily_reset_time.strftime('%Y-%m-%d %H:%M:%S')}

📈 **股票清單**
• 免費版股票: {len(bot.get_sp500_symbols())}支
• VIP版股票: {len(bot.get_all_symbols())}支

🤖 **系統狀態:** 🟢 正常運行"""
        
        await update.message.reply_text(status_msg)
        
    except Exception as e:
        await update.message.reply_text(f"❌ 狀態查詢失敗: {e}")

# Scheduled tasks
async def send_mag7_report_to_all(context: ContextTypes.DEFAULT_TYPE):
    """Send MAG7 report to all users (placeholder for actual implementation)"""
    try:
        report = await bot.generate_mag7_report()
        logger.info("MAG7 report generated successfully for scheduled broadcast")
        
        # In a real implementation, you would:
        # 1. Fetch all subscribed user IDs from database
        # 2. Send report to each user
        # 3. Handle rate limits and failures
        
        # For now, just log the report generation
        # all_users = get_all_users_from_database()
        # for user_id in all_users:
        #     try:
        #         await context.bot.send_message(chat_id=user_id, text=report)
        #         await asyncio.sleep(0.05)  # Rate limiting
        #     except Exception as e:
        #         logger.error(f"Failed to send MAG7 report to {user_id}: {e}")
        
    except Exception as e:
        logger.error(f"Failed to generate/send MAG7 report: {e}")

def setup_webhook():
    """Setup webhook for production deployment"""
    try:
        render_url = os.getenv('RENDER_EXTERNAL_URL', "https://maggie-stock-ai.onrender.com")
        webhook_url = f"{render_url}/{BOT_TOKEN}"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        data = {'url': webhook_url, 'allowed_updates': ['message']}
        
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info(f"Webhook set successfully: {webhook_url}")
            return True
        else:
            logger.error(f"Failed to set webhook: {result}")
            return False
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return False

def clear_webhook():
    """Clear webhook"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.get(url, timeout=10)
        result = response.json()
        logger.info(f"Webhook cleared: {result}")
        return result.get('ok', False)
    except Exception as e:
        logger.error(f"Failed to clear webhook: {e}")
        return False

def main():
    """Main function to run the bot"""
    logger.info("Starting Maggie Stock AI VIP-Enabled Bot...")
    
    # Initialize stock lists
    free_symbols = bot.get_sp500_symbols()
    vip_symbols = bot.get_all_symbols()
    logger.info(f"Loaded {len(free_symbols)} free stocks, {len(vip_symbols)} VIP stocks")
    
    # Initialize daily reset
    bot.reset_daily_queries()
    
    # Clear existing webhook
    clear_webhook()
    
    # Build application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(CommandHandler("mag7", mag7_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("upgrade", upgrade_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # Admin commands
    application.add_handler(CommandHandler("admin_add_vip", admin_add_vip_command))
    application.add_handler(CommandHandler("admin_remove_vip", admin_remove_vip_command))
    application.add_handler(CommandHandler("admin_status", admin_status_command))
    
    # Setup scheduled jobs
    job_queue = application.job_queue
    if job_queue:
        taipei_tz = pytz.timezone('Asia/Taipei')
        # Daily MAG7 reports
        for hour in [8, 12, 16, 20]:
            job_queue.run_daily(
                send_mag7_report_to_all, 
                time(hour, 0), 
                days=(0, 1, 2, 3, 4, 5, 6), 
                timezone=taipei_tz
            )
        
        # Daily reset
        job_queue.run_daily(
            lambda context: bot.reset_daily_queries(), 
            time(0, 0), 
            timezone=taipei_tz
        )
    
    # Run bot
    if os.getenv('RENDER'):
        logger.info(f"Running in Render mode on port {PORT}")
        try:
            if setup_webhook():
                logger.info("Starting webhook server...")
                application.run_webhook(
                    listen="0.0.0.0",
                    port=PORT,
                    webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL', 'https://maggie-stock-ai.onrender.com')}/{BOT_TOKEN}",
                    url_path=BOT_TOKEN
                )
            else:
                logger.warning("Webhook setup failed, using polling...")
                application.run_polling()
        except Exception as e:
            logger.error(f"Webhook failed: {e}, using polling...")
            application.run_polling()
    else:
        logger.info("Running in local development mode")
        application.run_polling()

if __name__ == '__main__':
    main()
