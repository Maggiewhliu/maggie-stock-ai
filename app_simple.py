#!/usr/bin/env python3
import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
PORT = int(os.getenv('PORT', 8080))

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理股票查詢"""
    if not context.args:
        await update.message.reply_text("Usage: /stock AAPL")
        return
    
    symbol = context.args[0].upper()
    
    # 簡單的股票數據模擬
    stock_prices = {
        'AAPL': {'name': 'Apple Inc.', 'price': 180.50, 'change': +2.30},
        'MSFT': {'name': 'Microsoft', 'price': 350.20, 'change': -1.50},
        'GOOGL': {'name': 'Google', 'price': 140.80, 'change': +3.20},
        'AMZN': {'name': 'Amazon', 'price': 145.60, 'change': +0.80},
        'TSLA': {'name': 'Tesla', 'price': 250.30, 'change': -5.40},
    }
    
    if symbol in stock_prices:
        data = stock_prices[symbol]
        change_symbol = "+" if data['change'] >= 0 else ""
        await update.message.reply_text(
            f"{data['name']} ({symbol})\n"
            f"Price: ${data['price']}\n"
            f"Change: {change_symbol}${data['change']}"
        )
    else:
        await update.message.reply_text(f"Stock {symbol} not supported yet.")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Maggie Stock AI!\n"
        "Use /stock AAPL to get stock info."
    )

def main():
    logger.info("Starting Maggie Stock AI Bot...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("stock", stock_command))
    
    # 暫時使用 polling 模式
    logger.info("Using polling mode")
    application.run_polling()

if __name__ == '__main__':
    main()
