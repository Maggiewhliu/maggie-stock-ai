# 刪除有問題的 app.py
rm app.py

# 創建正確的 app.py（分段創建避免語法錯誤）
cat > app.py << 'EOF'
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
                    "請提供股票代碼\n\n使用方法:\n/stock AAPL\n/stock MSFT\n/stock GOOGL"
                )
                return
            
            symbol = context.args[0].upper().strip()
            
            if not self._validate_symbol(symbol):
                await update.message.reply_text(
                    f"無效的股票代碼: {symbol}\n\n請檢查股票代碼是否正確"
                )
                return
            
            processing_msg = await update.message.reply_text(
                f"正在深度分析 {symbol}...\n預計1-3分鐘完成專業分析"
            )
            
            stock_data = await self.get_stock_data(symbol)
            
            if stock_data:
                basic_info = self._format_basic_info(stock_data)
                await processing_msg.edit_text(
                    f"{basic_info}\n\n正在進行AI深度分析..."
                )
                
                import asyncio
                await asyncio.sleep(2)
                
                final_report = self._format_final_report(stock_data)
                await processing_msg.edit_text(final_report)
            else:
                await processing_msg.edit_text(
                    f"找不到股票代碼 {symbol}\n\n請檢查股票代碼是否正確"
                )
                
        except Exception as e:
            logger.error(f"處理股票命令時發生錯誤: {e}")
            await update.message.reply_text("系統暫時無法處理您的請求")
    
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
            logger.error(f"獲取 {symbol} 數據失敗: {e}")
            return None
    
    def _format_basic_info(self, data):
        change_emoji = "📈" if data['change'] > 0 else "📉"
        change_sign = "+" if data['change'] > 0 else ""
        
        return f"""股票查詢結果

{data['name']} ({data['symbol']})
當前價格: ${data['current_price']:.2f}
{change_emoji} 漲跌: {change_sign}${data['change']:.2f} ({change_sign}{data['change_percent']:.2f}%)
成交量: {data['volume']:,}"""
    
    def _format_final_report(self, data):
        change_emoji = "📈" if data['change'] > 0 else "📉"
        change_sign = "+" if data['change'] > 0 else ""
        
        if data['change_percent'] > 2:
            recommendation = "謹慎樂觀"
            confidence = "中高"
        elif data['change_percent'] < -2:
            recommendation = "逢低布局"
            confidence = "中等"
        else:
            recommendation = "持續觀察"
            confidence = "中等"
        
        return f"""{data['name']} ({data['symbol']}) - 深度分析報告

即時價格資訊
當前價格: ${data['current_price']:.2f}
{change_emoji} 漲跌: {change_sign}${data['change']:.2f} ({change_sign}{data['change_percent']:.2f}%)
成交量: {data['volume']:,}

AI分析結果
投資建議: {recommendation}
信心度: {confidence}
風險等級: 中等

分析完成時間: {data['timestamp']}
數據來源: Yahoo Finance

---
想要更快速的分析？升級到 Pro Beta 版本！"""

bot = MaggieStockBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = """歡迎使用 Maggie's Stock AI！

功能介紹：
- 20分鐘深度股票分析
- AI投資建議與信心度

使用方法：
- /stock AAPL - 查詢蘋果股票
- /stock MSFT - 查詢微軟股票

由 Maggie 用心打造"""
    
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """Maggie Stock AI 使用指南

支援股票：
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- AMZN (Amazon)
- TSLA (Tesla)
- META (Meta)
- NVDA (NVIDIA)

範例：/stock AAPL"""
    
    await update.message.reply_text(help_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.upper()
    
    common_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
    for stock in common_stocks:
        if stock in text:
            await update.message.reply_text(
                f"偵測到股票代碼: {stock}\n使用 /stock {stock} 查詢詳細資訊"
            )
            return
    
    await update.message.reply_text(
        "您好！我是 Maggie Stock AI\n使用 /stock AAPL 查詢股票"
    )

def main():
    logger.info("正在啟動 Maggie Stock AI Bot...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stock", bot.handle_stock_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    if os.getenv('RENDER'):
        logger.info(f"Render 部署模式，Port: {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"https://maggie-stock-ai.onrender.com/{BOT_TOKEN}",
            url_path=BOT_TOKEN
        )
    else:
        logger.info("本地開發模式")
        application.run_polling()

if __name__ == '__main__':
    main()
EOF
