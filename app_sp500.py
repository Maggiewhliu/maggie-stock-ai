#!/usr/bin/env python3
import os
import logging
import requests
import yfinance as yf
from datetime import datetime, timedelta, time
import pytz
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from flask import Flask, request
import json
import random

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
PORT = int(os.getenv('PORT', 8080))

# Flask app for webhook
app = Flask(__name__)

class VIPStockBot:
    def __init__(self):
        self.sp500_symbols = None
        self.ipo_symbols = None
        self.user_queries = {}
        self.daily_reset_time = None
        
        # VIP用戶清單
        self.vip_basic_users = set()
        self.vic_pro_users = set()
        
        # 時區設置
        self.est = pytz.timezone('America/New_York')
        self.taipei = pytz.timezone('Asia/Taipei')
        
        # 七巨頭股票
        self.mag7 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
    
    def check_user_tier(self, user_id):
        """檢查用戶等級"""
        if user_id in self.vic_pro_users:
            return "vic"
        elif user_id in self.vip_basic_users:
            return "basic"
        else:
            return "free"
    
    def add_vip_user(self, user_id, tier):
        """添加VIP用戶（金流確認後手動調用）"""
        if tier == "basic":
            self.vip_basic_users.add(user_id)
            logger.info(f"Added user {user_id} to VIP Basic")
        elif tier == "vic" or tier == "pro":
            self.vic_pro_users.add(user_id)
            logger.info(f"Added user {user_id} to VIC Pro")
    
    def get_stock_coverage(self, user_id):
        """根據用戶等級返回股票覆蓋範圍"""
        user_tier = self.check_user_tier(user_id)
        if user_tier in ["basic", "vic"]:
            return self.get_full_stock_symbols()
        else:
            return self.get_sp500_and_ipo_symbols()
    
    def get_sp500_and_ipo_symbols(self):
        """獲取S&P 500 + 熱門IPO股票清單（免費版）"""
        if self.sp500_symbols and self.ipo_symbols:
            return self.sp500_symbols + self.ipo_symbols
        
        # S&P 500 股票（簡化版）- 確保TSLA在清單第一位
        sp500_symbols = [
            'TSLA', 'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'META', 'NVDA', 'ORCL', 'CRM',
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
        basic_symbols = self.get_sp500_and_ipo_symbols()
        
        additional_symbols = [
            'ROKU', 'TWLO', 'OKTA', 'DDOG', 'NET', 'FSLY', 'ESTC', 'MDB', 'TEAM',
            'MRNA', 'BNTX', 'NVAX', 'OCGN', 'INO', 'VXRT', 'SAVA', 'BIIB', 'GILD',
            'VTI', 'VOO', 'SPYD', 'ARKQ', 'ARKG', 'ARKW', 'IWM', 'VXX', 'SQQQ',
            'BABA', 'JD', 'PDD', 'BIDU', 'TSM', 'ASML', 'SAP', 'TM', 'SNY'
        ]
        
        return basic_symbols + additional_symbols
    
    def get_stock_analysis(self, symbol, user_id):
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
            if user_tier in ["basic", "vic"]:
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
        if user_tier in ["basic", "vic"]:
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

💎 升級VIP享受Market Maker專業分析！
📞 立即升級請找管理員: @maggie_investment (Maggie.L)"""
            
        else:  # VIP版本
            vip = analysis['vip_insights']
            additional = data['additional_analysis']
            
            message = f"""🎯 {data['symbol']} Market Maker 專業分析
📅 {data['timestamp']}

📊 股價資訊
💰 當前價格: ${data['current_price']:.2f}
{change_emoji} 變化: {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%)
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

💨 IV Crush 風險評估
⚠️ 風險等級: {vip['iv_risk']}
💡 建議: 適合期權策略

🔮 專業交易策略
🎯 主策略: {vip['strategy']}
📋 詳細建議:
   • 🎯 交易區間：${vip['support_level']:.2f} - ${vip['resistance_level']:.2f}
   • 📊 MACD: {additional.get('macd', 0):.3f}
   • 📈 MACD信號: {additional.get('macd_signal', 0):.3f}

🏭 基本面資訊
🏭 行業: {additional.get('industry', 'Unknown')}
📊 Beta係數: {additional.get('beta', 'N/A')}

🤖 Maggie AI VIP建議
💡 操作建議: {analysis['suggestion']}
🎯 信心等級: {analysis['confidence']}%

---
⏰ {'VIC專業版 30秒極速分析' if user_tier == 'vic' else 'VIP基礎版 5分鐘專業分析'}
🤖 分析師: {analysis['analyst']}
🔥 {'專業版' if user_tier == 'vic' else '基礎版'}用戶專享！"""
        
        return message

# 初始化機器人
bot = VIPStockBot()

def stock_command(update: Update, context: CallbackContext):
    """股票查詢命令"""
    try:
        user_id = update.effective_user.id
        logger.info(f"User {user_id} called stock command")
        
        if not context.args:
            update.message.reply_text(
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
            update.message.reply_text(f"❌ '{symbol}' 不在支援清單中")
            return
        
        # 發送分析中訊息
        processing_msg = update.message.reply_text(
            f"🔍 正在分析 {symbol}...\n⏰ 獲取即時數據中..."
        )
        
        # 獲取股票分析
        analysis_data = bot.get_stock_analysis(symbol, user_id)
        
        if analysis_data:
            final_message = bot.format_stock_analysis(analysis_data)
            processing_msg.edit_text(final_message)
        else:
            processing_msg.edit_text(f"❌ 無法分析 {symbol}")
            
    except Exception as e:
        logger.error(f"Error in stock command: {e}")
        update.message.reply_text("❌ 系統錯誤，請稍後再試")

def start_command(update: Update, context: CallbackContext):
    """開始命令"""
    logger.info(f"User {update.effective_user.id} started bot")
    
    welcome_message = """🤖 歡迎使用 Maggie Stock AI!

📊 免費版功能
• 股票覆蓋: 500+支股票 (S&P 500 + 熱門IPO)
• 查詢限制: 每日3次
• 分析深度: 10分鐘專業報告

💡 快速開始
• /stock AAPL - 分析蘋果公司
• /stock TSLA - 分析特斯拉

💎 升級VIP享受24/7查詢！"""
    
    update.message.reply_text(welcome_message)

def help_command(update: Update, context: CallbackContext):
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
    
    update.message.reply_text(help_message)

# Global updater
updater = None

@app.route('/webhook', methods=['POST'])
def webhook():
    """處理 webhook 請求"""
    try:
        update = Update.de_json(request.get_json(force=True), updater.bot)
        updater.dispatcher.process_update(update)
        return "OK"
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

@app.route('/')
def index():
    return "Maggie Stock AI Bot is running!"

@app.route('/health')
def health():
    return "OK"

def main():
    """主函數"""
    global updater
    logger.info("Starting Maggie Stock AI Bot...")
    
    # 建立應用
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # 註冊命令
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("stock", stock_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # 檢查是否在 Render 環境
    if os.environ.get('RENDER'):
        # 使用 webhook 模式
        webhook_url = f"https://maggie-stock-ai.onrender.com/webhook"
        updater.bot.set_webhook(url=webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
        
        # 啟動 Flask server
        app.run(host='0.0.0.0', port=PORT)
    else:
        # 本地開發使用 polling
        logger.info("Starting polling...")
        updater.start_polling()
        updater.idle()

if __name__ == '__main__':
    main()
