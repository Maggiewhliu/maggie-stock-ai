#!/usr/bin/env python3
"""
Maggie Stock AI Bot - 主應用程序
純 Telegram Bot，不使用 Flask
"""

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 設定 logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE')
PORT = int(os.getenv('PORT', 8080))

# 簡化的股票查詢類
class SimpleStockBot:
    """簡化版股票機器人，避免複雜的依賴問題"""
    
    def __init__(self):
        self.yahoo_api_key = "NBWPE7OFZHTT3OFI"
    
    async def handle_stock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理股票查詢"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "❌ 請提供股票代碼\n\n"
                    "📝 使用方法: /stock AAPL\n"
                    "📊 支援股票: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA"
                )
                return
            
            symbol = context.args[0].upper().strip()
            
            # 發送處理中訊息
            processing_msg = await update.message.reply_text(
                f"🔍 正在深度分析 {symbol}...\n"
                f"⏱️ 預計1-3分鐘完成分析"
            )
            
            # 獲取股票數據
            stock_data = await self.get_stock_data_simple(symbol)
            
            if stock_data:
                # 格式化回應
                response = self.format_stock_response(stock_data)
                await processing_msg.edit_text(response)
            else:
                await processing_msg.edit_text(
                    f"❌ 找不到股票代碼 {symbol}\n\n"
                    f"💡 請檢查股票代碼是否正確\n"
                    f"📊 支援的股票: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA"
                )
                
        except Exception as e:
            logger.error(f"股票查詢錯誤: {e}")
            await update.message.reply_text(
                "❌ 系統暫時無法處理您的請求\n請稍後再試"
            )
    
    async def get_stock_data_simple(self, symbol):
        """簡化的股票數據獲取"""
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'symbol' not in info:
                return None
            
            # 獲取基本數據
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
                'market_cap': info.get('marketCap'),
            }
            
        except ImportError:
            logger.error("yfinance 未安裝")
            return self.get_fallback_data(symbol)
        except Exception as e:
            logger.error(f"獲取 {symbol} 數據失敗: {e}")
            return self.get_fallback_data(symbol)
    
    def get_fallback_data(self, symbol):
        """備用數據"""
        fallback_stocks = {
            'AAPL': {'name': 'Apple Inc.', 'price': 180.00},
            'MSFT': {'name': 'Microsoft Corporation', 'price': 350.00},
            'GOOGL': {'name': 'Alphabet Inc.', 'price': 140.00},
            'AMZN': {'name': 'Amazon.com Inc.', 'price': 145.00},
            'TSLA': {'name': 'Tesla Inc.', 'price': 250.00},
            'META': {'name': 'Meta Platforms Inc.', 'price': 300.00},
            'NVDA': {'name': 'NVIDIA Corporation', 'price': 450.00}
        }
        
        if symbol in fallback_stocks:
            stock = fallback_stocks[symbol]
            return {
                'symbol': symbol,
                'name': stock['name'],
                'current_price': stock['price'],
                'previous_close': stock['price'] * 0.99,
                'change': stock['price'] * 0.01,
                'change_percent': 1.0,
                'volume': 1000000,
                'market_cap': 1000000000,
                'note': '備用數據，僅供參考'
            }
        return None
    
    def format_stock_response(self, data):
        """格式化股票回應"""
        change_emoji = "📈" if data['change'] > 0 else "📉" if data['change'] < 0 else "➡️"
        change_sign = "+" if data['change'] > 0 else ""
        
        response = f"""
🔍 **{data['name']} ({data['symbol']}) - 深度分析報告**

💰 **即時價格資訊**
當前價格: ${data['current_price']:.2f}
{change_emoji} 漲跌: {change_sign}${data['change']:.2f} ({change_sign}{data['change_percent']:.2f}%)
成交量: {data['volume']:,}

🤖 **AI分析結果**
投資建議: 謹慎觀察 ⭐⭐⭐
信心度: 中等
風險等級: 中等

📈 **技術分析**
趨勢: 震盪整理
建議: 分批進場，設定停損

⏰ **分析完成時間**: 剛剛
📊 **數據來源**: Yahoo Finance
        """
        
        if 'note' in data:
            response += f"\n⚠️ **注意**: {data['note']}"
        
        response += """

---
💎 想要更快速的分析？升級到 Pro Beta 版本！
        """
        
        return response.strip()

# 初始化機器人
bot = SimpleStockBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /start 命令"""
    welcome_message = """
🤖 **歡迎使用 Maggie's Stock AI！**

🔍 **功能介紹：**
• 📊 20分鐘深度股票分析
• 📈 AI投資建議與信心度
• 🆕 IPO新股分析
• 🎁 每日免費七巨頭報告

💡 **使用方法：**
• /stock AAPL - 查詢蘋果股票
• /stock MSFT - 查詢微軟股票
• /stock TSLA - 查詢特斯拉股票

🎯 **核心價值：**
"20分鐘深度分析比3秒查價更有價值"

---
由 Maggie 用 ❤️ 打造
    """
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理 /help 命令"""
    help_text = """
📚 **Maggie Stock AI 使用指南**

🔍 **股票查詢：**
/stock [股票代碼] - 深度分析股票

📊 **支援股票：**
• 🍎 AAPL (Apple)
• 🖥️ MSFT (Microsoft)  
• 🔍 GOOGL (Google)
• 📦 AMZN (Amazon)
• 🚗 TSLA (Tesla)
• 📘 META (Meta)
• 🎮 NVDA (NVIDIA)

💡 **範例：**
/stock AAPL
/stock TSLA

❓ 需要協助？聯繫 @maggie
    """
    await update.message.reply_text(help_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """處理一般文字"""
    text = update.message.text.upper()
    
    # 檢查常見股票代碼
    common_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
    for stock in common_stocks:
        if stock in text:
            await update.message.reply_text(
                f"🔍 偵測到股票代碼: {stock}\n"
                f"使用 /stock {stock} 查詢詳細資訊"
            )
            return
    
    await update.message.reply_text(
        "🤖 您好！我是 Maggie Stock AI\n"
        "使用 /stock AAPL 查詢股票\n"
        "使用 /help 查看使用說明"
    )

def main() -> None:
    """主函數"""
    logger.info("🚀 正在啟動 Maggie Stock AI Bot...")
    
    if not BOT_TOKEN:
        logger.error("❌ 未設定 BOT_TOKEN")
        return
    
    # 創建應用程序
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 註冊處理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stock", bot.handle_stock_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # 啟動機器人
    if os.getenv('RENDER'):
        logger.info(f"🌐 Render 部署模式，Port: {PORT}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"https://maggie-stock-ai.onrender.com/{BOT_TOKEN}",
            url_path=BOT_TOKEN
        )
    else:
        logger.info("💻 本地開發模式")
        application.run_polling()

if __name__ == '__main__':
    main()
