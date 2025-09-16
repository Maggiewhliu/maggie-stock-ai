#!/usr/bin/env python3
import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'

def start_command(update: Update, context: CallbackContext):
    """測試開始命令"""
    update.message.reply_text("機器人運行中！")

def test_command(update: Update, context: CallbackContext):
    """測試命令"""
    user_id = update.effective_user.id
    update.message.reply_text(f"測試成功！您的用戶ID是: {user_id}")

def stock_command(update: Update, context: CallbackContext):
    """股票查詢命令"""
    if context.args:
        symbol = context.args[0].upper()
        if symbol == "TSLA":
            update.message.reply_text("TSLA 測試成功！機器人正常工作。")
        else:
            update.message.reply_text(f"收到股票代號: {symbol}")
    else:
        update.message.reply_text("請提供股票代號，例如: /stock TSLA")

def main():
    """主函數"""
    logger.info("Starting simple test bot...")
    
    try:
        updater = Updater(token=BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # 註冊命令
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("test", test_command))
        dispatcher.add_handler(CommandHandler("stock", stock_command))
        
        logger.info("Commands registered, starting polling...")
        
        # 啟動機器人
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"Bot failed to start: {e}")
        raise

if __name__ == '__main__':
    main()
