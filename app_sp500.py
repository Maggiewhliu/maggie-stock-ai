#!/usr/bin/env python3
import os
import logging
import requests
import yfinance as yf
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
        
    def get_sp500_symbols(self):
        """獲取標普500股票清單（使用擴展固定清單確保穩定性）"""
        if self.sp500_symbols:
            return self.sp500_symbols
            
        # 完整標普500股票清單（固定版本，避免依賴問題）
        sp500_symbols = [
            # 科技股 - Technology
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'ORCL', 'CRM',
            'NFLX', 'AMD', 'INTC', 'QCOM', 'CSCO', 'IBM', 'NOW', 'INTU', 'AMAT', 'ADI',
            'MU', 'MRVL', 'KLAC', 'LRCX', 'SNPS', 'CDNS', 'FTNT', 'TEAM', 'WDAY', 'ZM',
            'DOCU', 'OKTA', 'SPLK', 'VEEV', 'ZS', 'CRWD', 'DDOG', 'SNOW', 'NET', 'PLTR',
            
            # 金融股 - Financial Services
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'USB', 'PNC',
            'COF', 'TFC', 'BK', 'STT', 'FITB', 'HBAN', 'RF', 'CFG', 'KEY', 'ZION',
            'AIG', 'PRU', 'MET', 'AFL', 'ALL', 'TRV', 'PGR', 'CB', 'AJG', 'MMC',
            'AON', 'WTW', 'BRO', 'CINF', 'L', 'FNF', 'RJF', 'NTRS', 'IVZ', 'BEN',
            
            # 醫療保健 - Healthcare
            'UNH', 'JNJ', 'PFE', 'ABBV', 'LLY', 'TMO', 'ABT', 'MDT', 'BMY', 'MRK',
            'DHR', 'CVS', 'CI', 'HUM', 'ANTM', 'SYK', 'GILD', 'ISRG', 'ZTS', 'BSX',
            'ELV', 'REGN', 'VRTX', 'BIIB', 'ILMN', 'MRNA', 'AMGN', 'CELG', 'IDXX', 'IQV',
            'A', 'RMD', 'DXCM', 'EW', 'ZBH', 'STE', 'HOLX', 'ALGN', 'TFX', 'COO',
            
            # 消費品 - Consumer Discretionary & Staples
            'PG', 'KO', 'PEP', 'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW',
            'COST', 'DIS', 'CMCSA', 'VZ', 'T', 'TMUS', 'CL', 'KMB', 'GIS', 'K',
            'AMZN', 'TSLA', 'F', 'GM', 'NFLX', 'DIS', 'CMCSA', 'CHTR', 'PARA', 'WBD',
            'GPS', 'M', 'JWN', 'NCLH', 'CCL', 'RCL', 'MGM', 'WYNN', 'LVS', 'PENN',
            
            # 工業股 - Industrials
            'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'RTX', 'LMT', 'NOC', 'GD',
            'DE', 'EMR', 'ETN', 'ITW', 'PH', 'CMI', 'FDX', 'NSC', 'UNP', 'CSX',
            'LUV', 'DAL', 'UAL', 'AAL', 'JBLU', 'ALK', 'SAVE', 'WAB', 'TXT', 'ROK',
            'DOV', 'IR', 'FAST', 'PCAR', 'CHRW', 'EXPD', 'JBHT', 'KNX', 'SWK', 'PKG',
            
            # 能源股 - Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'HES', 'DVN',
            'KMI', 'OKE', 'WMB', 'EPD', 'ET', 'MPLX', 'PAGP', 'BKR', 'HAL', 'FTI',
            'NOV', 'RIG', 'VAL', 'MRO', 'APA', 'FANG', 'PXD', 'CXO', 'OVV', 'CLR',
            
            # 材料股 - Materials
            'LIN', 'APD', 'ECL', 'FCX', 'NEM', 'DOW', 'DD', 'PPG', 'SHW', 'NUE',
            'VMC', 'MLM', 'FMC', 'LYB', 'CF', 'MOS', 'IFF', 'ALB', 'CE', 'PKX',
            'RPM', 'EMN', 'IP', 'WRK', 'SON', 'SEE', 'AVY', 'BALL', 'CCK', 'SLGN',
            
            # 公用事業 - Utilities
            'NEE', 'DUK', 'SO', 'AEP', 'EXC', 'XEL', 'WEC', 'ED', 'ETR', 'ES',
            'AWK', 'PEG', 'SRE', 'D', 'PCG', 'EIX', 'PPL', 'CMS', 'DTE', 'ATO',
            'CNP', 'NI', 'LNT', 'EVRG', 'AES', 'FE', 'PNW', 'NRG', 'VST', 'CEG',
            
            # 房地產 - Real Estate
            'AMT', 'PLD', 'CCI', 'EQIX', 'SPG', 'O', 'WELL', 'DLR', 'PSA', 'EQR',
            'AVB', 'VTR', 'ARE', 'SBAC', 'UDR', 'ESS', 'MAA', 'KIM', 'REG', 'FRT',
            'BXP', 'HST', 'SLG', 'VNO', 'PEAK', 'AMH', 'EXR', 'CPT', 'AIV', 'BRX',
            
            # 金融服務 - Financial (Payment processors, etc.)
            'V', 'MA', 'PYPL', 'SQ', 'FIS', 'FISV', 'ADP', 'PAYX', 'IT', 'ACN',
            'TXN', 'AVGO', 'AAPL', 'MSFT', 'QCOM', 'NOW', 'CRM', 'ORCL', 'IBM', 'HPQ',
            
            # 大型綜合企業 - Diversified
            'BRK-B', 'JNJ', 'UNH', 'XOM', 'PG', 'TSLA', 'NVDA', 'META', 'GOOGL', 'AMZN',
            'GE', 'MMM', 'WMT', 'JPM', 'V', 'MA', 'HD', 'PFE', 'VZ', 'DIS',
            
            # 其他重要股票
            'COST', 'NFLX', 'CRM', 'AMD', 'TMO', 'ABT', 'DHR', 'LIN', 'UNP', 'LOW',
            'QCOM', 'INTC', 'IBM', 'ORCL', 'CSCO', 'TXN', 'AVGO', 'HON', 'UPS', 'CAT',
            'BA', 'MMM', 'WM', 'GD', 'RTX', 'LMT', 'NOC', 'SPGI', 'CME', 'ICE'
        ]
        
        # 去重並排序
        sp500_symbols = sorted(list(set(sp500_symbols)))
        
        self.sp500_symbols = sp500_symbols
        self.last_update = datetime.now()
        
        logger.info(f"Loaded {len(sp500_symbols)} S&P 500 symbols")
        return sp500_symbols
    
    async def get_real_stock_data(self, symbol):
        """獲取真實股票數據"""
        try:
            logger.info(f"Fetching real data for {symbol}")
            
            # 使用 yfinance 獲取數據
            ticker = yf.Ticker(symbol)
            
            # 獲取基本信息
            info = ticker.info
            
            # 檢查股票是否有效
            if not info or len(info) < 5:
                logger.warning(f"Invalid or insufficient data for {symbol}")
                return None
            
            # 獲取歷史數據作為備用
            hist = ticker.history(period="5d")
            
            # 提取價格信息
            current_price = None
            price_fields = ['currentPrice', 'regularMarketPrice', 'previousClose']
            
            for field in price_fields:
                if field in info and info[field]:
                    current_price = float(info[field])
                    break
            
            # 如果從info獲取不到，使用歷史數據
            if not current_price and not hist.empty:
                current_price = float(hist['Close'][-1])
            
            if not current_price:
                logger.warning(f"No price data available for {symbol}")
                return None
            
            # 獲取前一交易日收盤價
            previous_close = info.get('previousClose')
            if not previous_close and len(hist) > 1:
                previous_close = float(hist['Close'][-2])
            elif not previous_close:
                previous_close = current_price
            else:
                previous_close = float(previous_close)
            
            # 計算變動
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
            
            # 格式化成交量
            volume = info.get('volume', 0) or info.get('regularMarketVolume', 0)
            if volume > 1000000:
                volume_str = f"{volume/1000000:.1f}M"
            elif volume > 1000:
                volume_str = f"{volume/1000:.1f}K"
            else:
                volume_str = str(volume) if volume else "N/A"
            
            # 獲取其他信息
            market_cap = info.get('marketCap')
            pe_ratio = info.get('trailingPE') or info.get('forwardPE')
            
            # 獲取52週高低點
            fifty_two_week_high = info.get('fiftyTwoWeekHigh')
            fifty_two_week_low = info.get('fiftyTwoWeekLow')
            
            return {
                'symbol': symbol,
                'name': info.get('shortName') or info.get('longName', symbol),
                'current_price': current_price,
                'previous_close': previous_close,
                'change': change,
                'change_percent': change_percent,
                'volume': volume,
                'volume_str': volume_str,
                'market_cap': market_cap,
                'pe_ratio': pe_ratio,
                'fifty_two_week_high': fifty_two_week_high,
                'fifty_two_week_low': fifty_two_week_low,
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
        if data['change'] > 0:
            change_emoji = "📈"
            change_sign = "+"
        elif data['change'] < 0:
            change_emoji = "📉"
            change_sign = ""
        else:
            change_emoji = "➡️"
            change_sign = ""
        
        # 市值格式化
        market_cap_str = "N/A"
        if data.get('market_cap') and data['market_cap'] > 0:
            if data['market_cap'] > 1000000000000:  # 兆
                market_cap_str = f"${data['market_cap']/1000000000000:.2f}T"
            elif data['market_cap'] > 1000000000:  # 億
                market_cap_str = f"${data['market_cap']/1000000000:.1f}B"
            elif data['market_cap'] > 1000000:  # 百萬
                market_cap_str = f"${data['market_cap']/1000000:.1f}M"
        
        # P/E 比率
        pe_str = f"{data['pe_ratio']:.2f}" if data.get('pe_ratio') and data['pe_ratio'] > 0 else "N/A"
        
        # 52週高低點
        high_52w = f"${data['fifty_two_week_high']:.2f}" if data.get('fifty_two_week_high') else "N/A"
        low_52w = f"${data['fifty_two_week_low']:.2f}" if data.get('fifty_two_week_low') else "N/A"
        
        message = f"""{change_emoji} **{data['name']} ({data['symbol']})**

💰 **Current Price:** ${data['current_price']:.2f}
📊 **Change:** {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%)
📈 **Volume:** {data['volume_str']}
🏢 **Market Cap:** {market_cap_str}
📋 **P/E Ratio:** {pe_str}
📊 **52W High:** {high_52w}
📊 **52W Low:** {low_52w}

🕐 **Updated:** {data['timestamp']}
📡 **Data Source:** {data['data_source']}

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

def set_webhook():
    """設置 webhook"""
    try:
        # 獲取 Render 應用的 URL
        render_url = os.getenv('RENDER_EXTERNAL_URL')
        if not render_url:
            # 如果沒有環境變量，使用預設
            render_url = "https://maggie-stock-ai.onrender.com"
        
        webhook_url = f"{render_url}/{BOT_TOKEN}"
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        data = {
            'url': webhook_url,
            'allowed_updates': ['message', 'callback_query']
        }
        
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        if result.get('ok'):
            logger.info(f"Webhook set successfully: {webhook_url}")
            return True
        else:
            logger.error(f"Failed to set webhook: {result}")
            return False
            
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return False

# 初始化機器人實例
bot = SP500StockBot()

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理股票查詢命令"""
    try:
        if not context.args:
            sp500_symbols = bot.get_sp500_symbols()
            sample_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'WMT', 'KO']
            
            await update.message.reply_text(
                f"**Usage:** /stock [SYMBOL]\n\n"
                f"**S&P 500 Support:** {len(sp500_symbols)} stocks available\n\n"
                f"**Popular Examples:**\n" +
                "\n".join([f"• /stock {symbol}" for symbol in sample_symbols]) +
                f"\n\n**Try:** /list for more options"
            )
            return
        
        symbol = context.args[0].upper().strip()
        
        # 檢查是否為支援的股票
        sp500_symbols = bot.get_sp500_symbols()
        if symbol not in sp500_symbols:
            # 提供相似的股票建議
            suggestions = [s for s in sp500_symbols if symbol in s or s.startswith(symbol[:2])][:5]
            suggestion_text = ""
            if suggestions:
                suggestion_text = f"\n\n**Similar stocks:** {', '.join(suggestions)}"
            
            await update.message.reply_text(
                f"❌ Stock symbol '{symbol}' is not in our S&P 500 database.\n\n"
                f"**Database:** {len(sp500_symbols)} S&P 500 stocks\n"
                f"**Popular:** AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA\n"
                f"**Use:** /list to see categories{suggestion_text}"
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
                f"• Market is currently closed\n"
                f"• Temporary Yahoo Finance API issues\n"
                f"• Stock delisted or suspended\n"
                f"• Network connectivity problems\n\n"
                f"Please try again in a few minutes or try another stock."
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

I provide real-time analysis for S&P 500 stocks with enhanced features.

📊 **Features:**
• Live stock prices from Yahoo Finance
• {sp500_count} S&P 500 stocks supported
• Market cap, P/E ratios, and 52-week ranges
• Real-time price changes with trend indicators
• Professional financial metrics

💡 **Quick Commands:**
• `/stock AAPL` - Get Apple stock data
• `/stock TSLA` - Get Tesla stock data
• `/list` - Browse stocks by sector
• `/help` - Complete command guide

🎯 **Core Philosophy:**
"Real-time data beats delayed information"

✨ **New Features:**
• 52-week high/low tracking
• Enhanced stock suggestions
• Expanded S&P 500 coverage

---
🔧 Built with precision by Maggie
📈 Powered by Yahoo Finance API"""
    
    await update.message.reply_text(welcome_message)

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """顯示熱門股票清單"""
    popular_stocks = {
        '🚀 Tech Giants': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'ORCL'],
        '🏦 Financial': ['JPM', 'BAC', 'WFC', 'GS', 'BLK', 'AXP', 'V', 'MA'],
        '🏥 Healthcare': ['UNH', 'JNJ', 'PFE', 'ABBV', 'LLY', 'TMO', 'ABT', 'MDT'],
        '🛒 Consumer': ['WMT', 'HD', 'PG', 'KO', 'PEP', 'MCD', 'NKE', 'COST'],
        '🏭 Industrial': ['BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'RTX', 'LMT'],
        '⚡ Energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC'],
        '🏠 Real Estate': ['AMT', 'PLD', 'CCI', 'EQIX', 'SPG', 'O']
    }
    
    message = "📈 **S&P 500 Stocks by Sector:**\n\n"
    
    for sector, stocks in popular_stocks.items():
        message += f"**{sector}:**\n"
        for stock in stocks:
            message += f"• `/stock {stock}`\n"
        message += "\n"
    
    sp500_count = len(bot.get_sp500_symbols())
    message += f"💡 **Total coverage:** {sp500_count} S&P 500 stocks\n"
    message += f"🔍 **Tip:** Type stock symbol directly to get suggestions"
    
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /help 命令"""
    sp500_count = len(bot.get_sp500_symbols())
    
    help_message = f"""📚 **Maggie Stock AI - Complete Guide**

**🔧 Commands:**
• `/stock [SYMBOL]` - Get comprehensive stock data
• `/list` - Browse stocks organized by sector
• `/help` - Show this complete guide
• `/start` - Welcome screen and overview

**📊 Data Coverage:**
• {sp500_count} S&P 500 companies tracked
• Real-time prices via Yahoo Finance API
• Market cap, P/E ratios, trading volume
• 52-week high/low price ranges
• Daily price change with percentages

**💡 Usage Examples:**
• `/stock AAPL` - Apple Inc. analysis
• `/stock MSFT` - Microsoft Corporation
• `/stock GOOGL` - Alphabet Inc. (Google)
• `/stock TSLA` - Tesla Inc.

**✨ Advanced Features:**
• Live price updates during market hours
• Trend indicators (📈📉➡️)
• Professional financial metrics
• Sector-based stock organization
• Smart stock symbol suggestions

**⏰ Market Hours:**
• US Market: 9:30 AM - 4:00 PM EST
• Pre/Post market data available
• Weekend data shows Friday close

**🛠️ Troubleshooting:**
• No data? Market might be closed
• Wrong symbol? Use `/list` to browse
• Error? Try again in a few minutes

**📞 Support:**
Built by Maggie with ❤️ for investors
Data powered by Yahoo Finance"""
    
    await update.message.reply_text(help_message)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般文字訊息"""
    text = update.message.text.upper().strip()
    
    # 檢查是否為股票代碼格式 (2-5 個字母)
    if len(text) >= 2 and len(text) <= 5 and text.isalpha():
        sp500_symbols = bot.get_sp500_symbols()
        
        if text in sp500_symbols:
            await update.message.reply_text(
                f"💡 Found '{text}' in S&P 500!\n"
                f"Use `/stock {text}` to get real-time data."
            )
            return
        else:
            # 提供相似的股票建議
            suggestions = [s for s in sp500_symbols if text in s or s.startswith(text[:2])][:3]
            if suggestions:
                await update.message.reply_text(
                    f"'{text}' not found in S&P 500.\n\n"
                    f"**Similar stocks:**\n" +
                    "\n".join([f"• `/stock {s}`" for s in suggestions])
                )
                return
    
    # 檢查是否包含知名股票代碼
    popular_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'WMT', 'KO']
    
    for symbol in popular_symbols:
        if symbol in text:
            await update.message.reply_text(
                f"💡 I detected '{symbol}' in your message!\n"
                f"Use `/stock {symbol}` to get real-time analysis."
            )
            return
    
    # 一般回應
    responses = [
        "Hello! I'm Maggie Stock AI 🤖\n\nI specialize in real-time S&P 500 stock analysis.\nTry `/stock AAPL` or `/help` for guidance.",
        "Hi there! 👋\n\nI provide live financial data for S&P 500 stocks.\nUse `/list` to browse by sector or `/stock [SYMBOL]` for analysis.",
        "Welcome! 📈\n\nI'm here to help with stock market data.\nType `/help` for commands or try `/stock MSFT` for a demo."
    ]
    
    import random
    await update.message.reply_text(random.choice(responses))

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """處理錯誤"""
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    """主函數"""
    logger.info("Starting Maggie Stock AI Bot with enhanced S&P 500 coverage...")
    
    # 預載標普500清單
    logger.info("Pre-loading expanded S&P 500 symbols...")
    symbols = bot.get_sp500_symbols()
    logger.info(f"Successfully loaded {len(symbols)} S&P 500 symbols")
    
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
            # 設置 webhook
            if set_webhook():
                logger.info("Webhook set successfully, starting webhook server...")
                application.run_webhook(
                    listen="0.0.0.0",
                    port=PORT,
                    webhook_url=f"{os.getenv('RENDER_EXTERNAL_URL', 'https://maggie-stock-ai.onrender.com')}/{BOT_TOKEN}",
                    url_path=BOT_TOKEN,
                    allowed_updates=Update.ALL_TYPES
                )
            else:
                logger.warning("Webhook setup failed, falling back to polling...")
                application.run_polling(allowed_updates=Update.ALL_TYPES)
        except Exception as e:
            logger.error(f"Webhook mode failed: {e}")
            logger.info("Falling back to polling mode...")
            application.run_polling(allowed_updates=Update.ALL_TYPES)
    else:
        logger.info("Running in local development mode with polling")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
