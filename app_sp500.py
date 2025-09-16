#!/usr/bin/env python3
import logging
import os
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from flask import Flask, request

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
PORT = int(os.environ.get('PORT', 8080))

# Flask app for webhook
app = Flask(__name__)

def start_command(update: Update, context: CallbackContext):
    """測試開始命令"""
    update.message.reply_text("✅ 機器人正常運行！")
    logger.info(f"User {update.effective_user.id} used /start")

def test_command(update: Update, context: CallbackContext):
    """測試命令"""
    user_id = update.effective_user.id
    update.message.reply_text(f"🧪 測試成功！\n您的用戶ID: {user_id}")
    logger.info(f"User {user_id} used /test")

#!/usr/bin/env python3
import logging
import os
import yfinance as yf
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from flask import Flask, request

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
PORT = int(os.environ.get('PORT', 8080))
ADMIN_USER_ID = 981883005  # Maggie.L

# Flask app for webhook
app = Flask(__name__)

class VIPStockBot:
    def __init__(self):
        self.vip_basic_users = set()
        self.vip_pro_users = set()
        
        # 支援的股票清單 - 確保TSLA在內
        self.supported_stocks = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
            'NFLX', 'AMD', 'INTC', 'ORCL', 'CRM', 'ADBE',
            'JPM', 'BAC', 'WFC', 'GS', 'V', 'MA', 'PYPL',
            'JNJ', 'PFE', 'UNH', 'ABBV', 'LLY', 'MRNA',
            'KO', 'PG', 'WMT', 'HD', 'MCD', 'NKE', 'SBUX',
            'SPY', 'QQQ', 'VTI', 'IWM',
            'PLTR', 'SNOW', 'CRWD', 'ZM', 'ROKU', 'COIN',
            'BABA', 'JD', 'PDD', 'NIO', 'XPEV', 'LI'
        ]
        
    def check_user_tier(self, user_id):
        if user_id in self.vip_pro_users:
            return "pro"
        elif user_id in self.vip_basic_users:
            return "basic"
        else:
            return "free"
    
    def is_admin(self, user_id):
        return user_id == ADMIN_USER_ID
    
    def add_vip_user(self, user_id, tier):
        if tier == "basic":
            self.vip_basic_users.add(user_id)
            self.vip_pro_users.discard(user_id)
            return True
        elif tier == "pro":
            self.vip_pro_users.add(user_id)
            self.vip_basic_users.discard(user_id)
            return True
        return False
    
    def get_stock_analysis(self, symbol):
        """獲取股票分析"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="30d")
            info = ticker.info
            
            if hist.empty:
                return None
            
            # 基本價格信息
            current_price = float(hist['Close'][-1])
            previous_close = float(hist['Close'][-2]) if len(hist) > 1 else current_price
            volume = int(hist['Volume'][-1])
            
            # 計算技術指標
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            
            # 52週高低點
            high_52w = float(hist['High'].max())
            low_52w = float(hist['Low'].min())
            
            # 簡單RSI計算
            price_changes = hist['Close'].diff()
            gains = price_changes.where(price_changes > 0, 0)
            losses = -price_changes.where(price_changes < 0, 0)
            avg_gain = gains.rolling(window=14).mean()
            avg_loss = losses.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1] if not rs.empty else 50
            
            return {
                'symbol': symbol,
                'name': info.get('shortName', symbol),
                'current_price': current_price,
                'change': change,
                'change_percent': change_percent,
                'volume': volume,
                'high_52w': high_52w,
                'low_52w': low_52w,
                'rsi': rsi,
                'market_cap': info.get('marketCap'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {e}")
            return None
    
    def format_analysis(self, data, user_tier):
        """格式化分析報告"""
        if not data:
            return "無法獲取股票數據"
        
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
        
        # RSI分析
        if data['rsi'] > 70:
            rsi_signal = "超買警告"
        elif data['rsi'] < 30:
            rsi_signal = "超賣機會"
        else:
            rsi_signal = "正常範圍"
        
        # 操作建議
        if data['change_percent'] > 3:
            suggestion = "建議持有，注意高位風險"
        elif data['change_percent'] > 0:
            suggestion = "建議持有"
        elif data['change_percent'] > -3:
            suggestion = "建議觀望"
        else:
            suggestion = "建議減倉或等待反彈"
        
        if user_tier == "free":
            message = f"""🎯 {data['name']} ({data['symbol']}) 免費版分析
📅 {data['timestamp']}

📊 基礎股價資訊
💰 當前價格: ${data['current_price']:.2f}
{change_emoji} 變化: {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%)
📦 成交量: {data['volume']:,}
🏢 市值: {market_cap_str}

📈 技術分析
📊 RSI指標: {data['rsi']:.1f} ({rsi_signal})
📊 52週區間: ${data['low_52w']:.2f} - ${data['high_52w']:.2f}

🤖 Maggie AI 建議
💡 操作建議: {suggestion}

---
⏰ 免費版分析完成
🤖 分析師: Maggie AI FREE

💎 升級VIP享受專業分析！
📞 聯繫: @maggie_investment (Maggie.L)"""
        
        else:
            # VIP版本會有更多指標
            message = f"""🎯 {data['symbol']} Market Maker 專業分析
📅 {data['timestamp']}

📊 股價資訊
💰 當前價格: ${data['current_price']:.2f}
{change_emoji} 變化: {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%)
📦 成交量: {data['volume']:,}
🏢 市值: {market_cap_str}

📈 專業技術分析
📊 RSI指標: {data['rsi']:.1f} ({rsi_signal})
📊 52週區間: ${data['low_52w']:.2f} - ${data['high_52w']:.2f}

🤖 Maggie AI VIP建議
💡 操作建議: {suggestion}

---
⏰ VIP{'專業版' if user_tier == 'pro' else '基礎版'}分析完成
🤖 分析師: Maggie AI {user_tier.upper()}"""
        
        return message

# 初始化機器人
bot = VIPStockBot()

def start_command(update: Update, context: CallbackContext):
    """開始命令"""
    user_id = update.effective_user.id
    user_tier = bot.check_user_tier(user_id)
    
    welcome_message = f"""🤖 歡迎使用 Maggie Stock AI!

📊 您的等級: {user_tier.upper()}版

💡 快速開始:
• /stock AAPL - 分析蘋果公司
• /stock TSLA - 分析特斯拉
• /help - 查看幫助

💎 升級VIP享受專業分析！
📞 聯繫: @maggie_investment"""
    
    update.message.reply_text(welcome_message)
    logger.info(f"User {user_id} ({user_tier}) used /start")

def test_command(update: Update, context: CallbackContext):
    """測試命令"""
    user_id = update.effective_user.id
    user_tier = bot.check_user_tier(user_id)
    is_admin = bot.is_admin(user_id)
    
    test_msg = f"""🧪 系統測試結果

👤 用戶信息:
- 用戶ID: {user_id}
- 等級: {user_tier.upper()}
- 管理員: {'是' if is_admin else '否'}

📊 系統狀態:
- 支援股票: {len(bot.supported_stocks)}支
- TSLA支援: {'✅' if 'TSLA' in bot.supported_stocks else '❌'}
- 機器人: ✅ 正常運行"""
    
    update.message.reply_text(test_msg)
    logger.info(f"User {user_id} used /test")

def stock_command(update: Update, context: CallbackContext):
    """股票查詢命令"""
    user_id = update.effective_user.id
    user_tier = bot.check_user_tier(user_id)
    
    if not context.args:
        update.message.reply_text(
            "請提供股票代號，例如:\n"
            "• /stock AAPL - 分析蘋果公司\n"
            "• /stock TSLA - 分析特斯拉\n\n"
            f"支援 {len(bot.supported_stocks)} 支熱門股票"
        )
        return
    
    symbol = context.args[0].upper().strip()
    logger.info(f"User {user_id} ({user_tier}) queried stock: {symbol}")
    
    # 檢查股票是否支援
    if symbol not in bot.supported_stocks:
        update.message.reply_text(
            f"❌ '{symbol}' 暫不支援\n\n"
            f"🔥 熱門選擇: AAPL, TSLA, NVDA, MSFT\n"
            f"📞 如需添加股票請聯繫: @maggie_investment"
        )
        return
    
    # 發送分析中訊息
    processing_msg = update.message.reply_text(
        f"🔍 正在分析 {symbol}...\n"
        f"⏰ 獲取即時數據中..."
    )
    
    # 獲取股票分析
    analysis_data = bot.get_stock_analysis(symbol)
    
    if analysis_data:
        final_message = bot.format_analysis(analysis_data, user_tier)
        processing_msg.edit_text(final_message)
    else:
        processing_msg.edit_text(f"❌ 無法分析 {symbol}，請稍後再試")

def help_command(update: Update, context: CallbackContext):
    """幫助命令"""
    help_message = """📚 Maggie Stock AI 使用指南

🔧 基本命令
• /start - 歡迎頁面
• /stock [代號] - 股票分析
• /test - 系統測試
• /help - 幫助說明

📊 使用範例
• /stock AAPL - 蘋果公司
• /stock TSLA - 特斯拉
• /stock NVDA - 輝達

📋 支援股票 (部分)
🔥 科技股: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA
💰 金融股: JPM, BAC, V, MA, PYPL
📊 ETF: SPY, QQQ, VTI
🇨🇳 中概股: BABA, JD, NIO, XPEV

💎 升級VIP享受專業分析
📞 聯繫: @maggie_investment"""
    
    update.message.reply_text(help_message)

def admin_add_vip_command(update: Update, context: CallbackContext):
    """管理員添加VIP命令"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        update.message.reply_text("❌ 此命令僅限管理員使用")
        return
    
    if len(context.args) != 2:
        update.message.reply_text(
            "使用方法: /admin_add_vip [用戶ID] [basic/pro]\n"
            "例如: /admin_add_vip 123456789 basic"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        tier = context.args[1].lower()
        
        if bot.add_vip_user(target_user_id, tier):
            update.message.reply_text(
                f"✅ VIP用戶添加成功\n"
                f"用戶ID: {target_user_id}\n"
                f"等級: {tier.upper()}"
            )
        else:
            update.message.reply_text("❌ 添加失敗，等級必須是 basic 或 pro")
            
    except ValueError:
        update.message.reply_text("❌ 用戶ID必須是數字")

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

def main():
    """主函數"""
    global updater
    logger.info("Starting Maggie Stock AI Bot...")
    
    try:
        updater = Updater(token=BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # 註冊命令
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("test", test_command))
        dispatcher.add_handler(CommandHandler("stock", stock_command))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("admin_add_vip", admin_add_vip_command))
        
        logger.info("Commands registered")
        
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
        
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        raise

if __name__ == '__main__':
    main()

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
    
    try:
        updater = Updater(token=BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # 註冊命令
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("test", test_command))
        dispatcher.add_handler(CommandHandler("stock", stock_command))
        
        logger.info("Commands registered")
        
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
        
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        raise

if __name__ == '__main__':
    main()
