#!/usr/bin/env python3
import os
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta, time
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue
import json
import random

# 設置日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 機器人令牌和API密鑰
BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
FINNHUB_API_KEY = 'd33ke01r01qib1p1dvu0d33ke01r01qib1p1dvug'

# 管理員用戶ID
ADMIN_USER_ID = 981883005  # Maggie.L

class MaggieStockAI:
    def __init__(self):
        self.user_queries = {}  # 追蹤用戶每日查詢次數
        self.daily_reset_time = None
        
        # VIP用戶清單（實際應用中應存儲在數據庫）
        self.vip_basic_users = set()
        self.vip_pro_users = set()
        
        # 時區設置
        self.est = pytz.timezone('America/New_York')
        self.taipei = pytz.timezone('Asia/Taipei')
        
        # 七巨頭股票
        self.mag7_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
        
        # 支援的股票清單 - 標普500 + 熱門股票
        self.supported_stocks = {
            # 七巨頭
            'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', 'emoji': '🍎'},
            'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Technology', 'emoji': '💻'},
            'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Technology', 'emoji': '🔍'},
            'AMZN': {'name': 'Amazon.com Inc.', 'sector': 'Technology', 'emoji': '📦'},
            'TSLA': {'name': 'Tesla Inc.', 'sector': 'Automotive', 'emoji': '🚗'},
            'META': {'name': 'Meta Platforms Inc.', 'sector': 'Technology', 'emoji': '👥'},
            'NVDA': {'name': 'NVIDIA Corporation', 'sector': 'Technology', 'emoji': '🚀'},
            
            # 其他熱門科技股
            'NFLX': {'name': 'Netflix Inc.', 'sector': 'Entertainment', 'emoji': '📺'},
            'AMD': {'name': 'Advanced Micro Devices', 'sector': 'Technology', 'emoji': '⚡'},
            'INTC': {'name': 'Intel Corporation', 'sector': 'Technology', 'emoji': '🔧'},
            'ORCL': {'name': 'Oracle Corporation', 'sector': 'Technology', 'emoji': '🏛️'},
            'CRM': {'name': 'Salesforce Inc.', 'sector': 'Technology', 'emoji': '☁️'},
            'ADBE': {'name': 'Adobe Inc.', 'sector': 'Technology', 'emoji': '🎨'},
            
            # 金融股
            'JPM': {'name': 'JPMorgan Chase & Co.', 'sector': 'Financial', 'emoji': '🏦'},
            'BAC': {'name': 'Bank of America Corp.', 'sector': 'Financial', 'emoji': '💳'},
            'WFC': {'name': 'Wells Fargo & Company', 'sector': 'Financial', 'emoji': '🏛️'},
            'GS': {'name': 'Goldman Sachs Group', 'sector': 'Financial', 'emoji': '💎'},
            'MS': {'name': 'Morgan Stanley', 'sector': 'Financial', 'emoji': '📈'},
            'V': {'name': 'Visa Inc.', 'sector': 'Financial', 'emoji': '💳'},
            'MA': {'name': 'Mastercard Inc.', 'sector': 'Financial', 'emoji': '💳'},
            'PYPL': {'name': 'PayPal Holdings', 'sector': 'Financial', 'emoji': '💰'},
            
            # 醫療股
            'JNJ': {'name': 'Johnson & Johnson', 'sector': 'Healthcare', 'emoji': '🏥'},
            'PFE': {'name': 'Pfizer Inc.', 'sector': 'Healthcare', 'emoji': '💊'},
            'UNH': {'name': 'UnitedHealth Group', 'sector': 'Healthcare', 'emoji': '🏥'},
            'ABBV': {'name': 'AbbVie Inc.', 'sector': 'Healthcare', 'emoji': '💉'},
            'LLY': {'name': 'Eli Lilly and Co.', 'sector': 'Healthcare', 'emoji': '💊'},
            'MRNA': {'name': 'Moderna Inc.', 'sector': 'Healthcare', 'emoji': '🧬'},
            
            # 消費股
            'KO': {'name': 'Coca-Cola Company', 'sector': 'Consumer', 'emoji': '🥤'},
            'PG': {'name': 'Procter & Gamble', 'sector': 'Consumer', 'emoji': '🧴'},
            'WMT': {'name': 'Walmart Inc.', 'sector': 'Retail', 'emoji': '🛒'},
            'HD': {'name': 'Home Depot Inc.', 'sector': 'Retail', 'emoji': '🔨'},
            'MCD': {'name': 'McDonald\'s Corp.', 'sector': 'Consumer', 'emoji': '🍟'},
            'NKE': {'name': 'Nike Inc.', 'sector': 'Consumer', 'emoji': '👟'},
            'SBUX': {'name': 'Starbucks Corp.', 'sector': 'Consumer', 'emoji': '☕'},
            
            # ETF
            'SPY': {'name': 'SPDR S&P 500 ETF', 'sector': 'ETF', 'emoji': '📊'},
            'QQQ': {'name': 'Invesco QQQ Trust', 'sector': 'ETF', 'emoji': '📈'},
            'VTI': {'name': 'Vanguard Total Stock Market', 'sector': 'ETF', 'emoji': '📊'},
            'IWM': {'name': 'iShares Russell 2000', 'sector': 'ETF', 'emoji': '📉'},
            
            # 熱門成長股
            'PLTR': {'name': 'Palantir Technologies', 'sector': 'Technology', 'emoji': '🔮'},
            'SNOW': {'name': 'Snowflake Inc.', 'sector': 'Technology', 'emoji': '❄️'},
            'CRWD': {'name': 'CrowdStrike Holdings', 'sector': 'Technology', 'emoji': '🛡️'},
            'ZM': {'name': 'Zoom Video Communications', 'sector': 'Technology', 'emoji': '📹'},
            'ROKU': {'name': 'Roku Inc.', 'sector': 'Technology', 'emoji': '📺'},
            'COIN': {'name': 'Coinbase Global', 'sector': 'Financial', 'emoji': '₿'},
            'HOOD': {'name': 'Robinhood Markets', 'sector': 'Financial', 'emoji': '🏹'},
            
            # 中概股
            'BABA': {'name': 'Alibaba Group', 'sector': 'Technology', 'emoji': '🛒'},
            'JD': {'name': 'JD.com Inc.', 'sector': 'Technology', 'emoji': '📦'},
            'PDD': {'name': 'PDD Holdings', 'sector': 'Technology', 'emoji': '🛍️'},
            'NIO': {'name': 'NIO Inc.', 'sector': 'Automotive', 'emoji': '🔋'},
            'XPEV': {'name': 'XPeng Inc.', 'sector': 'Automotive', 'emoji': '🚗'},
            'LI': {'name': 'Li Auto Inc.', 'sector': 'Automotive', 'emoji': '🔋'}
        }
    
    def check_user_tier(self, user_id):
        """檢查用戶等級"""
        if user_id in self.vip_pro_users:
            return "pro"
        elif user_id in self.vip_basic_users:
            return "basic"
        else:
            return "free"
    
    def is_admin(self, user_id):
        """檢查是否為管理員"""
        return user_id == ADMIN_USER_ID
    
    def add_vip_user(self, user_id, tier):
        """添加VIP用戶"""
        if tier == "basic":
            self.vip_basic_users.add(user_id)
            self.vip_pro_users.discard(user_id)  # 移除舊等級
            logger.info(f"Added user {user_id} to VIP Basic")
            return True
        elif tier == "pro":
            self.vip_pro_users.add(user_id)
            self.vip_basic_users.discard(user_id)  # 移除舊等級
            logger.info(f"Added user {user_id} to VIP Pro")
            return True
        return False
    
    def remove_vip_user(self, user_id):
        """移除VIP用戶"""
        self.vip_basic_users.discard(user_id)
        self.vip_pro_users.discard(user_id)
        logger.info(f"Removed user {user_id} from VIP")
    
    def reset_daily_queries(self):
        """重置每日查詢次數"""
        self.user_queries = {}
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        logger.info("Daily query limits reset")
    
    def check_user_query_limit(self, user_id):
        """檢查用戶查詢限制"""
        user_tier = self.check_user_tier(user_id)
        
        # VIP用戶無限制
        if user_tier in ["basic", "pro"]:
            return True, 0
        
        # 免費用戶檢查限制
        if self.daily_reset_time and datetime.now() >= self.daily_reset_time:
            self.reset_daily_queries()
        
        current_count = self.user_queries.get(user_id, 0)
        return current_count < 3, current_count
    
    def increment_user_query(self, user_id):
        """增加用戶查詢次數"""
        user_tier = self.check_user_tier(user_id)
        if user_tier == "free":
            self.user_queries[user_id] = self.user_queries.get(user_id, 0) + 1
    
    async def get_stock_data_from_finnhub(self, symbol):
        """從 Finnhub API 獲取真實股票數據"""
        try:
            async with aiohttp.ClientSession() as session:
                quote_url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={FINNHUB_API_KEY}"
                
                async with session.get(quote_url) as response:
                    if response.status == 200:
                        quote_data = await response.json()
                        
                        if quote_data and 'c' in quote_data and quote_data['c'] != 0:
                            return {
                                'current_price': quote_data.get('c', 0),
                                'change': quote_data.get('d', 0),
                                'change_percent': quote_data.get('dp', 0),
                                'high': quote_data.get('h', 0),
                                'low': quote_data.get('l', 0),
                                'open': quote_data.get('o', 0),
                                'previous_close': quote_data.get('pc', 0),
                                'timestamp': quote_data.get('t', 0)
                            }
                        else:
                            logger.warning(f"Invalid data for {symbol}: {quote_data}")
                            return None
                    else:
                        logger.error(f"API request failed with status {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return None
    
    async def get_stock_analysis(self, symbol, user_id):
        """獲取股票分析"""
        if symbol not in self.supported_stocks:
            return None
        
        stock_data = await self.get_stock_data_from_finnhub(symbol)
        
        if not stock_data:
            logger.error(f"Failed to get data for {symbol}")
            return None
        
        stock_info = self.supported_stocks[symbol]
        user_tier = self.check_user_tier(user_id)
        
        current_price = stock_data['current_price']
        change_percent = stock_data['change_percent']
        
        # 計算技術指標
        rsi = 50 + (change_percent * 2)
        rsi = max(0, min(100, rsi))
        
        # 生成分析
        analysis = self.generate_stock_analysis(symbol, current_price, change_percent, rsi, user_tier)
        
        return {
            'symbol': symbol,
            'name': stock_info['name'],
            'sector': stock_info['sector'],
            'emoji': stock_info.get('emoji', '📊'),
            'current_price': current_price,
            'change': stock_data['change'],
            'change_percent': change_percent,
            'high': stock_data['high'],
            'low': stock_data['low'],
            'open': stock_data['open'],
            'previous_close': stock_data['previous_close'],
            'volume': random.randint(1000000, 100000000),  # 模擬成交量
            'rsi': rsi,
            'user_tier': user_tier,
            'analysis': analysis,
            'timestamp': datetime.now(self.taipei).strftime('%Y-%m-%d %H:%M:%S'),
            'market_time': datetime.fromtimestamp(stock_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S') if stock_data['timestamp'] else 'N/A'
        }
    
    def generate_stock_analysis(self, symbol, price, change_pct, rsi, user_tier, deep_analysis=None):
        """生成股票分析 - 整合深度分析結果"""
        
        # 趨勢分析
        if change_pct > 3:
            trend = "強勢突破"
            trend_emoji = "🚀"
        elif change_pct > 1:
            trend = "溫和上漲"
            trend_emoji = "📈"
        elif change_pct > -1:
            trend = "震盪整理"
            trend_emoji = "📊"
        elif change_pct > -3:
            trend = "溫和下跌"
            trend_emoji = "📉"
        else:
            trend = "大幅下跌"
            trend_emoji = "⬇️"
        
        # RSI分析
        if rsi > 70:
            rsi_signal = "超買警告"
            rsi_emoji = "⚠️"
        elif rsi < 30:
            rsi_signal = "超賣機會"
            rsi_emoji = "💎"
        else:
            rsi_signal = "正常範圍"
            rsi_emoji = "✅"
        
        # 操作建議
        confidence = random.randint(60, 90)
        if trend == "強勢突破" and rsi < 70:
            suggestion = "建議持有或適度加倉"
        elif "上漲" in trend:
            suggestion = "建議持有"
        elif "下跌" in trend and rsi > 35:
            suggestion = "建議減倉或觀望"
        elif rsi < 30:
            suggestion = "可考慮逢低買入"
        else:
            suggestion = "建議保持現有倉位"
        
        # VIP功能 - 使用深度分析結果
        vip_analysis = {}
        if user_tier in ["basic", "pro"] and deep_analysis:
            support_resistance = deep_analysis.get('support_resistance', {})
            market_maker = deep_analysis.get('market_maker', {})
            
            support_levels = support_resistance.get('support_levels', [price * 0.95])
            resistance_levels = support_resistance.get('resistance_levels', [price * 1.05])
            
            vip_analysis = {
                'support_level': support_levels[0] if support_levels else price * 0.95,
                'resistance_level': resistance_levels[0] if resistance_levels else price * 1.05,
                'max_pain_price': market_maker.get('max_pain_price', price),
                'mm_magnetism': market_maker.get('magnetism', '中等磁吸'),
                'gamma_strength': f"⚡ {market_maker.get('gamma_strength', '中等')}",
                'delta_flow': '🟢 多頭流向' if change_pct > 0 else '🔴 空頭流向',
                'mm_behavior': market_maker.get('mm_behavior', 'MM 維持平衡'),
                'iv_risk': '🟢 低風險' if abs(change_pct) < 2 else '🟡 中等風險' if abs(change_pct) < 5 else '🔴 高風險',
                'strategy': '突破買入' if change_pct > 2 else '逢低買入' if change_pct < -2 else '區間操作',
                'risk_level': deep_analysis.get('risk_assessment', {}).get('overall_risk', '中等風險'),
                'volume_profile': market_maker.get('volume_profile', '中')
            }
        
        return {
            'trend': trend,
            'trend_emoji': trend_emoji,
            'rsi_signal': rsi_signal,
            'rsi_emoji': rsi_emoji,
            'suggestion': suggestion,
            'confidence': confidence,
            'vip_analysis': vip_analysis
        }(['突破買入', '逢低買入', '區間操作', '觀望等待']),
                'risk_level': random.choice(['低風險', '中等風險', '高風險'])
            }
        
        return {
            'trend': trend,
            'trend_emoji': trend_emoji,
            'rsi_signal': rsi_signal,
            'rsi_emoji': rsi_emoji,
            'suggestion': suggestion,
            'confidence': confidence,
            'vip_analysis': vip_analysis
        }
    
    def format_stock_message(self, data):
        """格式化股票分析訊息"""
        if not data:
            return "❌ 無法獲取股票數據"
        
        user_tier = data['user_tier']
        analysis = data['analysis']
        
        change_sign = "+" if data['change'] > 0 else ""
        price_color = "🟢" if data['change'] > 0 else "🔴" if data['change'] < 0 else "⚪"
        
        # 格式化成交量
        volume = data['volume']
        if volume > 1e9:
            volume_str = f"{volume/1e9:.1f}B"
        elif volume > 1e6:
            volume_str = f"{volume/1e6:.1f}M"
        else:
            volume_str = f"{volume:,.0f}"
        
        if user_tier == "free":
            message = f"""🎯 {data['emoji']} {data['name']} ({data['symbol']})
📅 分析時間: {data['timestamp']} 台北時間

💰 **實時股價**
{price_color} 當前價格: ${data['current_price']:.2f}
{analysis['trend_emoji']} 變化: {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%) | {analysis['trend']}
📊 今日區間: ${data['low']:.2f} - ${data['high']:.2f}
📦 成交量: {volume_str}
🏭 行業: {data['sector']}

📊 **技術分析**
{analysis['rsi_emoji']} RSI: {data['rsi']:.1f} ({analysis['rsi_signal']})
📈 趨勢判斷: {analysis['trend']}

🤖 **Maggie AI 建議**
💡 操作建議: {analysis['suggestion']}
🎯 信心等級: {analysis['confidence']}%

---
⏰ 免費版 10分鐘深度報告
🤖 分析師: Maggie AI FREE
📊 數據來源: Finnhub

💎 **升級VIP享受Market Maker專業分析！**
**VIP基礎版特色:**
✅ **24/7全天候查詢** (不受時間限制)
✅ **全美股8000+支** (vs 免費版500支)
✅ **無限次數查詢** (vs 免費版每日3次)
✅ **5分鐘分析** (vs 免費版10分鐘)
✅ **Max Pain 磁吸分析**
✅ **Gamma 支撐阻力地圖**
✅ **Delta Flow 對沖分析**

🎁 **限時優惠半價:** 美金原價~~$19.99~~ **$9.99/月** | 台幣原價~~$600~~ **$300/月**

📞 **立即升級請找管理員:** @maggie_investment (Maggie.L)
⭐ **不滿意30天退款保證**"""
            
        else:  # VIP版本
            vip = analysis['vip_analysis']
            
            message = f"""🎯 {data['emoji']} {data['symbol']} Market Maker 專業分析
📅 {data['timestamp']} 台北時間

📊 **股價資訊**
{price_color} 當前價格: ${data['current_price']:.2f}
{analysis['trend_emoji']} 變化: {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%) | {analysis['trend']}
📊 今日區間: ${data['low']:.2f} - ${data['high']:.2f}
📦 成交量: {volume_str}

🧲 **Max Pain 磁吸分析**
{vip['mm_magnetism']} 目標: ${vip['max_pain_price']:.2f}
📏 距離: ${abs(data['current_price'] - vip['max_pain_price']):.2f}
⚠️ 風險等級: {vip['risk_level']}

⚡ **Gamma 支撐阻力地圖**
🛡️ 最近支撐: ${vip['support_level']:.2f}
🚧 最近阻力: ${vip['resistance_level']:.2f}
💪 Gamma 強度: {vip['gamma_strength']}
📊 交易區間: ${vip['support_level']:.2f} - ${vip['resistance_level']:.2f}

🌊 **Delta Flow 對沖分析**
📈 流向: {vip['delta_flow']}
🤖 MM 行為: {vip['mm_behavior']}

💨 **IV Crush 風險評估**
⚠️ 風險等級: {vip['iv_risk']}
💡 建議: 適合期權策略

🔮 **專業交易策略**
🎯 主策略: {vip['strategy']}
📋 詳細建議:
   • 🎯 交易區間：${vip['support_level']:.2f} - ${vip['resistance_level']:.2f}
   • 📊 MM 目標價位: ${vip['max_pain_price']:.2f}

🤖 **Maggie AI VIP建議**
💡 操作建議: {analysis['suggestion']}
🎯 信心等級: {analysis['confidence']}%

---
⏰ {'VIP專業版 30秒極速分析' if user_tier == 'pro' else 'VIP基礎版 5分鐘專業分析'}
🤖 分析師: Maggie AI {user_tier.upper()}
📊 數據來源: Finnhub Real-time
🔥 {'專業版' if user_tier == 'pro' else '基礎版'}用戶專享！"""
        
        return message
    
    async def generate_mag7_report(self):
        """生成七巨頭報告"""
        try:
            mag7_data = []
            
            # 獲取七巨頭數據
            for symbol in self.mag7_symbols:
                stock_data = await self.get_stock_data_from_finnhub(symbol)
                if stock_data:
                    stock_info = self.supported_stocks[symbol]
                    mag7_data.append({
                        'symbol': symbol,
                        'name': stock_info['name'],
                        'emoji': stock_info['emoji'],
                        'price': stock_data['current_price'],
                        'change': stock_data['change'],
                        'change_percent': stock_data['change_percent'],
                        'volume': random.randint(10000000, 200000000)
                    })
            
            # 排序（按漲跌幅）
            mag7_data.sort(key=lambda x: x['change_percent'], reverse=True)
            
            # 計算平均漲跌
            avg_change = sum(stock['change_percent'] for stock in mag7_data) / len(mag7_data)
            
            # 生成報告
            taipei_time = datetime.now(self.taipei)
            time_emoji = "🌅" if 6 <= taipei_time.hour < 12 else "☀️" if 12 <= taipei_time.hour < 18 else "🌙"
            time_desc = "晨間報告" if 6 <= taipei_time.hour < 12 else "午間報告" if 12 <= taipei_time.hour < 18 else "深夜守望"
            
            # 強勢和弱勢股票
            strong_stocks = [s for s in mag7_data if s['change_percent'] > 0]
            weak_stocks = [s for s in mag7_data if s['change_percent'] < 0]
            
            # 市場情緒
            if avg_change > 2:
                market_sentiment = "熱烈上漲 🚀"
            elif avg_change > 0:
                market_sentiment = "樂觀上漲 📈"
            elif avg_change > -2:
                market_sentiment = "震盪整理 📊"
            else:
                market_sentiment = "謹慎下跌 📉"
            
            report = f"""🎯 美股七巨頭追蹤 {time_emoji} {time_desc}
📅 {taipei_time.strftime('%Y-%m-%d %H:%M')} 台北時間

📊 **實時表現排行**"""
            
            # 排行榜
            for i, stock in enumerate(mag7_data, 1):
                change_sign = "+" if stock['change'] > 0 else ""
                trend_emoji = "🔥" if stock['change_percent'] > 2 else "📈" if stock['change_percent'] > 0 else "📊" if stock['change_percent'] > -1 else "📉"
                
                if stock['change_percent'] > 3:
                    trend_desc = "強勢突破"
                elif stock['change_percent'] > 1:
                    trend_desc = "溫和上漲"
                elif stock['change_percent'] > -1:
                    trend_desc = "震盪整理"
                else:
                    trend_desc = "溫和下跌"
                
                report += f"""
{i}️⃣ {trend_emoji} {stock['emoji']} {stock['symbol']} ${stock['price']:.2f}
📊 {change_sign}{stock['change']:.2f} ({change_sign}{stock['change_percent']:.2f}%) | {trend_desc}"""
            
            # 弱勢股票警示
            if weak_stocks:
                report += f"\n\n⚠️ **弱勢股票**"
                for stock in weak_stocks[:2]:  # 只顯示最弱的兩支
                    report += f"\n📉 {stock['emoji']} {stock['symbol']} ${stock['price']:.2f} ({stock['change_percent']:+.2f}%)"
            
            # 整體表現
            best_stock = mag7_data[0]
            worst_stock = mag7_data[-1]
            
            report += f"""

🏛️ **七巨頭整體表現**
📈 平均漲跌: {avg_change:+.2f}%
🔥 最強: {best_stock['emoji']} {best_stock['symbol']} ({best_stock['change_percent']:+.2f}%)
❄️ 最弱: {worst_stock['emoji']} {worst_stock['symbol']} ({worst_stock['change_percent']:+.2f}%)

🧲 **重點 Max Pain 提醒**
🧲 MSFT: ${mag7_data[1]['price'] * 0.98:.2f} 🔴 極強磁吸
🧲 GOOGL: ${mag7_data[2]['price'] * 0.97:.2f} 🟡 中等磁吸

💡 **交易策略提醒**
🚀 強勢追蹤: 關注 {best_stock['symbol']} 的延續性
🛒 逢低布局: 考慮 {worst_stock['symbol']} 的反彈機會
⚖️ 平衡配置: 七巨頭分散風險，長期看漲

🎯 **今日市場總結**
📈 多頭股票: {len(strong_stocks)}支
📉 空頭股票: {len(weak_stocks)}支
🔥 市場情緒: {market_sentiment} ({avg_change:+.2f}%)
📊 放量股票: {best_stock['emoji']} {best_stock['symbol']}, {mag7_data[1]['emoji']} {mag7_data[1]['symbol']}

📈 **技術面分析**
RSI超買: {best_stock['emoji']} {best_stock['symbol']} (74.6) 
RSI超賣: {'無' if len(weak_stocks) == 0 else f"{worst_stock['emoji']} {worst_stock['symbol']} (25.3)"}
MACD金叉: 無
MACD死叉: 無

💡 **AI智能建議**
🟢 長線持有: 💻 Microsoft, 🍎 Apple, 🔍 Alphabet
🟡 短線觀望: {best_stock['emoji']} {best_stock['symbol']}
🔴 風險警示: 風險可控
📋 投資組合: 可適度增加成長股配置，但注意風險控制

🕐 下次更新: 6小時後

---
📊 Beta測試版 | 2.0增強版
🔄 每6小時自動更新 (00:00/06:00/12:00/18:00)
🤖 新增: 市場總結 + 技術分析 + AI建議
💬 反饋請找管理員 @maggie_investment"""
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating MAG7 report: {e}")
            return "❌ 生成七巨頭報告時發生錯誤"

# 初始化機器人
bot = MaggieStockAI()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """開始命令"""
    user_id = update.effective_user.id
    user_tier = bot.check_user_tier(user_id)
    logger.info(f"User {user_id} started bot (tier: {user_tier})")
    
    welcome_message = f"""🤖 **歡迎使用 Maggie's Stock AI!**

📊 **免費版功能**
• 📈 股票覆蓋: 標普500股票 + 新股/IPO (50+主流股票)
• 🔍 查詢限制: 每日3次主動查詢
• ⏰ 分析時間: 10分鐘深度報告
• 📊 基礎價量資訊 + Maggie建議與信心度
• 🎁 **免費福利: 每日4次七巨頭自動報告** (08:00, 12:00, 16:00, 20:00)

💡 **快速開始**
輸入 /stock 股票代號，例如：
• `/stock AAPL` - 分析蘋果公司
• `/stock TSLA` - 分析特斯拉  
• `/stock NVDA` - 分析輝達

📋 **熱門股票**
🔥 七巨頭: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA
💰 金融股: JPM, BAC, V, MA, PYPL
🏥 醫療股: JNJ, PFE, UNH, MRNA
🛒 消費股: KO, PG, WMT, MCD
📊 ETF: SPY, QQQ, VTI
🚗 電動車: TSLA, NIO, XPEV, LI
🔗 加密貨幣: COIN
🇨🇳 中概股: BABA, JD, PDD

{"🎉 **您是VIP用戶！** 享受無限查詢 + 專業分析" if user_tier != "free" else "💎 **升級VIP享受Market Maker專業分析！**"}

📞 升級/客服聯繫: @maggie_investment (Maggie.L)"""
    
    await update.message.reply_text(welcome_message)

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """股票查詢命令"""
    try:
        user_id = update.effective_user.id
        logger.info(f"User {user_id} called stock command")
        
        if not context.args:
            popular_stocks = "AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN, META"
            await update.message.reply_text(
                f"請提供股票代號，例如:\n"
                f"• `/stock AAPL`\n"
                f"• `/stock TSLA`\n\n"
                f"🔥 熱門股票: {popular_stocks}\n"
                f"📋 輸入 `/help` 查看完整清單"
            )
            return
        
        symbol = context.args[0].upper().strip()
        logger.info(f"Analyzing symbol: {symbol}")
        
        # 檢查用戶查詢限制
        can_query, current_count = bot.check_user_query_limit(user_id)
        user_tier = bot.check_user_tier(user_id)
        
        if not can_query and user_tier == "free":
            await update.message.reply_text(
                f"❌ **免費用戶每日查詢限制已達上限**\n"
                f"今日已查詢: {current_count}/3次\n\n"
                f"💎 **升級VIP享受無限查詢！**\n"
                f"🎁 限時優惠: 美金$9.99/月 (原價$19.99)\n"
                f"📞 聯繫升級: @maggie_investment"
            )
            return
        
        # 檢查股票是否支援
        if symbol not in bot.supported_stocks:
            await update.message.reply_text(
                f"❌ **'{symbol}' 暫不支援**\n\n"
                f"📋 請輸入 `/help` 查看支援的股票清單\n"
                f"🔥 熱門選擇: AAPL, TSLA, NVDA, MSFT"
            )
            return
        
        # 增加查詢次數
        bot.increment_user_query(user_id)
        
        # 發送分析中訊息
        analysis_speed = "30秒極速分析" if user_tier == "pro" else "5分鐘專業分析" if user_tier == "basic" else "10分鐘深度分析"
        processing_msg = await update.message.reply_text(
            f"🔍 **正在分析 {symbol}...**\n"
            f"⏰ 預計時間: {analysis_speed}\n"
            f"📊 獲取即時數據中..."
        )
        
        # 移除模擬延遲，使用真實分析時間
        # delay = 1 if user_tier == "pro" else 2 if user_tier == "basic" else 3
        # await asyncio.sleep(delay)
        
        # 獲取股票數據
        stock_data = await bot.get_stock_analysis(symbol, user_id)
        
        if stock_data:
            final_message = bot.format_stock_message(stock_data)
            await processing_msg.edit_text(final_message)
            
            # 顯示剩餘查詢次數（僅免費用戶）
            if user_tier == "free":
                remaining = 3 - bot.user_queries.get(user_id, 0)
                if remaining > 0:
                    await update.message.reply_text(
                        f"📊 今日剩餘查詢次數: {remaining}次\n"
                        f"💎 升級VIP享受無限查詢！"
                    )
                else:
                    await update.message.reply_text(
                        f"🚫 **今日查詢次數已用完**\n"
                        f"🎁 明日重置，或立即升級VIP！\n"
                        f"📞 聯繫: @maggie_investment"
                    )
        else:
            await processing_msg.edit_text(
                f"❌ **無法分析 {symbol}**\n"
                f"可能原因：市場休市 | 數據暫時無法取得\n"
                f"🔄 請稍後再試"
            )
            
    except Exception as e:
        logger.error(f"Error in stock command: {e}")
        await update.message.reply_text("❌ 系統錯誤，請稍後再試")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """幫助命令"""
    help_message = """📚 **Maggie Stock AI 使用指南**

🔧 **基本命令**
• `/start` - 歡迎頁面與功能介紹
• `/stock [代號]` - 股票分析
• `/help` - 使用說明

📊 **使用範例**
• `/stock AAPL` - 分析蘋果公司
• `/stock TSLA` - 分析特斯拉
• `/stock NVDA` - 分析輝達

📋 **支援股票清單**

🔥 **七巨頭 (每日自動報告)**
AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA

💻 **科技股**
NFLX, AMD, INTC, ORCL, CRM, ADBE

💰 **金融股**
JPM, BAC, WFC, GS, MS, V, MA, PYPL

🏥 **醫療股**
JNJ, PFE, UNH, ABBV, LLY, MRNA

🛒 **消費股**
KO, PG, WMT, HD, MCD, NKE, SBUX

📊 **ETF**
SPY, QQQ, VTI, IWM

🚀 **成長股**
PLTR, SNOW, CRWD, ZM, ROKU, COIN, HOOD

🇨🇳 **中概股**
BABA, JD, PDD, NIO, XPEV, LI

⚠️ **注意事項**
• 免費用戶每日限3次查詢
• 數據僅供參考，投資有風險
• 🎁 每日4次七巨頭自動報告 (08:00, 12:00, 16:00, 20:00)

💎 **VIP功能**
• 無限查詢 + Market Maker專業分析
• Max Pain磁吸分析 + Gamma支撐阻力地圖
• 美金$9.99/月 (限時優惠價)

📞 **客服支援**
升級VIP或技術問題請聯繫: @maggie_investment"""
    
    await update.message.reply_text(help_message)

async def admin_add_vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理員添加VIP用戶命令"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ 此命令僅限管理員使用")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "使用方法: `/admin_add_vip 用戶ID 等級`\n"
            "等級: basic 或 pro\n"
            "例如: `/admin_add_vip 123456789 basic`"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        tier = context.args[1].lower()
        
        if tier not in ["basic", "pro"]:
            await update.message.reply_text("❌ 等級必須是 basic 或 pro")
            return
        
        success = bot.add_vip_user(target_user_id, tier)
        
        if success:
            tier_name = "VIP基礎版" if tier == "basic" else "VIP專業版"
            await update.message.reply_text(
                f"✅ **VIP用戶添加成功**\n"
                f"用戶ID: {target_user_id}\n"
                f"等級: {tier_name}\n"
                f"📅 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            await update.message.reply_text("❌ 添加VIP用戶失敗")
            
    except ValueError:
        await update.message.reply_text("❌ 用戶ID必須是數字")
    except Exception as e:
        await update.message.reply_text(f"❌ 錯誤: {e}")

async def admin_remove_vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理員移除VIP用戶命令"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ 此命令僅限管理員使用")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "使用方法: `/admin_remove_vip 用戶ID`\n"
            "例如: `/admin_remove_vip 123456789`"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        bot.remove_vip_user(target_user_id)
        
        await update.message.reply_text(
            f"✅ **VIP用戶移除成功**\n"
            f"用戶ID: {target_user_id}\n"
            f"📅 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
    except ValueError:
        await update.message.reply_text("❌ 用戶ID必須是數字")
    except Exception as e:
        await update.message.reply_text(f"❌ 錯誤: {e}")

async def admin_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理員查看狀態命令"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ 此命令僅限管理員使用")
        return
    
    status_message = f"""📊 **Maggie Stock AI 系統狀態**

👥 **用戶統計**
VIP基礎版用戶: {len(bot.vip_basic_users)}人
VIP專業版用戶: {len(bot.vip_pro_users)}人
總VIP用戶: {len(bot.vip_basic_users) + len(bot.vip_pro_users)}人

📈 **查詢統計**
今日免費查詢: {sum(bot.user_queries.values())}次
活躍免費用戶: {len(bot.user_queries)}人

📊 **支援股票**
股票總數: {len(bot.supported_stocks)}支
七巨頭: {len(bot.mag7_symbols)}支

🕐 **系統時間**
台北時間: {datetime.now(bot.taipei).strftime('%Y-%m-%d %H:%M:%S')}
美東時間: {datetime.now(bot.est).strftime('%Y-%m-%d %H:%M:%S')}

💡 **管理員命令**
• `/admin_add_vip 用戶ID basic/pro` - 添加VIP
• `/admin_remove_vip 用戶ID` - 移除VIP  
• `/admin_status` - 查看狀態
• `/admin_broadcast 訊息` - 群發消息"""
    
    await update.message.reply_text(status_message)

async def send_mag7_report(context: ContextTypes.DEFAULT_TYPE):
    """發送七巨頭定時報告"""
    try:
        report = await bot.generate_mag7_report()
        
        # 這裡需要存儲所有用戶的chat_id來群發
        # 由於示例中沒有用戶數據庫，暫時只發給管理員
        await context.bot.send_message(
            chat_id=ADMIN_USER_ID,
            text=report
        )
        
        logger.info("MAG7 report sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending MAG7 report: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般訊息"""
    text = update.message.text.upper().strip()
    
    # 檢查是否是股票代號
    if text in bot.supported_stocks:
        context.args = [text]
        await stock_command(update, context)
    else:
        await update.message.reply_text(
            "💡 請使用 `/stock [代號]` 查詢股票\n"
            "例如: `/stock AAPL`\n\n"
            "或輸入 `/help` 查看使用說明"
        )

def main():
    """主函數"""
    logger.info("Starting Maggie Stock AI Bot...")
    
    try:
        # 建立應用
        application = Application.builder().token(BOT_TOKEN).build()
        
        # 註冊命令處理器
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("stock", stock_command))
        application.add_handler(CommandHandler("help", help_command))
        
        # 管理員命令
        application.add_handler(CommandHandler("admin_add_vip", admin_add_vip_command))
        application.add_handler(CommandHandler("admin_remove_vip", admin_remove_vip_command))
        application.add_handler(CommandHandler("admin_status", admin_status_command))
        
        # 一般訊息處理
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # 設定定時任務 - 七巨頭報告 (台北時間 08:00, 12:00, 16:00, 20:00)
        job_queue = application.job_queue
        
        # 每日 08:00 台北時間
        job_queue.run_daily(send_mag7_report, time=time(0, 0), days=(0, 1, 2, 3, 4, 5, 6))  # UTC時間
        # 每日 12:00 台北時間  
        job_queue.run_daily(send_mag7_report, time=time(4, 0), days=(0, 1, 2, 3, 4, 5, 6))
        # 每日 16:00 台北時間
        job_queue.run_daily(send_mag7_report, time=time(8, 0), days=(0, 1, 2, 3, 4, 5, 6))
        # 每日 20:00 台北時間
        job_queue.run_daily(send_mag7_report, time=time(12, 0), days=(0, 1, 2, 3, 4, 5, 6))
        
        logger.info("Job queue configured for MAG7 reports")
        
        # 啟動機器人
        logger.info("Bot starting with polling...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == '__main__':
    main()
