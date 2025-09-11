#!/usr/bin/env python3
import os
import logging
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
PORT = int(os.getenv('PORT', 8080))

class SP500StockBot:
    def __init__(self):
        self.sp500_symbols = None
        self.last_update = None
        self.cache_duration = timedelta(hours=24)  # 每天更新一次標普500清單
        
    def get_sp500_symbols(self):
        """獲取標普500股票清單"""
        try:
            # 檢查緩存是否有效
            if (self.sp500_symbols and self.last_update and 
                datetime.now() - self.last_update < self.cache_duration):
                return self.sp500_symbols
            
            logger.info("Fetching S&P 500 symbols...")
            
            # 從 Wikipedia 獲取標普500清單
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            sp500_table = tables[0]
            
            # 提取並清理股票代碼
            symbols = []
            for symbol in sp500_table['Symbol'].tolist():
                if isinstance(symbol, str):
                    # 處理特殊字符（如 BRK.B -> BRK-B）
                    clean_symbol = symbol.replace('.', '-')
                    symbols.append(clean_symbol)
            
            self.sp500_symbols = symbols
            self.last_update = datetime.now()
            
            logger.info(f"Successfully loaded {len(symbols)} S&P 500 symbols")
            return symbols
            
        except Exception as e:
            logger.error(f"Failed to fetch S&P 500 symbols: {e}")
            # 返回主要股票作為備用
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B',
                'UNH', 'JNJ', 'V', 'PG', 'JPM', 'HD', 'MA', 'BAC', 'ABBV', 'PFE',
                'KO', 'AVGO', 'PEP', 'TMO', 'COST', 'DIS', 'ABT', 'MRK', 'VZ', 'ADBE',
                'CRM', 'ACN', 'LLY', 'NFLX', 'NKE', 'WMT', 'ORCL', 'CSCO', 'XOM'
            ]
    
    async def get_real_stock_data(self, symbol):
        """獲取真實股票數據"""
        try:
            logger.info(f"Fetching real data for {symbol}")
            
            # 使用 yfinance 獲取數據
            ticker = yf.Ticker(symbol)
            
            # 獲取基本信息
            info = ticker.info
            
            # 檢查股票是否有效
            if not info or 'symbol' not in info:
                return None
            
            # 獲取歷史數據（最近2天）
            hist = ticker.history(period="2d")
            if hist.empty:
                return None
            
            # 提取價格信息
            current_price = info.get('currentPrice')
            if not current_price:
                current_price = hist['Close'][-1]
            
            previous_close = info.get('previousClose')
            if not previous_close and len(hist) > 1:
                previous_close = hist['Close'][-2]
            elif not previous_close:
                previous_close = current_price
            
            # 計算變動
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
            
            # 格式化成交量
            volume = info.get('volume', 0)
            if volume > 1000000:
                volume_str = f"{volume/1000000:.1f}M"
            elif volume > 1000:
                volume_str = f"{volume/1000:.1f}K"
            else:
                volume_str = str(volume)
            
            return {
                'symbol': symbol,
                'name': info.get('shortName') or info.get('longName', symbol),
                'current_price': float(current_price),
                'previous_close': float(previous_close),
                'change': float(change),
                'change_percent': float(change_percent),
                'volume': volume,
                'volume_str': volume_str,
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'data_source': 'Yahoo Finance (Live)',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Failed to get real data for {symbol}: {e}")
            return None
    
    def format_stock_message(self, data):
        """格式化股票訊息"""
        if not data:
            return "Unable to fetch stock data."
        
        # 格式化變動顯示
        change_emoji = "📈" if data['change'] >= 0 else "📉"
        change_sign = "+" if data['change'] >= 0 else ""
        
        # 市值格式化
        market_cap_str = "N/A"
        if data.get('market_cap'):
            if data['market_cap'] > 1000000000000:  # 兆
                market_cap_str = f"${data['market_cap']/1000000000000:.2f}T"
            elif data['market_cap'] > 1000000000:  # 億
                market_cap_str = f"${data['market_cap']/1000000000:.1f}B"
            elif data['market_cap'] > 1000000:  # 百萬
                market_cap_str = f"${data['market_cap']/1000000:.1f}M"
        
        # P/E 比率
        pe_str = f"{data['pe_ratio']:.2f}" if data.get('pe_ratio') else "N/A"
        
        message = f"""{change_emoji} **{data['name']} ({data['symbol']})**

💰 **Price:** ${data['current_price']:.2f}
📊 **Change:** {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%)
📈 **Volume:** {data['volume_str']}
🏢 **Market Cap:** {market_cap_str}
📋 **P/E Ratio:** {pe_str}

🕐 **Updated:** {data['timestamp']}
📡 **Source:** {data['data_source']}

---
*Maggie Stock AI - Real-time S&P 500 Data*"""
        
        return message

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

# 初始化機器人實例
bot = SP500StockBot()

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理股票查詢命令"""
    try:
        if not context.args:
            sp500_symbols = bot.get_sp500_symbols()
            sample_symbols = sp500_symbols[:10]  # 顯示前10個作為示例
            
            await update.message.reply_text(
                f"**Usage:** /stock [SYMBOL]\n\n"
                f"**S&P 500 Support:** {len(sp500_symbols)} stocks available\n\n"
                f"**Examples:**\n" +
                "\n".join([f"• /stock {symbol}" for symbol in sample_symbols]) +
                f"\n\n**Popular stocks:** AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA"
            )
            return
        
        symbol = context.args[0].upper().strip()
        
        # 檢查是否為支援的股票
        sp500_symbols = bot.get_sp500_symbols()
        if symbol not in sp500_symbols:
            await update.message.reply_text(
                f"Stock symbol '{symbol}' is not in the S&P 500.\n\n"
                f"**Supported:** {len(sp500_symbols)} S&P 500 stocks\n"
                f"**Examples:** AAPL, MSFT, GOOGL, AMZN, TSLA"
            )
            return
        
        # 發送處理中訊息
        processing_msg = await update.message.reply_text(
            f"🔍 **Analyzing {symbol}...**\n"
            f"⏱️ Fetching real-time data from Yahoo Finance..."
        )
        
        # 獲取真實股票數據
        stock_data = await bot.get_real_stock_data(symbol)
        
        if stock_data:
            # 格式化並發送完整報告
            final_message = bot.format_stock_message(stock_data)
            await processing_msg.edit_text(final_message)
        else:
            await processing_msg.edit_text(
                f"❌ **Unable to fetch data for {symbol}**\n\n"
                f"This might be due to:\n"
                f"• Market is closed\n"
                f"• Temporary API issues\n"
                f"• Stock symbol not found\n\n"
                f"Please try again later."
            )
            
    except Exception as e:
        logger.error(f"Error in stock command: {e}")
        await update.message.reply_text(
            "❌ Sorry, I encountered an error while processing your request. Please try again."
        )

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 命令"""
    sp500_count = len(bot.get_sp500_symbols())
    
    welcome_message = f"""🤖 **Welcome to Maggie Stock AI!**

I provide real-time analysis for all S&P 500 stocks.

📊 **Features:**
• Live stock prices from Yahoo Finance
• {sp500_count} S&P 500 stocks supported
• Market cap and P/E ratios
• Real-time price changes

💡 **Usage:**
• `/stock AAPL` - Get Apple stock data
• `/stock TSLA` - Get Tesla stock data
• `/list` - See popular stocks

🎯 **Core Value:**
"Real-time data beats delayed information"

---
Built with precision by Maggie"""
    
    await update.message.reply_text(welcome_message)

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """顯示熱門股票清單"""
    popular_stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA',
        'BRK-B', 'UNH', 'JNJ', 'V', 'PG', 'JPM', 'HD', 'MA'
    ]
    
    message = "📈 **Popular S&P 500 Stocks:**\n\n"
    
    for i, symbol in enumerate(popular_stocks, 1):
        message += f"{i:2d}. `/stock {symbol}`\n"
    
    sp500_count = len(bot.get_sp500_symbols())
    message += f"\n💡 **Total supported:** {sp500_count} S&P 500 stocks"
    
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /help 命令"""
    sp500_count = len(bot.get_sp500_symbols())
    
    help_message = f"""📚 **Maggie Stock AI Help**

**Commands:**
• `/stock [SYMBOL]` - Get real-time stock data
• `/list` - Show popular stocks
• `/help` - Show this help

**Data Coverage:**
• {sp500_count} S&P 500 companies
• Real-time prices via Yahoo Finance
• Market cap, P/E ratios, volume

**Examples:**
• `/stock AAPL` - Apple Inc.
• `/stock MSFT` - Microsoft Corp.
• `/stock GOOGL` - Alphabet Inc.

**Features:**
• Live price updates
• Change indicators (📈📉)
• Professional financial metrics

Need support? Contact @maggie"""
    
    await update.message.reply_text(help_message)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般文字訊息"""
    text = update.message.text.upper()
    
    # 檢查是否包含支援的股票代碼
    sp500_symbols = bot.get_sp500_symbols()
    
    for symbol in sp500_symbols[:50]:  # 檢查前50個熱門股票
        if symbol in text:
            await update.message.reply_text(
                f"💡 I detected '{symbol}' in your message!\n"
                f"Use `/stock {symbol}` to get real-time data."
            )
            return
    
    # 一般回應
    await update.message.reply_text(
        "Hello! I'm Maggie Stock AI 🤖\n\n"
        "I provide real-time S&P 500 stock data.\n"
        "Use `/stock AAPL` or `/help` for more info."
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """處理錯誤"""
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    """主函數"""
    logger.info("Starting Maggie Stock AI Bot with S&P 500 real data...")
    
    # 預載標普500清單
    logger.info("Pre-loading S&P 500 symbols...")
    symbols = bot.get_sp500_symbols()
    logger.info(f"Loaded {len(symbols)} S&P 500 symbols")
    
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
    application.add_handler(CommandHandler("list", list_command))
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
