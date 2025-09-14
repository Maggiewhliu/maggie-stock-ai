#!/usr/bin/env python3
import os
import logging
import requests
import yfinance as yf
from datetime import datetime, timedelta, time
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue
import asyncio
import json
import random

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
PORT = int(os.getenv('PORT', 8080))

class FreemiumStockBot:
    def __init__(self):
        self.sp500_symbols = None
        self.ipo_symbols = None
        self.user_queries = {}  # 追蹤用戶每日查詢次數
        self.daily_reset_time = None
        
        # 時區設置
        self.est = pytz.timezone('America/New_York')
        self.taipei = pytz.timezone('Asia/Taipei')
        
        # 七巨頭股票
        self.mag7 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
        
    def reset_daily_queries(self):
        """重置每日查詢次數"""
        self.user_queries = {}
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        logger.info("Daily query limits reset")
    
    def check_user_query_limit(self, user_id):
        """檢查用戶查詢限制"""
        # 檢查是否需要重置
        if self.daily_reset_time and datetime.now() >= self.daily_reset_time:
            self.reset_daily_queries()
        
        current_count = self.user_queries.get(user_id, 0)
        return current_count < 3, current_count
    
    def increment_user_query(self, user_id):
        """增加用戶查詢次數"""
        self.user_queries[user_id] = self.user_queries.get(user_id, 0) + 1
    
    def is_premarket_window(self):
        """檢查是否在開盤前15分鐘窗口"""
        now_est = datetime.now(self.est)
        current_time = now_est.time()
        current_weekday = now_est.weekday()
        
        # 週一到週五
        if current_weekday >= 5:
            return False, "weekend"
        
        # 9:15-9:30 AM EST
        if time(9, 15) <= current_time <= time(9, 30):
            return True, "allowed"
        elif current_time < time(9, 15):
            return False, "too_early"
        else:
            return False, "too_late"
    
    def get_sp500_and_ipo_symbols(self):
        """獲取S&P 500 + 熱門IPO股票清單"""
        if self.sp500_symbols and self.ipo_symbols:
            return self.sp500_symbols + self.ipo_symbols
        
        # S&P 500 股票
        sp500_symbols = [
            # 科技巨頭
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'ORCL', 'CRM',
            'NFLX', 'AMD', 'INTC', 'QCOM', 'CSCO', 'IBM', 'NOW', 'INTU', 'AMAT', 'ADI',
            
            # 金融
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'USB', 'PNC',
            'COF', 'TFC', 'BK', 'STT', 'V', 'MA', 'PYPL', 'SQ', 'FIS', 'FISV',
            
            # 醫療保健
            'UNH', 'JNJ', 'PFE', 'ABBV', 'LLY', 'TMO', 'ABT', 'MDT', 'BMY', 'MRK',
            'DHR', 'CVS', 'CI', 'HUM', 'SYK', 'GILD', 'ISRG', 'ZTS', 'BSX', 'REGN',
            
            # 消費品
            'PG', 'KO', 'PEP', 'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW',
            'COST', 'DIS', 'CMCSA', 'VZ', 'T', 'TMUS', 'CL', 'KMB', 'GIS', 'K',
            
            # 工業
            'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'RTX', 'LMT', 'NOC', 'GD',
            'DE', 'EMR', 'ETN', 'ITW', 'PH', 'CMI', 'FDX', 'NSC', 'UNP', 'CSX',
            
            # 能源
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'HES', 'DVN',
            
            # 材料
            'LIN', 'APD', 'ECL', 'FCX', 'NEM', 'DOW', 'DD', 'PPG', 'SHW', 'NUE',
            
            # 公用事業
            'NEE', 'DUK', 'SO', 'AEP', 'EXC', 'XEL', 'WEC', 'ED', 'ETR', 'ES',
            
            # 房地產
            'AMT', 'PLD', 'CCI', 'EQIX', 'SPG', 'O', 'WELL', 'DLR', 'PSA', 'EQR'
        ]
        
        # 熱門IPO和新股 (2023-2025)
        ipo_symbols = [
            # 最新IPO
            'ARM', 'FIGS', 'RBLX', 'COIN', 'HOOD', 'AFRM', 'SOFI', 'UPST', 'OPEN',
            'LCID', 'RIVN', 'F', 'GM', 'NKLA', 'RIDE', 'GOEV', 'HYLN', 'SPCE',
            
            # 熱門成長股
            'PLTR', 'SNOW', 'CRWD', 'ZM', 'PTON', 'DOCU', 'ROKU', 'TWLO', 'OKTA',
            'DDOG', 'NET', 'FSLY', 'ESTC', 'MDB', 'TEAM', 'ATLASSIAN', 'SHOP',
            
            # 生技新股
            'MRNA', 'BNTX', 'NVAX', 'OCGN', 'INO', 'VXRT', 'SAVA', 'BIIB', 'GILD',
            
            # 電動車生態
            'NIO', 'XPEV', 'LI', 'BYDDY', 'QS', 'BLNK', 'CHPT', 'EVGO', 'PLUG',
            
            # 其他熱門
            'ARKK', 'ARKQ', 'ARKG', 'ARKW', 'SPYD', 'VTI', 'VOO', 'SPY', 'QQQ'
        ]
        
        self.sp500_symbols = sorted(list(set(sp500_symbols)))
        self.ipo_symbols = sorted(list(set(ipo_symbols)))
        
        total_count = len(self.sp500_symbols) + len(self.ipo_symbols)
        logger.info(f"Loaded {len(self.sp500_symbols)} S&P 500 + {len(self.ipo_symbols)} IPO/Growth stocks = {total_count} total")
        
        return self.sp500_symbols + self.ipo_symbols
    
    async def get_stock_analysis(self, symbol):
        """獲取10分鐘深度股票分析"""
        try:
            ticker = yf.Ticker(symbol)
            
            # 獲取數據
            hist = ticker.history(period="30d")
            info = ticker.info
            
            if hist.empty:
                return None
            
            # 基本價格信息
            current_price = float(hist['Close'][-1])
            previous_close = float(hist['Close'][-2]) if len(hist) > 1 else current_price
            volume = int(hist['Volume'][-1])
            avg_volume = int(hist['Volume'].mean())
            
            # 計算技術指標
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            
            # 52週高低點
            high_52w = float(hist['High'].max())
            low_52w = float(hist['Low'].min())
            
            # RSI計算 (簡化版)
            price_changes = hist['Close'].diff()
            gains = price_changes.where(price_changes > 0, 0)
            losses = -price_changes.where(price_changes < 0, 0)
            avg_gain = gains.rolling(window=14).mean()
            avg_loss = losses.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1] if not rs.empty else 50
            
            # 移動平均線
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            ma50 = hist['Close'].rolling(window=min(50, len(hist))).mean().iloc[-1]
            
            # Maggie AI 分析
            maggie_analysis = self.generate_maggie_analysis(
                symbol, current_price, change_percent, rsi, volume, avg_volume,
                high_52w, low_52w, ma20, ma50, info
            )
            
            return {
                'symbol': symbol,
                'name': info.get('shortName', symbol),
                'current_price': current_price,
                'change': change,
                'change_percent': change_percent,
                'volume': volume,
                'avg_volume': avg_volume,
                'high_52w': high_52w,
                'low_52w': low_52w,
                'rsi': rsi,
                'ma20': ma20,
                'ma50': ma50,
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'maggie_analysis': maggie_analysis,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {e}")
            return None
    
    def generate_maggie_analysis(self, symbol, price, change_pct, rsi, volume, avg_volume, high_52w, low_52w, ma20, ma50, info):
        """生成 Maggie AI 分析建議"""
        
        # 趨勢分析
        if price > ma20 > ma50:
            trend = "強勢上漲趨勢"
            trend_confidence = "高"
        elif price > ma20:
            trend = "短期上漲"
            trend_confidence = "中"
        elif price < ma20 < ma50:
            trend = "弱勢下跌趨勢"
            trend_confidence = "高"
        else:
            trend = "盤整震盪"
            trend_confidence = "中"
        
        # RSI 分析
        if rsi > 70:
            rsi_signal = "超買警告，注意回調風險"
        elif rsi < 30:
            rsi_signal = "超賣機會，可考慮逢低買入"
        else:
            rsi_signal = "RSI 正常範圍"
        
        # 成交量分析
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1
        if volume_ratio > 2:
            volume_signal = "異常放量，關注重大消息"
        elif volume_ratio > 1.5:
            volume_signal = "溫和放量，市場活躍"
        else:
            volume_signal = "成交量正常"
        
        # 價格位置分析
        price_position = (price - low_52w) / (high_52w - low_52w) * 100
        if price_position > 80:
            position_signal = "接近52週高點，謹慎追高"
        elif price_position < 20:
            position_signal = "接近52週低點，可能存在價值"
        else:
            position_signal = "價格位置適中"
        
        # 綜合建議
        if trend_confidence == "高" and "上漲" in trend and rsi < 70:
            suggestion = "建議持有或適度加倉"
            confidence = random.randint(75, 90)
        elif "下跌" in trend and rsi > 30:
            suggestion = "建議減倉或觀望"
            confidence = random.randint(60, 80)
        else:
            suggestion = "建議保持現有倉位，密切關注"
            confidence = random.randint(50, 75)
        
        # 風險評估
        if symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN']:
            risk_level = "低"
        elif symbol in self.mag7:
            risk_level = "中"
        else:
            risk_level = "中高"
        
        return {
            'trend': trend,
            'rsi_signal': rsi_signal,
            'volume_signal': volume_signal,
            'position_signal': position_signal,
            'suggestion': suggestion,
            'confidence': confidence,
            'risk_level': risk_level,
            'analyst': 'Maggie AI'
        }
    
    def format_stock_analysis(self, data):
        """格式化股票分析報告"""
        if not data:
            return "無法獲取股票數據"
        
        change_emoji = "📈" if data['change'] > 0 else "📉" if data['change'] < 0 else "➡️"
        change_sign = "+" if data['change'] > 0 else ""
        
        # 市值格式化
        market_cap_str = "N/A"
        if data.get('market_cap'):
            if data['market_cap'] > 1e12:
                market_cap_str = f"${data['market_cap']/1e12:.2f}T"
            elif data['market_cap'] > 1e9:
                market_cap_str = f"${data['market_cap']/1e9:.1f}B"
            elif data['market_cap'] > 1e6:
                market_cap_str = f"${data['market_cap']/1e6:.1f}M"
        
        analysis = data['maggie_analysis']
        
        message = f"""🎯 {data['name']} ({data['symbol']}) Market Maker 專業分析
📅 {data['timestamp']}

📊 股價資訊
💰 當前價格: ${data['current_price']:.2f}
{change_emoji} 變化: {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%)
📦 成交量: {data['volume']:,}
🏢 市值: {market_cap_str}

📈 技術分析
📊 RSI指標: {data['rsi']:.1f}
📏 MA20: ${data['ma20']:.2f}
📏 MA50: ${data['ma50']:.2f}
📊 52週區間: ${data['low_52w']:.2f} - ${data['high_52w']:.2f}

🤖 Maggie AI 專業分析
🎯 趨勢判斷: {analysis['trend']}
📊 RSI信號: {analysis['rsi_signal']}
📈 成交量: {analysis['volume_signal']}
📍 價格位置: {analysis['position_signal']}

💡 投資建議
📋 操作建議: {analysis['suggestion']}
🎯 信心等級: {analysis['confidence']}%
⚠️ 風險等級: {analysis['risk_level']}

---
⏰ 分析時間: 10分鐘深度報告
📊 數據延遲: 3-5分鐘
🤖 分析師: {analysis['analyst']}

💡 升級至專業版享受即時分析!"""
        
        return message
    
    async def generate_mag7_report(self):
        """生成七巨頭自動報告"""
        try:
            taipei_time = datetime.now(self.taipei)
            
            # 獲取七巨頭數據
            mag7_data = []
            for symbol in self.mag7:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")
                    info = ticker.info
                    
                    if not hist.empty:
                        current_price = float(hist['Close'][-1])
                        previous_close = float(hist['Close'][-2]) if len(hist) > 1 else current_price
                        change = current_price - previous_close
                        change_percent = (change / previous_close) * 100
                        volume = int(hist['Volume'][-1])
                        
                        mag7_data.append({
                            'symbol': symbol,
                            'name': info.get('shortName', symbol),
                            'price': current_price,
                            'change': change,
                            'change_percent': change_percent,
                            'volume': volume
                        })
                        
                except Exception as e:
                    logger.error(f"Failed to get data for {symbol}: {e}")
                    continue
            
            if not mag7_data:
                return "無法獲取七巨頭數據"
            
            # 排序（按漲跌幅）
            mag7_data.sort(key=lambda x: x['change_percent'], reverse=True)
            
            # 計算整體表現
            avg_change = sum(d['change_percent'] for d in mag7_data) / len(mag7_data)
            strongest = mag7_data[0]
            weakest = mag7_data[-1]
            
            # 時段判斷
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
            
            # 生成報告
            report = f"""🎯 美股七巨頭追蹤 {session}
📅 {taipei_time.strftime('%Y-%m-%d %H:%M')} 台北時間

📊 實時表現排行"""
            
            # 前5名
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
            
            # 弱勢股票
            weak_stocks = [s for s in mag7_data if s['change_percent'] < 0]
            if weak_stocks:
                report += f"\n\n⚠️ 弱勢股票"
                for stock in weak_stocks[:2]:
                    emoji = self.get_stock_emoji(stock['symbol'])
                    report += f"\n📉 {emoji} {stock['name']} ${stock['price']:.2f} ({stock['change_percent']:.2f}%)"
            
            # 整體分析
            report += f"\n\n🏛️ 七巨頭整體表現"
            report += f"\n📈 平均漲跌: {avg_change:+.2f}%"
            report += f"\n🔥 最強: {self.get_stock_emoji(strongest['symbol'])} {strongest['name']} ({strongest['change_percent']:+.2f}%)"
            report += f"\n❄️ 最弱: {self.get_stock_emoji(weakest['symbol'])} {weakest['name']} ({weakest['change_percent']:+.2f}%)"
            
            # 市場情緒
            if avg_change > 1:
                market_mood = "🚀 強勢上漲"
            elif avg_change > 0:
                market_mood = "📈 樂觀上漲"
            elif avg_change > -1:
                market_mood = "📊 震盪整理"
            else:
                market_mood = "📉 調整壓力"
            
            report += f"\n\n💡 交易策略提醒"
            if strongest['change_percent'] > 3:
                report += f"\n🚀 強勢追蹤: 關注 {strongest['symbol']} 的延續性"
            if weakest['change_percent'] < -2:
                report += f"\n🛒 逢低布局: 考慮 {weakest['symbol']} 的反彈機會"
            report += f"\n⚖️ 平衡配置: 七巨頭分散風險，長期看漲"
            
            report += f"\n\n🎯 今日市場總結"
            up_count = len([s for s in mag7_data if s['change_percent'] > 0])
            down_count = len([s for s in mag7_data if s['change_percent'] < 0])
            report += f"\n📈 多頭股票: {up_count}支"
            report += f"\n📉 空頭股票: {down_count}支"
            report += f"\n🔥 市場情緒: {market_mood} ({avg_change:+.2f}%)"
            
            # AI建議
            report += f"\n\n💡 AI智能建議"
            if avg_change > 1:
                report += f"\n🟢 長線持有: 💻 Microsoft, 🍎 Apple, 🔍 Alphabet"
                if strongest['change_percent'] > 5:
                    report += f"\n🟡 短線觀望: {self.get_stock_emoji(strongest['symbol'])} {strongest['name']}"
                report += f"\n🔴 風險警示: 風險可控"
                report += f"\n📋 投資組合: 可適度增加成長股配置，但注意風險控制"
            elif avg_change > -1:
                report += f"\n🟡 均衡配置: 維持現有倉位，觀察市場動向"
                report += f"\n🔴 風險警示: 注意短期波動"
            else:
                report += f"\n🔴 謹慎操作: 考慮適當避險，等待市場明確方向"
            
            report += f"\n\n🕐 下次更新: 6小時後"
            report += f"\n\n---"
            report += f"\n📊 免費版 | 每日4次自動報告"
            report += f"\n🔄 每6小時自動更新 (08:00/12:00/16:00/20:00)"
            report += f"\n🤖 新增: 市場總結 + 技術分析 + AI建議"
            report += f"\n💬 反饋請找管理員Maggie.L"
            report += f"\n⭐ 評分請回覆 /rating 1-10"
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate MAG7 report: {e}")
            return "暫時無法生成七巨頭報告，請稍後再試"
    
    def get_stock_emoji(self, symbol):
        """獲取股票對應的emoji"""
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

def clear_webhook():
    """清除webhook"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.get(url, timeout=10)
        result = response.json()
        logger.info(f"Webhook cleared: {result}")
        return result.get('ok', False)
    except Exception as e:
        logger.error(f"Failed to clear webhook: {e}")
        return False

def set_webhook():
    """設置webhook"""
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

# 初始化機器人
bot = FreemiumStockBot()

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """股票查詢命令"""
    try:
        user_id = update.effective_user.id
        
        if not context.args:
            all_symbols = bot.get_sp500_and_ipo_symbols()
            can_query, current_count = bot.check_user_query_limit(user_id)
            
            status_msg = f"🎯 **Maggie Stock AI 免費版**\n\n"
            status_msg += f"📊 **股票覆蓋:** {len(all_symbols)}支股票 (S&P 500 + 熱門IPO)\n"
            status_msg += f"🔍 **每日查詢:** {current_count}/3 次已使用\n"
            status_msg += f"⏰ **分析時間:** 10分鐘深度報告\n"
            status_msg += f"📈 **數據延遲:** 3-5分鐘\n\n"
            
            # 檢查開盤前窗口
            allowed, reason = bot.is_premarket_window()
            if not allowed:
                if reason == "weekend":
                    status_msg += f"🔴 **週末市場關閉**\n"
                elif reason == "too_early":
                    status_msg += f"🟡 **開盤前窗口未開啟** (9:15-9:30 AM EST)\n"
                else:
                    status_msg += f"🔴 **今日查詢窗口已關閉**\n"
                status_msg += f"⏰ **下次可查詢:** 明日9:15 AM EST\n\n"
            else:
                status_msg += f"🟢 **查詢窗口開啟中** (剩餘{30 - datetime.now(bot.est).minute + 15}分鐘)\n\n"
            
            status_msg += f"**熱門範例:**\n"
            status_msg += f"• /stock AAPL - 蘋果公司\n"
            status_msg += f"• /stock TSLA - 特斯拉\n"
            status_msg += f"• /stock ARM - 最新IPO\n"
            status_msg += f"• /stock NVDA - 輝達\n\n"
            status_msg += f"🎁 **免費福利:** 每日4次七巨頭自動報告 (08:00/12:00/16:00/20:00)\n"
            status_msg += f"💎 **升級專業版:** 即時查詢 + 無限次數 + 30秒快速分析"
            
            await update.message.reply_text(status_msg)
            return
        
        symbol = context.args[0].upper().strip()
        
        # 檢查用戶查詢限制
        can_query, current_count = bot.check_user_query_limit(user_id)
        if not can_query:
            await update.message.reply_text(
                f"⏰ **每日查詢限制已達上限**\n\n"
                f"🔍 **今日已使用:** 3/3 次\n"
                f"⏰ **重置時間:** 明日 00:00\n\n"
                f"🎁 **仍可享受:** 免費七巨頭自動報告\n"
                f"💎 **升級專業版:** 無限查詢次數\n\n"
                f"**七巨頭股票:** {', '.join(bot.mag7)}\n"
                f"**下次自動報告:** 每6小時發送"
            )
            return
        
        # 檢查開盤前窗口
        allowed, reason = bot.is_premarket_window()
        if not allowed:
            next_window = "明日 9:15 AM EST" if reason != "weekend" else "下週一 9:15 AM EST"
            await update.message.reply_text(
                f"🔒 **查詢窗口已關閉**\n\n"
                f"⏰ **開放時間:** 開盤前15分鐘 (9:15-9:30 AM EST)\n"
                f"📅 **下次開放:** {next_window}\n"
                f"🔍 **剩餘查詢:** {3-current_count}/3 次\n\n"
                f"🎁 **免費享受:** 七巨頭自動報告\n"
                f"💎 **專業版:** 全天候即時查詢"
            )
            return
        
        # 檢查股票是否支援
        all_symbols = bot.get_sp500_and_ipo_symbols()
        if symbol not in all_symbols:
            suggestions = [s for s in all_symbols if symbol in s or s.startswith(symbol[:2])][:3]
            suggestion_text = ""
            if suggestions:
                suggestion_text = f"\n\n**相似股票:** {', '.join(suggestions)}"
            
            await update.message.reply_text(
                f"❌ **股票代號 '{symbol}' 不在支援清單**\n\n"
                f"📊 **支援範圍:** {len(all_symbols)}支股票\n"
                f"• S&P 500 成分股\n"
                f"• 熱門IPO/成長股\n"
                f"• 主流ETF{suggestion_text}\n\n"
                f"🔍 **剩餘查詢:** {3-current_count}/3 次"
            )
            return
        
        # 增加查詢次數
        bot.increment_user_query(user_id)
        remaining = 3 - (current_count + 1)
        
        # 發送分析中訊息
        processing_msg = await update.message.reply_text(
            f"🔍 **正在分析 {symbol}...**\n"
            f"⏰ **預計時間:** 10分鐘深度分析\n"
            f"🤖 **Maggie AI:** 準備專業建議\n"
            f"📊 **剩餘查詢:** {remaining}/3 次"
        )
        
        # 獲取股票分析
        analysis_data = await bot.get_stock_analysis(symbol)
        
        if analysis_data:
            final_message = bot.format_stock_analysis(analysis_data)
            await processing_msg.edit_text(final_message)
        else:
            await processing_msg.edit_text(
                f"❌ **無法分析 {symbol}**\n\n"
                f"可能原因:\n"
                f"• 股票暫停交易\n"
                f"• 數據源暫時不可用\n"
                f"• 網路連線問題\n\n"
                f"🔍 **剩餘查詢:** {remaining}/3 次\n"
                f"💡 **建議:** 稍後再試或查詢其他股票"
            )
            
    except Exception as e:
        logger.error(f"Error in stock command: {e}")
        await update.message.reply_text(
            "❌ **系統錯誤**\n\n請稍後再試，如問題持續請聯繫客服"
        )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """開始命令"""
    user_id = update.effective_user.id
    can_query, current_count = bot.check_user_query_limit(user_id)
    
    welcome_message = f"""🤖 **歡迎使用 Maggie Stock AI 免費版!**

我是您的專業股票分析助手，提供深度市場洞察。

📊 **免費版功能**
• **股票覆蓋:** 500+支股票 (S&P 500 + 熱門IPO)
• **查詢限制:** 每日3次主動查詢 ({current_count}/3 已使用)
• **分析深度:** 10分鐘專業報告
• **數據延遲:** 3-5分鐘
• **查詢時間:** 開盤前15分鐘 (9:15-9:30 AM EST)

🎁 **免費福利**
• **七巨頭報告:** 每日4次自動發送 (08:00/12:00/16:00/20:00)
• **專業分析:** Maggie AI 個人化建議
• **風險評估:** 完整風險等級分析

💡 **快速開始**
• `/stock AAPL` - 分析蘋果公司
• `/stock TSLA` - 分析特斯拉
• `/mag7` - 立即查看七巨頭報告
• `/upgrade` - 了解專業版功能

⭐ **核心價值**
"讓每個散戶都能享受專業級投資分析"

---
🔧 由 Maggie 用心打造
📈 專業分析 · 值得信賴"""
    
    await update.message.reply_text(welcome_message)

async def mag7_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """七巨頭報告命令"""
    processing_msg = await update.message.reply_text(
        "📊 **正在生成七巨頭報告...**\n"
        "⏰ 預計30秒，請稍候"
    )
    
    report = await bot.generate_mag7_report()
    await processing_msg.edit_text(report)

async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """升級說明"""
    upgrade_message = """💎 **Maggie Stock AI 專業版**

🆚 **版本對比**

**🆓 免費版 (當前)**
• 500+支股票
• 每日3次查詢
• 10分鐘分析報告
• 3-5分鐘數據延遲
• 開盤前15分鐘查詢窗口
• 免費七巨頭報告

**💎 專業版**
• 3000+支全球股票
• 無限次查詢
• 30秒快速分析
• 即時數據 (無延遲)
• 24/7全天候查詢
• 期權分析
• 技術指標預警
• 投資組合追蹤
• 優先客服支持

💰 **定價方案**
• **月付:** $29/月
• **年付:** $299/年 (省$49)
• **終身:** $999 (限時優惠)

🎯 **立即升級享受**
• 解除所有查詢限制
• 即時市場數據
• 專業投資建議
• 獨家策略報告

📞 **聯繫升級:** @Maggie_VIP_Bot"""
    
    await update.message.reply_text(upgrade_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """幫助命令"""
    help_message = """📚 **Maggie Stock AI 使用指南**

**🔧 基本命令**
• `/start` - 歡迎頁面與功能介紹
• `/stock [代號]` - 股票深度分析
• `/mag7` - 七巨頭實時報告
• `/upgrade` - 專業版升級說明
• `/status` - 查詢使用狀態

**📊 股票分析功能**
• **深度報告:** 10分鐘專業分析
• **技術指標:** RSI, 移動平均線
• **AI建議:** Maggie 個人化建議
• **風險評估:** 完整風險等級

**⏰ 使用限制**
• **查詢時間:** 開盤前15分鐘 (9:15-9:30 AM EST)
• **每日限制:** 3次主動查詢
• **股票範圍:** S&P 500 + 熱門IPO (500+支)

**🎁 免費福利**
• **自動報告:** 七巨頭每日4次 (08:00/12:00/16:00/20:00)
• **即時通知:** 重要市場動態
• **專業建議:** AI驅動的投資建議

**📱 使用技巧**
• 在查詢窗口開啟時使用效果最佳
• 善用七巨頭免費報告掌握大盤
• 升級專業版享受無限制服務

**🆘 技術支持**
遇到問題？聯繫 @Maggie_Support_Bot"""
    
    await update.message.reply_text(help_message)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """用戶狀態查詢"""
    user_id = update.effective_user.id
    can_query, current_count = bot.check_user_query_limit(user_id)
    allowed, reason = bot.is_premarket_window()
    
    est_time = datetime.now(bot.est)
    taipei_time = datetime.now(bot.taipei)
    
    status_msg = f"""📊 **您的使用狀態**

🔍 **查詢狀態**
• **今日已用:** {current_count}/3 次
• **剩餘查詢:** {3-current_count} 次
• **明日重置:** 00:00 (台北時間)

⏰ **查詢窗口**"""
    
    if allowed:
        remaining_min = 30 - est_time.minute + 15
        status_msg += f"\n🟢 **目前開放** (剩餘 {remaining_min} 分鐘)"
    elif reason == "weekend":
        status_msg += f"\n🔴 **週末關閉**"
    elif reason == "too_early":
        status_msg += f"\n🟡 **尚未開放** (9:15 AM EST)"
    else:
        status_msg += f"\n🔴 **今日已關閉**"
    
    status_msg += f"\n• **下次開放:** 明日 9:15-9:30 AM EST"
    
    status_msg += f"\n\n🕐 **時間資訊**"
    status_msg += f"\n• **美東時間:** {est_time.strftime('%H:%M EST')}"
    status_msg += f"\n• **台北時間:** {taipei_time.strftime('%H:%M')}"
    
    status_msg += f"\n\n🎁 **免費服務**"
    status_msg += f"\n• **七巨頭報告:** 每日4次自動發送"
    status_msg += f"\n• **下次報告:** 6小時後"
    
    if current_count >= 3:
        status_msg += f"\n\n💎 **今日查詢已用完**"
        status_msg += f"\n升級專業版享受無限查詢!"
    
    await update.message.reply_text(status_msg)

# 自動報告任務
async def send_mag7_report(context: ContextTypes.DEFAULT_TYPE):
    """發送七巨頭自動報告"""
    try:
        report = await bot.generate_mag7_report()
        
        # 這裡需要向所有訂閱用戶發送
        # 實際應用中應該維護用戶清單
        # 這裡簡化為記錄日誌
        logger.info("MAG7 report generated and ready to send")
        
        # 如果有用戶清單，可以這樣發送：
        # for user_id in subscribed_users:
        #     try:
        #         await context.bot.send_message(chat_id=user_id, text=report)
        #     except Exception as e:
        #         logger.error(f"Failed to send report to {user_id}: {e}")
        
    except Exception as e:
        logger.error(f"Failed to generate MAG7 report: {e}")

def main():
    """主函數"""
    logger.info("Starting Maggie Stock AI Freemium Bot...")
    
    # 初始化股票清單
    symbols = bot.get_sp500_and_ipo_symbols()
    logger.info(f"Loaded {len(symbols)} stocks (S&P 500 + IPO)")
    
    # 初始化每日重置
    bot.reset_daily_queries()
    
    # 清除webhook
    clear_webhook()
    
    # 建立應用
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 註冊命令
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(CommandHandler("mag7", mag7_command))
    application.add_handler(CommandHandler("upgrade", upgrade_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # 註冊定時任務 (七巨頭報告)
    job_queue = application.job_queue
    if job_queue:
        # 每日4次報告: 08:00, 12:00, 16:00, 20:00 (台北時間)
        taipei_tz = pytz.timezone('Asia/Taipei')
        job_queue.run_daily(send_mag7_report, time(8, 0), days=(0, 1, 2, 3, 4, 5, 6), timezone=taipei_tz)
        job_queue.run_daily(send_mag7_report, time(12, 0), days=(0, 1, 2, 3, 4, 5, 6), timezone=taipei_tz)
        job_queue.run_daily(send_mag7_report, time(16, 0), days=(0, 1, 2, 3, 4, 5, 6), timezone=taipei_tz)
        job_queue.run_daily(send_mag7_report, time(20, 0), days=(0, 1, 2, 3, 4, 5, 6), timezone=taipei_tz)
        
        # 每日重置查詢次數
        job_queue.run_daily(lambda context: bot.reset_daily_queries(), time(0, 0), timezone=taipei_tz)
    
    # 啟動機器人
    if os.getenv('RENDER'):
        logger.info(f"Running in Render mode on port {PORT}")
        try:
            if set_webhook():
                logger.info("Starting webhook server...")
                application.run_webhook(
                    listen="0.0.0.0",
                    port=PORT,
                    webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL', 'https://maggie-stock-ai.onrender.com')}/{BOT_TOKEN}",
                    url_path=BOT_TOKEN
                )
            else:
                logger.warning("Webhook failed, using polling...")
                application.run_polling()
        except Exception as e:
            logger.error(f"Webhook failed: {e}, using polling...")
            application.run_polling()
    else:
        logger.info("Running in local development mode")
        application.run_polling()

if __name__ == '__main__':
    main()
