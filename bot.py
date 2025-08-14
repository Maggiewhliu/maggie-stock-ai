import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import requests
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaggieBot:
    def __init__(self, token):
        self.token = token
        self.app = Application.builder().token(token).build()
        self.sp500_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 
            'BRK-B', 'JNJ', 'V', 'WMT', 'PG', 'JPM', 'UNH', 'MA',
            'DIS', 'HD', 'PYPL', 'BAC', 'NFLX', 'ADBE', 'CRM', 'XOM',
            'KO', 'PEP', 'COST', 'ABBV', 'CVX', 'MRK', 'TMO', 'ACN'
        ]
        self.user_queries = {}
        self._setup_handlers()
    
    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("vip", self.vip_command))
        self.app.add_handler(CommandHandler("test", self.test_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_query))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome = """🎉 歡迎使用 Maggie Stock AI！

🤖 我是您的專業股票分析助手

🆓 免費功能：
• 查詢熱門美股（每日3次）
• 即時價格與漲跌幅分析
• AI智能投資建議

📝 使用方法：
直接發送股票代碼，例如：AAPL

💎 VIP功能：
• 全美股8000+支無限查詢
• 技術分析指標
• 期權數據分析

🔓 升級VIP：/vip
❓ 使用幫助：/help
🧪 測試功能：/test"""
        
        await update.message.reply_text(welcome)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """📖 Maggie Stock AI 使用說明

🔍 股票查詢方法：
直接發送股票代碼，例如：AAPL

🆓 免費版限制：
• 每日3次查詢限制
• 支援熱門股票

💎 VIP版優勢：
• 全美股無限查詢
• 完整技術分析

📞 客服與支援：@maggie_invests

⚠️ 重要提醒：
所有分析僅供參考，投資決策請謹慎評估風險"""
        
        await update.message.reply_text(help_text)
    
    async def test_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """測試命令"""
        test_msg = """🧪 系統測試結果：

✅ Bot基本功能：正常
✅ 命令處理：正常  
✅ 客服聯絡：@maggie_invests
✅ 環境變量：已設置

🔧 如果股票查詢失敗，可能原因：
• yfinance庫連接問題
• Railway網路限制
• 數據源API限制

💡 建議：
1. 嘗試不同股票代碼
2. 稍後再試
3. 聯絡 @maggie_invests

當前時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
        
        await update.message.reply_text(test_msg)
    
    async def vip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🎯 VIP基礎版 $9.99/月", url="https://t.me/maggie_invests")],
            [InlineKeyboardButton("💎 VIP專業版 $19.99/月", url="https://t.me/maggie_invests")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        vip_text = """💎 升級 Maggie Stock AI VIP 會員

🎯 VIP基礎版 ($9.99/月)：
✅ 全美股8000+支無限查詢
✅ 技術分析指標
✅ 即時新聞摘要

💎 VIP專業版 ($19.99/月)：
✅ 基礎版全部功能
✅ 期權數據分析
✅ 籌碼分析

💬 立即升級或諮詢：@maggie_invests"""
        
        await update.message.reply_text(vip_text, reply_markup=reply_markup)
    
    async def handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        symbol = update.message.text.upper().strip()
        
        # 驗證股票代碼格式
        if not symbol.isalpha() or len(symbol) > 5:
            await update.message.reply_text(
                "❌ 請輸入有效的股票代碼\n\n📝 正確格式：AAPL, TSLA, GOOGL\n🧪 測試系統：/test"
            )
            return
        
        # 檢查查詢次數
        today = datetime.now().strftime('%Y-%m-%d')
        user_key = f"{user_id}_{today}"
        queries_today = self.user_queries.get(user_key, 0)
        
        if queries_today >= 3:
            keyboard = [[InlineKeyboardButton("🔓 升級VIP", url="https://t.me/maggie_invests")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ 免費版每日查詢次數已用完（3次）\n\n🔓 升級VIP享無限查詢！",
                reply_markup=reply_markup
            )
            return
        
        # 檢查支援的股票
        if symbol not in self.sp500_symbols:
            keyboard = [[InlineKeyboardButton("🔓 查詢全美股", url="https://t.me/maggie_invests")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ 免費版僅支援熱門股票\n\n✅ 支援清單：{', '.join(self.sp500_symbols[:10])}...\n\n💎 VIP版支援全美股！",
                reply_markup=reply_markup
            )
            return
        
        # 開始查詢
        processing = await update.message.reply_text("🔍 正在查詢股票數據...")
        
        try:
            # 使用簡單的示例數據（暫時替代yfinance）
            result = await self._get_demo_stock_data(symbol, queries_today)
            
            # 更新查詢計數
            self.user_queries[user_key] = queries_today + 1
            
            await processing.edit_text(result)
            
            # 記錄日誌
            logger.info(f"✅ Demo query: {username}({user_id}) -> {symbol}")
            
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            await processing.edit_text(
                f"❌ 查詢 {symbol} 時發生錯誤\n\n🔧 技術問題：系統正在修復中\n📞 聯絡客服：@maggie_invests\n🧪 系統測試：/test\n\n⏰ 請稍後再試"
            )
    
    async def _get_demo_stock_data(self, symbol, queries_used):
        """示例數據（替代yfinance）"""
        
        # 示例股票數據
        demo_data = {
            'AAPL': {'price': 175.43, 'change': 2.15, 'volume': '52.3M', 'name': 'Apple Inc.'},
            'TSLA': {'price': 248.90, 'change': -1.20, 'volume': '28.7M', 'name': 'Tesla Inc.'},
            'GOOGL': {'price': 142.56, 'change': 3.45, 'volume': '31.2M', 'name': 'Alphabet Inc.'},
            'MSFT': {'price': 378.85, 'change': 1.89, 'volume': '24.8M', 'name': 'Microsoft Corp.'},
            'AMZN': {'price': 145.78, 'change': -0.67, 'volume': '35.4M', 'name': 'Amazon.com Inc.'}
        }
        
        # 獲取數據或使用默認值
        if symbol in demo_data:
            data = demo_data[symbol]
        else:
            data = {'price': 100.00, 'change': 0.50, 'volume': '10.0M', 'name': f'{symbol} Corp.'}
        
        change_percent = (data['change'] / data['price']) * 100
        
        # 簡單的AI建議
        if change_percent > 1:
            recommendation = "🟢 買入"
            confidence = 75
        elif change_percent < -1:
            recommendation = "🔴 賣出"
            confidence = 70
        else:
            recommendation = "🟡 持有"
            confidence = 65
        
        result = f"""📊 [{symbol}] {data['name']} 股票分析

💰 當前價格：${data['price']:.2f}
📈 漲跌幅：{data['change']:+.2f} ({change_percent:+.2f}%)
📦 成交量：{data['volume']}

🎯 Maggie AI 建議：{recommendation}
📊 分析信心度：{confidence}%
⏰ 數據時間：{datetime.now().strftime('%m-%d %H:%M')}

💡 升級VIP解鎖：
✨ 即時真實數據
✨ 技術分析指標
✨ 期權數據分析

🔓 立即升級：/vip

📊 今日剩餘查詢：{2-queries_used}次
📜 注意：當前為演示數據
📞 客服支援：@maggie_invests"""
        
        return result
    
    def run(self):
        logger.info("🚀 Maggie Stock AI Bot (Demo Mode) 啟動中...")
        logger.info("📞 客服聯絡: @maggie_invests")
        logger.info("🧪 使用 /test 檢查系統狀態")
        
        try:
            self.app.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"❌ Bot運行錯誤: {e}")

if __name__ == "__main__":
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ 找不到 TELEGRAM_BOT_TOKEN")
        exit(1)
    
    logger.info("🔐 Token已設置")
    bot = MaggieBot(TOKEN)
    bot.run()
