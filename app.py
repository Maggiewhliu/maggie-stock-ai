import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境變數
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("請設置 TELEGRAM_BOT_TOKEN 環境變數")

# 創建 Flask 應用
app = Flask(__name__)

# 創建 Bot 和 Dispatcher (舊版本語法)
bot = Bot(TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# 指令處理函數 (舊版本語法)
def start_command(update: Update, context: CallbackContext):
    """處理 /start 指令"""
    update.message.reply_text(
        "👋 嗨！我是 Maggie's Stock AI\n\n"
        "🔹 /stock TSLA - 查詢股票\n"
        "🔹 /help - 顯示幫助\n\n"
        "機器人運行正常！"
    )

def stock_command(update: Update, context: CallbackContext):
    """處理 /stock 指令"""
    args = context.args
    if not args:
        update.message.reply_text("用法：/stock TSLA")
        return
    
    symbol = args[0].upper()
    update.message.reply_text(
        f"📊 {symbol} 分析中...\n\n"
        "💰 價格：$250.00\n"
        "📈 變動：+2.5%\n"
        "🎯 狀態：測試中\n\n"
        "（這是測試數據，功能開發中）"
    )

def help_command(update: Update, context: CallbackContext):
    """處理 /help 指令"""
    update.message.reply_text(
        "📚 Maggie's Stock AI 指令：\n\n"
        "🔹 /start - 開始使用\n"
        "🔹 /stock TSLA - 股票查詢\n"
        "🔹 /help - 顯示此幫助\n\n"
        "更多功能開發中..."
    )

def handle_message(update: Update, context: CallbackContext):
    """處理一般訊息"""
    update.message.reply_text(
        f"收到訊息：{update.message.text}\n"
        "請使用 /help 查看可用指令"
    )

# 註冊處理器 (舊版本語法)
dispatcher.add_handler(CommandHandler("start", start_command))
dispatcher.add_handler(CommandHandler("stock", stock_command))
dispatcher.add_handler(CommandHandler("help", help_command))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Flask 路由
@app.route("/")
def home():
    """首頁"""
    return {
        "status": "running",
        "service": "Maggie's Stock AI Bot",
        "message": "機器人運行中"
    }

@app.route("/health")
def health():
    """健康檢查"""
    return {"status": "healthy"}

@app.route("/set-webhook")
def set_webhook():
    """設置 webhook"""
    try:
        webhook_url = "https://maggie-stock-ai.onrender.com/webhook"
        result = bot.set_webhook(url=webhook_url)
        
        if result:
            return {"status": "success", "webhook": webhook_url}
        else:
            return {"status": "failed"}, 500
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/webhook", methods=["POST"])
def webhook():
    """處理 webhook (舊版本同步處理)"""
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, bot)
        
        # 舊版本同步處理
        dispatcher.process_update(update)
        
        return "OK"
    except Exception as e:
        logger.error(f"Webhook 錯誤: {str(e)}")
        return "Error", 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
