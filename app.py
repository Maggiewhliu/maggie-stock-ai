import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境變數
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("請設置 TELEGRAM_BOT_TOKEN 環境變數")

# 創建 Flask 應用
app = Flask(__name__)

# 創建 Telegram Application
application = Application.builder().token(TOKEN).build()

# 指令處理函數
async def start_command(update: Update, context):
    """處理 /start 指令"""
    await update.message.reply_text(
        "👋 嗨！我是 Maggie's Stock AI\n\n"
        "🔹 /stock TSLA - 查詢股票\n"
        "🔹 /help - 顯示幫助\n\n"
        "機器人運行正常！"
    )

async def stock_command(update: Update, context):
    """處理 /stock 指令"""
    if not context.args:
        await update.message.reply_text("用法：/stock TSLA")
        return
    
    symbol = context.args[0].upper()
    await update.message.reply_text(
        f"📊 {symbol} 分析中...\n\n"
        "💰 價格：$250.00\n"
        "📈 變動：+2.5%\n"
        "🎯 狀態：測試中\n\n"
        "（這是測試數據，功能開發中）"
    )

async def help_command(update: Update, context):
    """處理 /help 指令"""
    await update.message.reply_text(
        "📚 Maggie's Stock AI 指令：\n\n"
        "🔹 /start - 開始使用\n"
        "🔹 /stock TSLA - 股票查詢\n"
        "🔹 /help - 顯示此幫助\n\n"
        "更多功能開發中..."
    )

async def handle_message(update: Update, context):
    """處理一般訊息"""
    await update.message.reply_text(
        f"收到訊息：{update.message.text}\n"
        "請使用 /help 查看可用指令"
    )

# 註冊處理器
application.add_handler(CommandHandler("start", start_command))
application.add_handler(CommandHandler("stock", stock_command))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

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
        bot = Bot(TOKEN)
        result = bot.set_webhook(url=webhook_url)
        
        if result:
            return {"status": "success", "webhook": webhook_url}
        else:
            return {"status": "failed"}, 500
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route("/webhook", methods=["POST"])
def webhook():
    """處理 webhook"""
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, Bot(TOKEN))
        
        # 在新的事件循環中處理
        import asyncio
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(application.process_update(update))
        
        return "OK"
    except Exception as e:
        logger.error(f"Webhook 錯誤: {str(e)}")
        return "Error", 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
