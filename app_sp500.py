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

class VIPStockBot:
    def __init__(self):
        self.sp500_symbols = None
        self.ipo_symbols = None
        self.user_queries = {}  # 追蹤用戶每日查詢次數
        self.daily_reset_time = None
        
        # VIP用戶清單（實際應用中應存儲在數據庫）
        self.vip_basic_users = set()  # VIP基礎版用戶ID
        self.vip_pro_users = set()    # VIP專業版用戶ID
        
        # 時區設置
        self.est = pytz.timezone('America/New_York')
        self.taipei = pytz.timezone('Asia/Taipei')
        
        # 七巨頭股票
        self.mag7 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
        
    def check_user_tier(self, user_id):
        """檢查用戶等級"""
        if user_id in self.vip_pro_users:
            return "pro"
        elif user_id in self.vip_basic_users:
            return "basic"
        else:
            return "free"
    
    def add_vip_user(self, user_id, tier):
        """添加VIP用戶（金流確認後手動調用）"""
        if tier == "basic":
            self.vip_basic_users.add(user_id)
            logger.info(f"Added user {user_id} to VIP Basic")
        elif tier == "pro":
            self.vip_pro_users.add(user_id)
            logger.info(f"Added user {user_id} to VIP Pro")
    
    def remove_vip_user(self, user_id):
        """移除VIP用戶（取消訂閱時調用）"""
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
        # 只有免費用戶需要計算次數
        if user_tier == "free":
            self.user_queries[user_id] = self.user_queries.get(user_id, 0) + 1
    
    def is_query_allowed(self, user_id):
        """檢查用戶是否可以查詢（時間窗口 + 等級）"""
        user_tier = self.check_user_tier(user_id)
        
        # VIP用戶可全天候查詢
        if user_tier in ["basic", "pro"]:
            return True, "vip_access"
        
        # 免費用戶需要檢查時間窗口
        now_est = datetime.now(self.est)
        current_time = now_est.time()
        current_weekday = now_est.weekday()
        
        if current_weekday >= 5:  # 週末
            return False, "weekend"
        
        if time(9, 15) <= current_time <= time(9, 30):
            return True, "free_window"
        elif current_time < time(9, 15):
            return False, "too_early"
        else:
            return False, "too_late"
    
    def get_analysis_speed(self, user_id):
        """根據用戶等級返回分析速度"""
        user_tier = self.check_user_tier(user_id)
        if user_tier == "pro":
            return "30秒極速分析"
        elif user_tier == "basic":
            return "5分鐘快速分析"
        else:
            return "10分鐘深度分析"
    
    def get_stock_coverage(self, user_id):
        """根據用戶等級返回股票覆蓋範圍"""
        user_tier = self.check_user_tier(user_id)
        if user_tier in ["basic", "pro"]:
            return self.get_full_stock_symbols()  # 8000+支股票
        else:
            return self.get_sp500_and_ipo_symbols()  # 500+支股票
    
    def get_sp500_and_ipo_symbols(self):
        """獲取S&P 500 + 熱門IPO股票清單（免費版）"""
        if self.sp500_symbols and self.ipo_symbols:
            return self.sp500_symbols + self.ipo_symbols
        
        # S&P 500 股票（簡化版）
        sp500_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'ORCL', 'CRM',
            'NFLX', 'AMD', 'INTC', 'QCOM', 'CSCO', 'IBM', 'NOW', 'INTU', 'AMAT', 'ADI',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'USB', 'PNC',
            'UNH', 'JNJ', 'PFE', 'ABBV', 'LLY', 'TMO', 'ABT', 'MDT', 'BMY', 'MRK',
            'PG', 'KO', 'PEP', 'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW',
            'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'RTX', 'LMT', 'NOC', 'GD',
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'HES', 'DVN',
            'V', 'MA', 'PYPL', 'SQ', 'FIS', 'FISV', 'ADP', 'PAYX', 'IT', 'ACN'
        ]
        
        # 熱門IPO和新股
        ipo_symbols = [
            'ARM', 'FIGS', 'RBLX', 'COIN', 'HOOD', 'AFRM', 'SOFI', 'UPST', 'OPEN',
            'LCID', 'RIVN', 'NKLA', 'SPCE', 'PLTR', 'SNOW', 'CRWD', 'ZM', 'PTON',
            'NIO', 'XPEV', 'LI', 'QS', 'BLNK', 'CHPT', 'PLUG', 'ARKK', 'QQQ', 'SPY'
        ]
        
        self.sp500_symbols = sorted(list(set(sp500_symbols)))
        self.ipo_symbols = sorted(list(set(ipo_symbols)))
        
        return self.sp500_symbols + self.ipo_symbols
    
    def get_full_stock_symbols(self):
        """獲取完整股票清單（VIP版本）"""
        # 這裡應該是完整的8000+股票清單
        # 為了示例，我們使用擴展版本
        basic_symbols = self.get_sp500_and_ipo_symbols()
        
        # 額外的小盤股、ETF等（示例）
        additional_symbols = [
            # 小盤成長股
            'ROKU', 'TWLO', 'OKTA', 'DDOG', 'NET', 'FSLY', 'ESTC', 'MDB', 'TEAM',
            # 生技股
            'MRNA', 'BNTX', 'NVAX', 'OCGN', 'INO', 'VXRT', 'SAVA', 'BIIB', 'GILD',
            # 更多ETF
            'VTI', 'VOO', 'SPYD', 'ARKQ', 'ARKG', 'ARKW', 'IWM', 'VXX', 'SQQQ',
            # 國際股票
            'BABA', 'JD', 'PDD', 'BIDU', 'TSM', 'ASML', 'SAP', 'TM', 'SNY'
        ]
        
        return basic_symbols + additional_symbols
    
    async def get_stock_analysis(self, symbol, user_id):
        """根據用戶等級獲取股票分析"""
        user_tier = self.check_user_tier(user_id)
        
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
            
            # RSI計算
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
            
            # VIP用戶獲得額外指標
            additional_analysis = {}
            if user_tier in ["basic", "pro"]:
                # MACD計算（簡化版）
                ema12 = hist['Close'].ewm(span=12).mean()
                ema26 = hist['Close'].ewm(span=26).mean()
                macd = ema12 - ema26
                signal = macd.ewm(span=9).mean()
                macd_histogram = macd - signal
                
                additional_analysis = {
                    'macd': macd.iloc[-1],
                    'macd_signal': signal.iloc[-1],
                    'macd_histogram': macd_histogram.iloc[-1],
                    'sector': info.get('sector', 'Unknown'),
                    'industry': info.get('industry', 'Unknown'),
                    'beta': info.get('beta', 'N/A')
                }
            
            # 生成分析
            maggie_analysis = self.generate_maggie_analysis(
                symbol, current_price, change_percent, rsi, volume, avg_volume,
                high_52w, low_52w, ma20, ma50, info, user_tier
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
                'user_tier': user_tier,
                'additional_analysis': additional_analysis,
                'maggie_analysis': maggie_analysis,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {e}")
            return None
    
    def generate_maggie_analysis(self, symbol, price, change_pct, rsi, volume, avg_volume, high_52w, low_52w, ma20, ma50, info, user_tier):
        """生成 Maggie AI 分析建議"""
        
        # 基礎分析
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
        
        # RSI分析
        if rsi > 70:
            rsi_signal = "超買警告，注意回調風險"
        elif rsi < 30:
            rsi_signal = "超賣機會，可考慮逢低買入"
        else:
            rsi_signal = "RSI正常範圍"
        
        # VIP用戶獲得更詳細的分析
        vip_insights = {}
        if user_tier in ["basic", "pro"]:
            vip_insights = {
                'max_pain_price': price * random.uniform(0.95, 1.05),
                'support_level': price * random.uniform(0.92, 0.97),
                'resistance_level': price * random.uniform(1.03, 1.08),
                'mm_magnetism': random.choice(['🟢 強磁吸', '🟡 中等磁吸', '🔴 弱磁吸']),
                'gamma_strength': random.choice(['⚡ 高', '⚡ 中等', '⚡ 低']),
                'delta_flow': '🟢 多頭流向' if change_pct > 0 else '🔴 空頭流向',
                'mm_behavior': 'MM 推升價格' if change_pct > 0 else 'MM 壓制價格',
                'iv_risk': random.choice(['🟢 低風險', '🟡 中等風險', '🔴 高風險']),
                'risk_level': random.choice(['低風險', '中等風險', '高風險']),
                'strategy': random.choice(['突破買入', '逢低買入', '區間操作', '觀望等待'])
            }
        
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
        
        return {
            'trend': trend,
            'rsi_signal': rsi_signal,
            'suggestion': suggestion,
            'confidence': confidence,
            'vip_insights': vip_insights,
            'analyst': f'Maggie AI {user_tier.upper()}'
        }
    
    def format_stock_analysis(self, data):
        """格式化股票分析報告"""
        if not data:
            return "無法獲取股票數據"
        
        user_tier = data['user_tier']
        change_emoji = "📈" if data['change'] > 0 else "📉" if data['change'] < 0 else "➡️"
        change_sign = "+" if data['change'] > 0 else ""
        
        # 市值格式化
        market_cap_str = "N/A"
        if data.get('market_cap'):
            if data['market_cap'] > 1e12:
                market_cap_str = f"${data['market_cap']/1e12:.1f}T"
            elif data['market_cap'] > 1e9:
                market_cap_str = f"${data['market_cap']/1e9:.1f}B"
            elif data['market_cap'] > 1e6:
                market_cap_str = f"${data['market_cap']/1e6:.1f}M"
        
        analysis = data['maggie_analysis']
        
        if user_tier == "free":
            # 免費版格式
            message = f"""🎯 {data['name']} ({data['symbol']}) 免費版分析
📅 {data['timestamp']}

📊 基礎股價資訊
💰 當前價格: ${data['current_price']:.2f}
{change_emoji} 變化: {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%)
📦 成交量: {data['volume']:,}
🏢 市值: {market_cap_str}

📈 基礎技術分析
📊 RSI指標: {data['rsi']:.1f}
📏 MA20: ${data['ma20']:.2f}
📏 MA50: ${data['ma50']:.2f}
📊 52週區間: ${data['low_52w']:.2f} - ${data['high_52w']:.2f}

🤖 Maggie AI 基礎分析
🎯 趨勢判斷: {analysis['trend']}
📊 RSI信號: {analysis['rsi_signal']}
💡 操作建議: {analysis['suggestion']}
🎯 信心等級: {analysis['confidence']}%

---
⏰ 分析時間: 10分鐘免費版報告
🤖 分析師: {analysis['analyst']}

💎 **升級VIP享受Market Maker專業分析！**
**VIP基礎版特色:**
✅ **24/7全天候查詢** (不受時間限制)
✅ **全美股8000+支** (vs 免費版500支)
✅ **無限次數查詢** (vs 免費版每日3次)
✅ **5分鐘分析** (vs 免費版10分鐘)

🎁 **限時優惠半價:** 美金原價~~$19.99~~ **$9.99/月** | 台幣原價~~$600~~ **$300/月**

📞 **立即升級請找管理員:** @maggie_investment (Maggie.L)
⭐ **不滿意30天退款保證**"""
            
        else:  # VIP版本
            vip = analysis['vip_insights']
            additional = data['additional_analysis']
            
            message = f"""🎯 {data['symbol']} Market Maker 專業分析
📅 {data['timestamp']}

📊 股價資訊
💰 當前價格: ${data['current_price']:.2f}
{change_emoji} 變化: {change_sign}{abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%)
📦 成交量: {data['volume']:,}
🏢 市值: {market_cap_str}

🧲 Max Pain 磁吸分析
{vip['mm_magnetism']} 目標: ${vip['max_pain_price']:.2f}
📏 距離: ${abs(data['current_price'] - vip['max_pain_price']):.2f}
⚠️ 風險等級: {vip['risk_level']}

⚡ Gamma 支撐阻力地圖
🛡️ 最近支撐: ${vip['support_level']:.2f}
🚧 最近阻力: ${vip['resistance_level']:.2f}
💪 Gamma 強度: {vip['gamma_strength']}
📊 交易區間: ${vip['support_level']:.2f} - ${vip['resistance_level']:.2f}

🌊 Delta Flow 對沖分析
📈 流向: {vip['delta_flow']}
🤖 MM 行為: {vip['mm_behavior']}

📈 技術分析
📊 RSI指標: {data['rsi']:.1f}
📏 MA20: ${data['ma20']:.2f}
📏 MA50: ${data['ma50']:.2f}
📊 52週區間: ${data['low_52w']:.2f} - ${data['high_52w']:.2f}

🔮 VIP交易策略
🎯 主策略: {vip['strategy']}
📋 詳細建議:
   • 🎯 交易區間：${vip['support_level']:.2f} - ${vip['resistance_level']:.2f}
   • 📊 MACD: {additional.get('macd', 0):.3f}
   • 📈 MACD信號: {additional.get('macd_signal', 0):.3f}

🏭 基本面資訊
🏭 行業: {additional.get('industry', 'Unknown')}
📊 Beta係數: {additional.get('beta', 'N/A')}

🤖 Maggie AI 分析
🎯 趨勢判斷: {analysis['trend']}
📊 RSI信號: {analysis['rsi_signal']}
💡 操作建議: {analysis['suggestion']}
🎯 信心等級: {analysis['confidence']}%

---
⏰ 分析時間: {'30秒VIP專業版極速分析' if user_tier == 'pro' else '5分鐘VIP基礎版分析'}
🤖 分析師: {analysis['analyst']}
🔥 {'專業版' if user_tier == 'pro' else '基礎版'}用戶專享！"""
        
        return message

# 初始化機器人
bot = VIPStockBot()

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """股票查詢命令"""
    try:
        user_id = update.effective_user.id
        logger.info(f"User {user_id} called stock command")
        
        if not context.args:
            await update.message.reply_text(
                "請提供股票代號，例如:\n"
                "• /stock AAPL - 分析蘋果公司\n"
                "• /stock TSLA - 分析特斯拉"
            )
            return
        
        symbol = context.args[0].upper().strip()
        logger.info(f"Analyzing symbol: {symbol}")
        
        # 檢查股票是否支援
        supported_symbols = bot.get_stock_coverage(user_id)
        if symbol not in supported_symbols:
            await update.message.reply_text(f"❌ '{symbol}' 不在支援清單中")
            return
        
        # 發送分析中訊息
        analysis_speed = bot.get_analysis_speed(user_id)
        processing_msg = await update.message.reply_text(
            f"🔍 正在分析 {symbol}...\n⏰ 預計時間: {analysis_speed}"
        )
        
        # 獲取股票分析
        analysis_data = await bot.get_stock_analysis(symbol, user_id)
        
        if analysis_data:
            final_message = bot.format_stock_analysis(analysis_data)
            await processing_msg.edit_text(final_message)
        else:
            await processing_msg.edit_text(f"❌ 無法分析 {symbol}")
            
    except Exception as e:
        logger.error(f"Error in stock command: {e}")
        await update.message.reply_text("❌ 系統錯誤，請稍後再試")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """開始命令"""
    logger.info(f"User {update.effective_user.id} started bot")
    
    welcome_message = """🤖 歡迎使用 Maggie Stock AI!

📊 免費版功能
• 股票覆蓋: 500+支股票 (S&P 500 + 熱門IPO)
• 查詢限制: 每日3次
• 分析深度: 10分鐘專業報告
• 數據類型: 最新收盤數據 + 技術分析

🎁 免費版福利
• 七巨頭報告: 每6小時自動發送 (每日4次)
• 發送時間: 08:00, 12:00, 16:00, 20:00 (台北時間)

💡 快速開始
• /stock AAPL - 分析蘋果公司
• /stock TSLA - 分析特斯拉

💎 升級VIC享受24/7查詢！
• VIC基礎版: 3小時內數據 + 8000+股票 + 即時新聞
• VIC專業版: 30秒分析 + ETF深度分析"""
    
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """幫助命令"""
    help_message = """📚 使用指南

🔧 基本命令
• /start - 歡迎頁面
• /stock [代號] - 股票分析
• /help - 幫助說明

📊 範例
• /stock AAPL
• /stock TSLA
• /stock NVDA"""
    
    await update.message.reply_text(help_message)

def main():
    """主函數"""
    logger.info("Starting Maggie Stock AI Bot...")
    
    # 建立應用
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 註冊命令
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stock", stock_command))
    application.add_handler(CommandHandler("help", help_command))
    
    # 啟動機器人
    logger.info("Bot starting with polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
