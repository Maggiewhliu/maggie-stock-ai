import os
import logging
import yfinance as yf
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

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
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_query))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome = """🎉 歡迎使用 Maggie Stock AI！

🤖 我是您的專業股票分析助手

🆓 免費功能：
- 查詢30+熱門美股（每日3次）
- 即時價格與漲跌幅分析
- AI智能投資建議
- 信心度評估

📝 使用方法：
直接發送股票代碼，例如：
- AAPL（蘋果）
- TSLA（特斯拉）
- GOOGL（谷歌）
- MSFT（微軟）

💎 VIP版功能：
- 全美股8000+支無限查詢
- 技術分析指標(RSI/MACD/布林帶)
- 期權數據分析(Max Pain/Gamma)
- 籌碼分析(主力進出/大戶比例)
- 即時新聞整合與AI摘要
- 價格警報通知

🔓 升級VIP：/vip
❓ 使用幫助：/help"""
        
        await update.message.reply_text(welcome)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """📖 Maggie Stock AI 使用說明

🔍 股票查詢方法：
直接發送股票代碼即可，例如：
- AAPL → 蘋果公司
- TSLA → 特斯拉  
- GOOGL → Alphabet(谷歌)
- MSFT → 微軟
- AMZN → 亞馬遜

🆓 免費版限制：
- 每日3次查詢限制
- 支援30+熱門股票
- 基本價量分析
- AI投資建議

💎 VIP版優勢：
- 全美股無限查詢
- 完整技術分析
- 期權數據解讀
- 即時新聞摘要
- 專業投資建議

📞 客服與支援：
- 技術問題：@maggie_support
- VIP升級：/vip
- 功能建議：歡迎私訊

⚠️ 重要提醒：
所有分析僅供參考，投資決策請謹慎評估風險"""
        
        await update.message.reply_text(help_text)
    
    async def vip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🎯 VIP基礎版 $9.99/月", url="https://t.me/maggies_vip_analyst_bot")],
            [InlineKeyboardButton("💎 VIP專業版 $19.99/月", url="https://t.me/maggies_vip_analyst_bot")],
            [InlineKeyboardButton("📊 詳細功能對比", callback_data="compare")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        vip_text = """💎 升級 Maggie Stock AI VIP 會員

🎯 VIP基礎版 ($9.99/月)：
✅ 全美股8000+支無限查詢
✅ 新股/IPO即時追蹤
✅ 基礎技術分析(RSI/MACD)
✅ 即時新聞整合與AI摘要
✅ 無延遲數據更新
✅ 每日市場摘要推送

💎 VIP專業版 ($19.99/月)：
✅ 基礎版全部功能
✅ 期權數據分析(Max Pain/Gamma/IV)
✅ 籌碼分析(主力進出/大戶比例)
✅ 進階技術指標(布林帶/KD/威廉指標)
✅ Notion投資組合管理面板
✅ 個人化價格警報通知
✅ 專屬VIP群組與客服

🎁 新用戶專屬優惠：
- 首月享5折優惠！
- 年付用戶額外2個月免費
- 7天無條件退款保證

📈 投資回報：
平均每月為VIP用戶識別出3-5個優質投資機會
專業分析工具助您做出更明智的投資決策

💬 立即升級或諮詢：
點擊上方按鈕或聯絡 @maggie_support"""
        
        await update.message.reply_text(vip_text, reply_markup=reply_markup)
    
    async def handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        symbol = update.message.text.upper().strip()
        
        # 驗證股票代碼格式
        if not symbol.isalpha() or len(symbol) > 5:
            await update.message.reply_text(
                "❌ 請輸入有效的股票代碼\n\n📝 正確格式例子：\n• AAPL（蘋果）\n• TSLA（特斯拉）\n• GOOGL（谷歌）"
            )
            return
        
        # 檢查每日查詢次數限制
        today = datetime.now().strftime('%Y-%m-%d')
        user_key = f"{user_id}_{today}"
        queries_today = self.user_queries.get(user_key, 0)
        
        if queries_today >= 3:
            keyboard = [[InlineKeyboardButton("🔓 立即升級VIP", url="https://t.me/maggies_vip_analyst_bot")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ 免費版每日查詢次數已用完（3次）\n\n💎 升級VIP享受：\n✅ 無限次查詢\n✅ 全美股覆蓋\n✅ 專業分析工具\n\n🎁 新用戶首月5折優惠！",
                reply_markup=reply_markup
            )
            return
        
        # 檢查是否為支持的股票
        if symbol not in self.sp500_symbols:
            keyboard = [[InlineKeyboardButton("🔓 查詢全美股8000+支", url="https://t.me/maggies_vip_analyst_bot")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ 免費版僅支援熱門股票查詢\n\n✅ 目前支援股票：\n{', '.join(self.sp500_symbols[:20])}\n... 共{len(self.sp500_symbols)}支\n\n💎 VIP版支援全美股8000+支股票！",
                reply_markup=reply_markup
            )
            return
        
        # 開始查詢流程
        processing = await update.message.reply_text("🔍 正在分析股票數據，請稍候...")
        
        try:
            # 使用yfinance獲取股票數據
            stock = yf.Ticker(symbol)
            hist = stock.history(period="5d")
            info = stock.info
            
            if hist.empty:
                await processing.edit_text("❌ 無法獲取股票數據，請檢查股票代碼或稍後再試")
                return
            
            # 計算關鍵指標
            current_price = hist['Close'][-1]
            prev_close = hist['Close'][-2] if len(hist) >= 2 else current_price
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100
            volume = hist['Volume'][-1]
            
            # 獲取公司基本信息
            company_name = info.get('longName', symbol)
            market_cap = info.get('marketCap', 0)
            
            # AI分析算法
            confidence = self._calculate_confidence(hist, info)
            recommendation = self._get_recommendation(change_percent, confidence, hist)
            
            # 格式化市值顯示
            if market_cap > 1e12:
                market_cap_str = f"${market_cap/1e12:.1f}T"
            elif market_cap > 1e9:
                market_cap_str = f"${market_cap/1e9:.1f}B"
            elif market_cap > 1e6:
                market_cap_str = f"${market_cap/1e6:.1f}M"
            else:
                market_cap_str = f"${market_cap:,.0f}"
            
            # 生成分析結果
            result = f"""📊 [{symbol}] {company_name[:30]} 股票分析

💰 當前價格：${current_price:.2f}
📈 漲跌幅：{change:+.2f} ({change_percent:+.2f}%)
📦 成交量：{volume:,.0f}
🏢 市值：{market_cap_str}

🎯 Maggie AI 建議：{recommendation}
📊 分析信心度：{confidence}%
⏰ 數據更新時間：{datetime.now().strftime('%m-%d %H:%M')}

💡 升級VIP解鎖專業功能：
✨ 技術分析指標(RSI/MACD/布林帶)
✨ 期權數據分析(Max Pain/Gamma)
✨ 即時新聞摘要與市場情緒
✨ 主力資金流向分析
✨ 個人化投資組合管理

🔓 立即升級：/vip

📊 今日剩餘免費查詢：{2-queries_today}次
📜 風險提示：投資有風險，決策需謹慎"""
            
            # 更新查詢計數
            self.user_queries[user_key] = queries_today + 1
            
            await processing.edit_text(result)
            
            # 記錄查詢日誌
            logger.info(f"✅ Query completed - User: {username}({user_id}), Symbol: {symbol}, Price: ${current_price:.2f}")
            
        except Exception as e:
            logger.error(f"❌ Query error for {symbol}: {str(e)}")
            await processing.edit_text(
                f"❌ 查詢 {symbol} 時發生錯誤\n\n可能原因：\n• 股票代碼不存在\n• 網路連線異常\n• 數據源暫時不可用\n\n請稍後再試或聯絡客服 @maggie_support"
            )
    
    def _calculate_confidence(self, hist, info):
        """計算AI分析信心度"""
        try:
            if len(hist) < 3:
                return 55
            
            # 基礎信心度
            base_confidence = 60
            
            # 基於價格穩定性
            price_volatility = hist['Close'].std() / hist['Close'].mean()
            if price_volatility < 0.05:  # 低波動性
                base_confidence += 10
            elif price_volatility > 0.15:  # 高波動性
                base_confidence -= 5
            
            # 基於成交量
            avg_volume = hist['Volume'].mean()
            if avg_volume > 1000000:  # 充足流動性
                base_confidence += 10
            elif avg_volume < 100000:  # 流動性不足
                base_confidence -= 10
            
            # 基於市值（如果有的話）
            market_cap = info.get('marketCap', 0)
            if market_cap > 100e9:  # 大型股
                base_confidence += 5
            elif market_cap < 1e9:  # 小型股
                base_confidence -= 5
            
            # 確保信心度在合理範圍內
            return max(40, min(85, base_confidence))
            
        except:
            return 60  # 默認信心度
    
    def _get_recommendation(self, change_percent, confidence, hist):
        """生成AI投資建議"""
        try:
            # 基於價格變化的初步建議
            if change_percent > 5:
                base_rec = "🟢 強烈買入" if confidence > 75 else "🟢 買入"
            elif change_percent > 2:
                base_rec = "🟢 買入" if confidence > 70 else "🟡 持有觀察"
            elif change_percent > -2:
                base_rec = "🟡 持有"
            elif change_percent > -5:
                base_rec = "🟠 謹慎持有" if confidence > 70 else "🔴 考慮賣出"
            else:
                base_rec = "🔴 賣出" if confidence > 75 else "🔴 考慮賣出"
            
            # 基於趨勢的調整
            if len(hist) >= 5:
                recent_trend = (hist['Close'][-1] - hist['Close'][-5]) / hist['Close'][-5]
                if recent_trend > 0.1 and change_percent > 0:  # 強勢上升趨勢
                    if "賣出" not in base_rec:
                        base_rec = base_rec.replace("持有", "買入")
                elif recent_trend < -0.1 and change_percent < 0:  # 強勢下降趨勢
                    if "買入" in base_rec:
                        base_rec = "🟡 持有觀察"
            
            return base_rec
            
        except:
            return "🟡 持有"  # 默認建議
    
    def run(self):
        logger.info("🚀 Maggie Stock AI Bot 正在啟動...")
        logger.info(f"✅ 支援股票數量: {len(self.sp500_symbols)}")
        logger.info("✅ 所有功能模組已載入")
        
        try:
            self.app.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"❌ Bot運行錯誤: {e}")

if __name__ == "__main__":
    # 檢查環境變量
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        logger.error("❌ 找不到 TELEGRAM_BOT_TOKEN 環境變量！")
        logger.error("💡 請在Railway設置環境變量：TELEGRAM_BOT_TOKEN")
        exit(1)
    
    logger.info("🔐 Bot Token 已設置")
    
    # 啟動Bot
    bot = MaggieBot(TOKEN)
    bot.run()
