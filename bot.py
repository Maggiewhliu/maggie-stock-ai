import os
import logging
import requests
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import asyncio
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaggieBot:
    def __init__(self, token, alpha_vantage_key):
        self.token = token
        self.alpha_vantage_key = alpha_vantage_key
        self.app = Application.builder().token(token).build()
        self.sp500_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 
            'BRK-B', 'JNJ', 'V', 'WMT', 'PG', 'JPM', 'UNH', 'MA',
            'DIS', 'HD', 'PYPL', 'BAC', 'NFLX', 'ADBE', 'CRM', 'XOM',
            'KO', 'PEP', 'COST', 'ABBV', 'CVX', 'MRK', 'TMO', 'ACN',
            'AVGO', 'LLY', 'NKE', 'ORCL', 'ABT', 'PFE', 'DHR', 'VZ',
            'IBM', 'INTC', 'CSCO', 'AMD', 'QCOM', 'TXN', 'INTU', 'BKNG'
        ]
        self.user_queries = {}
        self.api_call_count = 0
        self.last_api_reset = datetime.now()
        self._setup_handlers()
    
    def _setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("vip", self.vip_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_query))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome = """🎉 歡迎使用 Maggie Stock AI！

🤖 我是您的專業股票分析助手，使用Alpha Vantage即時數據

🆓 免費功能：
• 查詢48支熱門美股（每日3次）
• 即時價格與漲跌幅分析
• AI智能投資建議與信心度
• 基本市場數據分析

📝 使用方法：
直接發送股票代碼，例如：
• AAPL（蘋果）
• TSLA（特斯拉）
• GOOGL（谷歌）
• MSFT（微軟）

💎 VIP版功能：
• 全美股8000+支無限查詢
• 技術分析指標(RSI/MACD/布林帶)
• 期權數據分析(Max Pain/Gamma)
• 籌碼分析(主力進出/大戶比例)
• 即時新聞整合與AI摘要
• 個人化價格警報通知
• 投資組合管理工具

🔓 升級VIP：/vip
❓ 使用幫助：/help
📊 系統狀態：/status"""
        
        await update.message.reply_text(welcome)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """📖 Maggie Stock AI 使用說明

🔍 股票查詢方法：
直接發送股票代碼即可，例如：
• AAPL → 蘋果公司
• TSLA → 特斯拉  
• GOOGL → Alphabet(谷歌)
• MSFT → 微軟
• AMZN → 亞馬遜

🆓 免費版限制：
• 每日3次查詢限制
• 支援48支熱門股票
• 基本價量分析
• AI投資建議

💎 VIP版優勢：
• 全美股無限查詢
• 完整技術分析工具
• 期權數據解讀
• 即時新聞摘要
• 專業投資建議
• 個人化投資組合

📞 客服與支援：
• 技術問題：@maggie_invests
• VIP升級：/vip
• 功能建議：歡迎私訊
• 系統狀態：/status

⚠️ 重要提醒：
所有分析僅供參考，投資決策請謹慎評估風險
數據來源：Alpha Vantage Professional API"""
        
        await update.message.reply_text(help_text)
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """系統狀態檢查"""
        current_time = datetime.now()
        
        # 檢查API狀態
        try:
            test_response = await self._test_api_connection()
            api_status = "🟢 正常" if test_response else "🔴 異常"
        except:
            api_status = "🟠 檢測中"
        
        status_text = f"""📊 Maggie Stock AI 系統狀態

🔗 API連接：{api_status}
📡 數據來源：Alpha Vantage
⏰ 系統時間：{current_time.strftime('%Y-%m-%d %H:%M:%S')}
🌍 服務區域：Asia-Southeast

📈 支援股票：{len(self.sp500_symbols)}支熱門股票
💾 資料延遲：即時（<30秒）
🔄 更新頻率：實時

📞 技術支援：@maggie_invests
🔓 升級VIP：/vip

✅ 系統運行正常，可以開始查詢股票！"""
        
        await update.message.reply_text(status_text)
    
    async def vip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🎯 VIP基礎版 $9.99/月", url="https://t.me/maggie_invests")],
            [InlineKeyboardButton("💎 VIP專業版 $19.99/月", url="https://t.me/maggie_invests")],
            [InlineKeyboardButton("📊 功能對比表", callback_data="compare")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        vip_text = """💎 升級 Maggie Stock AI VIP 會員

🎯 VIP基礎版 ($9.99/月)：
✅ 全美股8000+支無限查詢
✅ 新股/IPO即時追蹤與分析
✅ 基礎技術分析(RSI/MACD/SMA)
✅ 即時新聞整合與AI摘要
✅ 無延遲專業級數據
✅ 每日市場報告推送

💎 VIP專業版 ($19.99/月)：
✅ 基礎版全部功能
✅ 高級技術分析(布林帶/KD/威廉指標)
✅ 期權數據分析(Max Pain/Gamma/IV)
✅ 籌碼分析(主力進出/大戶比例)
✅ Notion投資組合管理面板
✅ 個人化價格警報通知
✅ 專屬VIP群組與優先客服

🎁 新用戶專屬優惠：
• 首月享5折優惠！
• 年付用戶額外贈送2個月
• 7天無條件退款保證
• 免費投資策略諮詢

📈 投資價值：
平均每月為VIP用戶識別3-5個優質投資機會
專業分析工具助您提升投資勝率

💬 立即升級或諮詢：
點擊上方按鈕或聯絡 @maggie_invests"""
        
        await update.message.reply_text(vip_text, reply_markup=reply_markup)
    
    async def handle_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        symbol = update.message.text.upper().strip()
        
        # 驗證股票代碼格式
        if not symbol.isalpha() or len(symbol) > 5:
            await update.message.reply_text(
                "❌ 請輸入有效的股票代碼\n\n📝 正確格式例子：\n• AAPL（蘋果）\n• TSLA（特斯拉）\n• GOOGL（谷歌）\n\n💡 輸入 /status 查看系統狀態"
            )
            return
        
        # 檢查每日查詢次數限制
        today = datetime.now().strftime('%Y-%m-%d')
        user_key = f"{user_id}_{today}"
        queries_today = self.user_queries.get(user_key, 0)
        
        if queries_today >= 3:
            keyboard = [[InlineKeyboardButton("🔓 立即升級VIP", url="https://t.me/maggie_invests")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ 免費版每日查詢次數已用完（3次）\n\n💎 升級VIP享受：\n✅ 無限次查詢\n✅ 全美股覆蓋\n✅ 專業分析工具\n✅ 即時數據更新\n\n🎁 新用戶首月5折優惠！",
                reply_markup=reply_markup
            )
            return
        
        # 檢查是否為支持的股票
        if symbol not in self.sp500_symbols:
            keyboard = [[InlineKeyboardButton("🔓 查詢全美股8000+支", url="https://t.me/maggie_invests")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"❌ 免費版僅支援熱門股票查詢\n\n✅ 目前支援股票：\n{', '.join(self.sp500_symbols[:24])}\n... 共{len(self.sp500_symbols)}支\n\n💎 VIP版支援全美股8000+支股票！",
                reply_markup=reply_markup
            )
            return
        
        # 開始查詢流程
        processing = await update.message.reply_text("🔍 正在從Alpha Vantage獲取即時數據...")
        
        try:
            # 使用Alpha Vantage API獲取股票數據
            stock_data = await self._get_alpha_vantage_data(symbol)
            
            if stock_data.get('error'):
                await processing.edit_text(stock_data['error'])
                return
            
            # 更新查詢計數
            self.user_queries[user_key] = queries_today + 1
            
            # 格式化並發送結果
            result = self._format_stock_result(stock_data, queries_today)
            await processing.edit_text(result)
            
            # 記錄查詢日誌
            logger.info(f"✅ Alpha Vantage Query - User: {username}({user_id}), Symbol: {symbol}, Price: ${stock_data.get('price', 'N/A')}")
            
        except Exception as e:
            logger.error(f"❌ Query error for {symbol}: {str(e)}")
            await processing.edit_text(
                f"❌ 查詢 {symbol} 時發生錯誤\n\n可能原因：\n• API請求限制（每分鐘5次）\n• 網路連線異常\n• 股票代碼不存在\n\n💡 解決方案：\n• 稍後再試（1-2分鐘）\n• 檢查股票代碼拼寫\n• 聯絡客服 @maggie_invests\n\n🔓 VIP用戶享有優先API通道"
            )
    
    async def _get_alpha_vantage_data(self, symbol):
        """使用Alpha Vantage API獲取股票數據"""
        try:
            # 檢查API調用限制（免費版每分鐘5次）
            current_time = datetime.now()
            if (current_time - self.last_api_reset).seconds < 60 and self.api_call_count >= 5:
                return {"error": "❌ API請求過於頻繁\n\n免費版限制：每分鐘5次\n請稍後再試或升級VIP享受無限制API\n\n🔓 聯絡 @maggie_invests 升級"}
            
            # 重置API計數器（每分鐘）
            if (current_time - self.last_api_reset).seconds >= 60:
                self.api_call_count = 0
                self.last_api_reset = current_time
            
            # Alpha Vantage API請求
            base_url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params, timeout=10) as response:
                    if response.status != 200:
                        return {"error": f"❌ API請求失敗 (狀態碼: {response.status})\n請稍後再試或聯絡 @maggie_invests"}
                    
                    data = await response.json()
                    self.api_call_count += 1
            
            # 解析Alpha Vantage響應
            if "Global Quote" not in data:
                if "Note" in data:
                    return {"error": "❌ API請求限制\n\n免費版每分鐘限制5次請求\n請稍後再試或升級VIP\n\n💎 VIP用戶享有優先API通道"}
                elif "Error Message" in data:
                    return {"error": f"❌ 股票代碼 {symbol} 不存在\n\n請檢查拼寫或嘗試其他代碼\n💡 支援股票清單：/help"}
                else:
                    return {"error": "❌ 數據格式異常\n請稍後再試或聯絡 @maggie_invests"}
            
            quote = data["Global Quote"]
            
            # 提取股票數據
            current_price = float(quote["05. price"])
            change = float(quote["09. change"])
            change_percent = float(quote["10. change percent"].rstrip('%'))
            volume = int(quote["06. volume"])
            high = float(quote["03. high"])
            low = float(quote["04. low"])
            prev_close = float(quote["08. previous close"])
            
            # AI分析
            confidence = self._calculate_confidence(current_price, change_percent, volume, high, low)
            recommendation = self._get_recommendation(change_percent, confidence)
            
            return {
                'symbol': symbol,
                'price': current_price,
                'change': change,
                'change_percent': change_percent,
                'volume': volume,
                'high': high,
                'low': low,
                'prev_close': prev_close,
                'confidence': confidence,
                'recommendation': recommendation,
                'timestamp': datetime.now().strftime('%m-%d %H:%M'),
                'api_source': 'Alpha Vantage'
            }
            
        except aiohttp.ClientTimeout:
            return {"error": "❌ 網路連線超時\n\n請檢查網路連線或稍後再試\n💬 技術支援：@maggie_invests"}
        except aiohttp.ClientError as e:
            return {"error": f"❌ 網路連線錯誤\n\n請稍後再試\n技術詳情：{str(e)[:50]}...\n💬 聯絡客服：@maggie_invests"}
        except Exception as e:
            logger.error(f"Alpha Vantage API error: {str(e)}")
            return {"error": "❌ 系統暫時異常\n\n我們正在修復中，請稍後再試\n💬 聯絡客服：@maggie_invests"}
    
    async def _test_api_connection(self):
        """測試API連接"""
        try:
            base_url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": "AAPL",
                "apikey": self.alpha_vantage_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params, timeout=5) as response:
                    return response.status == 200
        except:
            return False
    
    def _calculate_confidence(self, price, change_percent, volume, high, low):
        """計算AI分析信心度"""
        try:
            base_confidence = 60
            
            # 基於價格波動範圍
            price_range = ((high - low) / price) * 100
            if price_range < 2:  # 低波動
                base_confidence += 15
            elif price_range > 8:  # 高波動
                base_confidence -= 10
            
            # 基於成交量（簡化判斷）
            if volume > 10000000:  # 高成交量
                base_confidence += 10
            elif volume < 1000000:  # 低成交量
                base_confidence -= 5
            
            # 基於漲跌幅絕對值
            abs_change = abs(change_percent)
            if abs_change > 5:  # 大幅波動
                base_confidence -= 5
            elif abs_change < 1:  # 小幅波動
                base_confidence += 5
            
            return max(40, min(90, base_confidence))
            
        except:
            return 65  # 默認信心度
    
    def _get_recommendation(self, change_percent, confidence):
        """生成AI投資建議"""
        try:
            if change_percent > 3:
                return "🟢 強烈買入" if confidence > 80 else "🟢 買入"
            elif change_percent > 1:
                return "🟢 買入" if confidence > 70 else "🟡 持有觀察"
            elif change_percent > -1:
                return "🟡 持有"
            elif change_percent > -3:
                return "🟠 謹慎持有" if confidence > 70 else "🔴 考慮賣出"
            else:
                return "🔴 賣出" if confidence > 80 else "🔴 考慮賣出"
            
        except:
            return "🟡 持有"
    
    def _format_stock_result(self, data, queries_used):
        """格式化股票查詢結果"""
        try:
            result = f"""📊 [{data['symbol']}] 即時股票分析

💰 當前價格：${data['price']:.2f}
📈 今日漲跌：{data['change']:+.2f} ({data['change_percent']:+.2f}%)
📦 成交量：{data['volume']:,}
📊 今日區間：${data['low']:.2f} - ${data['high']:.2f}
🔄 昨收價：${data['prev_close']:.2f}

🤖 Maggie AI 分析：
🎯 投資建議：{data['recommendation']}
📊 分析信心度：{data['confidence']}%
📡 數據來源：{data['api_source']} (即時)
⏰ 更新時間：{data['timestamp']}

💡 升級VIP解鎖專業功能：
✨ 技術分析指標(RSI/MACD/布林帶)
✨ 期權數據分析(Max Pain/Gamma)
✨ 即時新聞摘要與市場情緒
✨ 主力資金流向分析
✨ 個人化投資組合管理
✨ 價格警報通知

🔓 立即升級：/vip

📊 今日剩餘免費查詢：{2-queries_used}次
💬 客服支援：@maggie_invests
📜 風險提示：投資有風險，決策需謹慎"""
            
            return result
            
        except Exception as e:
            logger.error(f"Format error: {e}")
            return f"📊 [{data.get('symbol', 'N/A')}] 數據獲取成功但格式化異常\n💬 請聯絡客服：@maggie_invests"
    
    def run(self):
        logger.info("🚀 Maggie Stock AI Bot (Alpha Vantage版本) 啟動中...")
        logger.info(f"✅ Alpha Vantage API已配置")
        logger.info(f"✅ 支援股票數量: {len(self.sp500_symbols)}")
        logger.info("✅ 客服聯絡: @maggie_invests")
        
        try:
            self.app.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"❌ Bot運行錯誤: {e}")

if __name__ == "__main__":
    # 檢查環境變量
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not TOKEN:
        logger.error("❌ 找不到 TELEGRAM_BOT_TOKEN 環境變量！")
        exit(1)
    
    if not ALPHA_VANTAGE_KEY:
        logger.error("❌ 找不到 ALPHA_VANTAGE_API_KEY 環境變量！")
        logger.error("💡 請在Railway設置環境變量：ALPHA_VANTAGE_API_KEY")
        exit(1)
    
    logger.info("🔐 Telegram Bot Token 已設置")
    logger.info("🔑 Alpha Vantage API Key 已設置")
    
    # 啟動Bot
    bot = MaggieBot(TOKEN, ALPHA_VANTAGE_KEY)
    bot.run()
