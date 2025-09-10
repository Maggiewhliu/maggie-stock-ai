#!/usr/bin/env python3
import os
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
PORT = int(os.getenv('PORT', 8080))

def clear_webhook():
    """清除現有的 webhook 設定"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook"
        response = requests.get(url, timeout=10)
        result = response.json()
        logger.info(f"Webhook cleared: {result}")
        return result.get('ok', False)
    except Exception as e:
        logger.error(f"Failed to clear webhook: {e}")
        return False

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理股票查詢命令"""
    try:
        if not context.args:
            await update.message.reply_text(
                "Usage: /stock [SYMBOL]\n\n"
                "Examples:\n"
                "• /stock AAPL\n"
                "• /stock MSFT\n"
                "• /stock GOOGL\n"
                "• /stock AMZN\n"
                "• /stock TSLA"
            )
            return
        
        symbol = context.args[0].upper().strip()
        
        # 模擬股票數據 - 這些是示例數據
        stock_data = {
            'AAPL': {
                'name': 'Apple Inc.',
                'price': 180.50,
                'change': +2.30,
                'change_percent': +1.29,
                'volume': '45.2M'
            },
            'MSFT': {
                'name': 'Microsoft Corporation',
                'price': 350.20,
                'change': -1.50,
                'change_percent': -0.43,
                'volume': '32.1M'
            },
            'GOOGL': {
                'name': 'Alphabet Inc.',
                'price': 140.80,
                'change': +3.20,
                'change_percent': +2.33,
                'volume': '28.5M'
            },
            'AMZN': {
                'name': 'Amazon.com Inc.',
                'price': 145.60,
                'change': +0.80,
                'change_percent': +0.55,
                'volume': '41.8M'
            },
            'TSLA': {
                'name': 'Tesla Inc.',
                'price': 250.30,
                'change': -5.40,
                'change_percent': -2.11,
                'volume': '89.3M'
            },
            'META': {
                'name': 'Meta Platforms Inc.',
                'price': 295.40,
                'change': +4.60,
                'change_percent': +1.58,
                'volume': '22.7M'
            },
            'NVDA': {
                'name': 'NVIDIA Corporation',
                'price': 450.75,
                'change': +12.25,
                'change_percent': +2.79,
                'volume': '55.4M'
            }
        }
        
        if symbol in stock_data:
            data = stock_data[symbol]
            
            # 格式化變動顯示
            change_symbol = "+" if data['change'] >= 0 else ""
            change_emoji = "📈" if data['change'] >= 0 else "📉"
            
            message = f"""
{change_emoji} **{data['name']} ({symbol})**

💰 **Price:** ${data['price']:.2f}
📊 **Change:** {change_symbol}${data['change']:.2f} ({change_symbol}{data['change_percent']:.2f}%)
📈 **Volume:** {data['volume']}

---
*Maggie Stock AI - Demo Data*
            """.strip()
            
            await update.message.reply_text(message)
            
        else:
            supported_stocks = ", ".join(stock_data.keys())
            await update.message.reply_text(
                f"Stock symbol '{symbol}' is not supported yet.\n\n"
                f"**Currently supported stocks:**\n{supported_stocks}\n\n"
                f"More stocks coming soon!"
            )
            
    except Exception as e:
        logger.error(f"Error in stock command: {e}")
        await update.message.reply_text(
            "Sorry, I encountered an error while processing your request. Please try again."
        )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 命令"""
    welcome_message = """
🤖 **Welcome to Maggie Stock AI!**

I'm your personal stock analysis assistant.

**Available Commands:**
• `/stock [SYMBOL]` - Get stock information
• `/help` - Show this help message

**Supported Stocks:**
📱 AAPL (Apple)
💻 MSFT (Microsoft)
🔍 GOOGL (Google)
📦 AMZN (Amazon)
🚗 TSLA (Tesla)
📘 META (Meta)
🎮 NVDA (NVIDIA)

**Example:** `/stock AAPL`

---
Built with ❤️ by Maggie
    """.strip()
    
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /help 命令"""
    help_message = """
📚 **Maggie Stock AI Help**

**How to use:**
1. Type `/stock` followed by a stock symbol
2. Example: `/stock AAPL`

**Supported Stocks:**
• AAPL - Apple Inc.
• MSFT - Microsoft Corporation
• GOOGL - Alphabet Inc.
• AMZN - Amazon.com Inc.
• TSLA - Tesla Inc.
• META - Meta Platforms Inc.
• NVDA - NVIDIA Corporation

**Features:**
• Real-time stock prices
• Price change indicators
• Trading volume information

Need more help? Contact @maggie
    """.strip()
    
    await update.message.reply_text(help_message)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般文字訊息"""
    text = update.message.text.upper()
    
    # 檢查是否包含股票代碼
    stock_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
    
    for symbol in stock_symbols:
        if symbol in text:
            await update.message.reply_text(
                f"I detected '{symbol}' in your message!\n"
                f"Use `/stock {symbol}` to get detailed information."
            )
            return
    
    # 一般回應
    await update.message.reply_text(
        "Hello! I'm Maggie Stock AI 🤖\n\n"
        "Use `/stock AAPL` to get stock information\n"
        "Use `/help` for more commands"
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """處理錯誤"""
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    """主函數"""
    logger.info("Starting Maggie Stock AI Bot...")
    
    # 清除可能存在的 webhook 衝突
    logger.info("Clearing any existing webhooks...")
    if clear_webhook():
        logger.info("Webhook cleared successfully")
    else:
        logger.warning("Failed to clear webhook, continuing anyway...")
    
    # 建立 Telegram 應用程序
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 註冊命令處理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stock", stock_command))
    
    # 註冊文字訊息處理器
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # 註冊錯誤處理器
    application.add_error_handler(error_handler)
    
    # 啟動機器人
    if os.getenv('RENDER'):
        logger.info(f"Running in Render deployment mode on port {PORT}")
        try:
            application.run_webhook(
                listen="0.0.0.0",
                port=PORT,
                webhook_url=f"https://maggie-stock-ai.onrender.com/{BOT_TOKEN}",
                url_path=BOT_TOKEN,
                allowed_updates=Update.ALL_TYPES
            )
        except Exception as e:
            logger.error(f"Webhook failed: {e}")
            logger.info("Falling back to polling mode...")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
    else:
        logger.info("Running in local development mode with polling")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
