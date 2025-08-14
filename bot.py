import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""🎉 Maggie Stock AI 測試版

✅ Bot運行正常
📞 客服聯絡：@maggie_invests

發送任何股票代碼測試""")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper()
    await update.message.reply_text(f"""📊 [{text}] 測試查詢

💰 當前價格：$123.45 (演示數據)
📈 漲跌：+1.23 (+1.00%)

🎯 AI建議：🟡 持有
📞 客服：@maggie_invests

💡 VIP版提供真實數據""")

def main():
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🚀 Maggie Bot 啟動中...")
    app.run_polling()

if __name__ == '__main__':
    main()
