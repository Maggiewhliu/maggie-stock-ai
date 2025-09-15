#!/usr/bin/env python3
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 設置日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 你的機器人TOKEN
BOT_TOKEN = "8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """測試 /start 命令"""
    await update.message.reply_text("🤖 機器人啟動成功！\n\n輸入 /test 測試功能")

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """測試命令"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "無用戶名"
    
    test_message = f"""✅ **測試成功！**

👤 **用戶信息:**
• ID: {user_id}
• 用戶名: @{username}
• 時間: {update.message.date}

🔧 **機器人狀態:**
• 消息接收: ✅ 正常
• 回應功能: ✅ 正常
• TOKEN驗證: ✅ 正常

💡 現在可以開始添加股票功能了！"""
    
    await update.message.reply_text(test_message)

async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """回音測試 - 重複用戶發送的消息"""
    message_text = update.message.text
    await update.message.reply_text(f"收到消息: {message_text}")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """記錄錯誤"""
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    """主函數"""
    print("🚀 正在啟動測試機器人...")
    print(f"🔑 Token: {BOT_TOKEN[:10]}...")
    
    # 創建應用
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 添加處理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("test", test_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))
    
    # 添加錯誤處理器
    application.add_error_handler(error_handler)
    
    # 啟動機器人
    print("✅ 機器人啟動中...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
