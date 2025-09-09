# 創建 app.py
cat > app.py << 'EOF'
#!/usr/bin/env python3
"""
Maggie Stock AI Bot - 主應用程序
"""

import os
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 設定 logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
PORT = int(os.getenv('PORT', 8080))

class MaggieStockBot:
    def __init__(self):
        self.yahoo_api_key = "NBWPE7OFZHTT3OFI"
    
    async def handle_stock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理股票查詢"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "請提供股票代碼\n\n"
                    "使用方法:\n"
                    "• /stock AAPL - 查詢蘋果股票\n"
                    "• /stock MSFT - 查詢微軟股票\n"
                    "• /stock GOOGL - 查詢Google股票\n\n"
                    "支援股票: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA"
                )
                return
            
            symbol = context.args[0].upper().strip()
            
            # 驗證股票代碼
            if not self._validate_symbol(symbol):
                await update.message.reply_text(
                    f"無效的股票代碼: {symbol}\n\n"
                    "請檢查股票代碼是否正確\n"
                    "支援的股票: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA"
                )
                return
            
            # 發送處理中訊息
            processing_msg = await update.message.reply_text(
                f"正在深度分析 {symbol}...\n"
                f"預計1-3分鐘完成專業分析\n"
                f"正在獲取即時數據..."
            )
            
            # 獲取股票數據
            stock_data = await self.get_stock_data(symbol)
            
            if stock_data:
                # 更新訊息顯示基本資訊
                basic_info = self._format_basic_info(stock_data)
                await processing_msg.edit_text(
                    f"{basic_info}\n\n"
                    f"正在進行AI深度分析...\n"
                    f"技術分析進行中..."
                )
                
                # 等待一下模擬分析過程
                import asyncio
                await asyncio.sleep(2)
                
                # 發送完整分析報告
                final_report = self._format_final_report(stock_data)
                await processing_msg.edit_text(final_report)
                
            else:
                await processing_msg.edit_text(
                    f"找不到股票代碼 {symbol}\n\n"
                    f"請檢查:\n"
                    f"• 股票代碼是否正確\n"
                    f"• 是否為美股上市公司\n"
                    f"• 嘗試使用完整代碼\n\n"
                    f"範例: /stock AAPL"
                )
                
        except Exception as e:
            logger.error(f"處理股票命令時發生錯誤: {e}")
            await update.message.reply_text(
                "系統暫時無法處理您的請求\n"
                "請稍後再試，或聯繫客服協助"
            )
    
    def _validate_symbol(self, symbol):
        """驗證股票代碼"""
        if not symbol or len(symbol) < 1 or len(symbol) > 6:
            return False
        
        # 支援的主要股票
        supported_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
        return symbol in supported_stocks
    
    async def get_stock_data(self, symbol):
        """獲取股票數據"""
        try:
            import yfinance as yf
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or 'symbol' not in info:
                return None
            
            # 獲取當前價格
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
                'pe_ratio': info.get('trailingPE'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"獲取 {symbol} 數據失敗: {e}")
            return None
    
    def _format_basic_info(self, data):
        """格式化基本資訊"""
        change_emoji = "📈" if data['change'] > 0 else "📉" if data['change'] < 0 else "➡️"
        change_sign = "+" if data['change'] > 0 else ""
        
        return f"""股票查詢結果

{data['name']} ({data['symbol']})
當前價格: ${data['current_price']:.2f}
{change_emoji} 漲跌: {change_sign}${data['change']:.2f} ({change_sign}{data['change_percent']:.2f}%)
成交量: {data['volume']:,}"""
    
    def _format_final_report(self, data):
        """格式化最終報告"""
        change_emoji = "📈" if data['change'] > 0 else "📉" if data['change'] < 0 else "➡️"
        change_sign = "+" if data['change'] > 0 else ""
        
        # AI 分析建議
        if data['change_percent'] > 2:
            recommendation = "謹慎樂觀"
            confidence = "中高"
            risk_level = "中等"
        elif data['change_percent'] < -2:
            recommendation = "逢低布局"
            confidence = "中等"
            risk_level = "偏高"
        else:
            recommendation = "持續觀察"
            confidence = "中等"
            risk_level = "中等"
        
        return f"""{data['name']} ({data['symbol']}) - 深度分析報告

即時價格資訊
當前價格: ${data['current_price']:.2f}
{change_emoji} 漲跌: {change_sign}${data['change']:.2f} ({change_sign}{data['change_percent']:.2f}%)
成交量: {data['volume']:,}
52週最高: ${data.get('fifty_two_week_high', 'N/A')}
52週最低: ${data.get('fifty_two_week_low', 'N/A')}

AI分析結果
投資建議: {recommendation}
信心度: {confidence}
風險等級: {risk_level}

技術分析
趨勢: {"上升" if data['change'] > 0 else "下降" if data['change'] < 0 else "震盪"}
建議: {"持續關注上漲動能" if data['change'] > 0 else "注意支撐位表現" if data['change'] < 0 else "等待明確方向"}

分析完成時間: {data['timestamp']}
數據來源: Yahoo Finance

---
想要更快速的分析？升級到 Pro Beta 版本！"""

# 初始化機器人
bot = MaggieStockBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 命令"""
    welcome_message = """歡迎使用 Maggie's Stock AI！

功能介紹：
- 20分鐘深度股票分析
- AI投資建議與信心度
- IPO新股分析
- 每日免費七巨頭報告

使用方法：
- /stock AAPL - 查詢蘋果股票
- /stock MSFT - 查詢微軟股票
- /stock TSLA - 查詢特斯拉股票

核心價值：
"20分鐘深度分析比3秒查價更有價值"

---
由 Maggie 用心打造"""
    
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /help 命令"""
    help_text = """Maggie Stock AI 使用指南

股票查詢：
/stock [股票代碼] - 深度分析股票

支援股票：
- AAPL (Apple)
- MSFT (Microsoft)
- GOOGL (Google)
- AMZN (Amazon)
- TSLA (Tesla)
- META (Meta)
- NVDA (NVIDIA)

分析時間：
- 免費版: 20分鐘深度分析
- Pro版: 2分鐘快速分析
- VIP版: 30秒即時分析

範例：
/stock AAPL
/stock TSLA

需要協助？聯繫 @maggie"""
    
    await update.message.reply_text(help_text)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般文字"""
    text = update.message.text.upper()
    
    # 檢查常見股票代碼
    common_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
    for stock in common_stocks:
        if stock in text:
            await update.message.reply_text(
                f"偵測到股票代碼: {stock}\n"
                f"使用 /stock {stock} 查詢詳細資訊"
            )
            return
    
    await update.message.reply_text(
        "您好！我是 Maggie Stock AI\n"
        "使用 /stock AAPL 查詢股票\n"
        "使用 /help 查看使用說明"
    )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """處理錯誤"""
    logger.error(f"Exception while handling an update: {context.error}")

def main():
    """主函數"""
    logger.info("正在啟動 Maggie Stock AI Bot...")
    
    if not BOT_TOKEN:
        logger.error("未設定 BOT_TOKEN")
        return
    
    # 創建應用程序
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 註冊處理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stock", bot.handle_stock_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # 錯誤處理
    application.add_error_handler(error_handler)
    
    # 啟動機器人
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
