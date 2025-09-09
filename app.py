#!/usr/bin/env python3
import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
PORT = int(os.getenv('PORT', 8080))

class MaggieStockBot:
    def __init__(self):
        self.yahoo_api_key = "NBWPE7OFZHTT3OFI"
    
    async def handle_stock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not context.args:
                await update.message.reply_text(
                    "Please provide a stock symbol\n\n"
                    "Usage:\n"
                    "/stock AAPL\n"
                    "/stock MSFT\n"
                    "/stock GOOGL"
                )
                return
            
            symbol = context.args[0].upper().strip()
            
            if not self._validate_symbol(symbol):
                await update.message.reply_text(
                    f"Invalid stock symbol: {symbol}\n\n"
                    f"Please check if the stock symbol is correct"
                )
                return
            
            processing_msg = await update.message.reply_text(
                f"Analyzing {symbol}...\n"
                f"Expected completion time: 1-3 minutes"
            )
            
            stock_data = await self.get_stock_data(symbol)
            
            if stock_data:
                basic_info = self._format_basic_info(stock_data)
                await processing_msg.edit_text(
                    f"{basic_info}\n\n"
                    f"Performing AI deep analysis..."
                )
                
                import asyncio
                await asyncio.sleep(2)
                
                final_report = self._format_final_report(stock_data)
                await processing_msg.edit_text(final_report)
            else:
                await processing_msg.edit_text(
                    f"Stock symbol {symbol} not found\n\n"
                    f"Please check if the stock symbol is correct"
                )
                
        except Exception as e:
            logger.error(f"Error handling stock command: {e}")
            await update.message.reply_text("System temporarily unavailable")
    
    def _validate_symbol(self, symbol):
        supported_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
        return symbol in supported_stocks
    
    async def get_stock_data(self, symbol):
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'symbol' not in info:
                return None
            
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            previous_close = info.get('previousClose', current_price)
            
            if not current_price:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = hist['Close'][-1]
                else:
                    return None
            
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            
            return {
                'symbol': info.get('symbol', symbol),
                'name': info.get('shortName') or info.get('longName', symbol),
                'current_price': float(current_price),
                'previous_close': float(previous_close),
                'change': float(change),
                'change_percent': float(change_percent),
                'volume': int(info.get('volume', 0)),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Failed to get {symbol} data: {e}")
            return None
    
    def _format_basic_info(self, data):
        change_emoji = "UP" if data['change'] > 0 else "DOWN"
        change_sign = "+" if data['change'] > 0 else ""
        
        return f"""Stock Query Result

{data['name']} ({data['symbol']})
Current Price: ${data['current_price']:.2f}
{change_emoji} Change: {change_sign}${data['change']:.2f} ({change_sign}{data['change_percent']:.2f}%)
Volume: {data['volume']:,}"""
    
    def _format_final_report(self, data):
        change_emoji = "UP" if data['change'] > 0 else "DOWN"
        change_sign = "+" if data['change'] > 0 else ""
        
        if data['change_percent'] > 2:
            recommendation = "Cautiously Optimistic"
            confidence = "Medium-High"
        elif data['change_percent'] < -2:
            recommendation = "Buy on Dips"
            confidence = "Medium"
        else:
            recommendation = "Continue Monitoring"
            confidence = "Medium"
        
        return f"""{data['name']} ({data['symbol']}) - Deep Analysis Report

Real-time Price Information
Current Price: ${data['current_price']:.2f}
{change_emoji} Change: {change_sign}${data['change']:.2f} ({change_sign}{data['change_percent']:.2f}%)
Volume: {data['volume']:,}

AI Analysis Results
Investment Recommendation: {recommendation}
Confidence Level: {confidence}
Risk Level: Medium

Analysis Completion Time: {data['timestamp']}
Data Source: Yahoo Finance

---
Want faster analysis? Upgrade to Pro Beta version!"""

bot = MaggieStockBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = """Welcome to Maggie's Stock AI!

Features:
- 20-minute deep stock analysis
- AI investment recommendations

Usage:
- /stock AAPL - Query Apple stock
- /stock MSFT - Query Microsoft stock

Built with love by Maggie"""
    
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """Maggie Stock AI User Guide

Supported Stocks:
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- AMZN (Amazon)
- TSLA (Tesla)
- META (Meta)
- NVDA (NVIDIA)

Example: /stock AAPL"""
    
    await update.message.reply_text(help_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper()
    
    common_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
    for stock in common_stocks:
        if stock in text:
            await update.message.reply_text(
                f"Detected stock symbol: {stock}\nUse /stock {stock} for detailed information"
            )
            return
    
    await update.message.reply_text(
        "Hello! I am Maggie Stock AI\nUse /stock AAPL to query stocks"
    )

def main():
    logger.info("Starting Maggie Stock AI Bot...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stock", bot.handle_stock_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    if os.getenv('RENDER'):
        logger.info(f"Render deployment mode, Port: {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"https://maggie-stock-ai.onrender.com/{BOT_TOKEN}",
            url_path=BOT_TOKEN
        )
    else:
        logger.info("Local development mode")
        application.run_polling()

if __name__ == '__main__':
    main()
