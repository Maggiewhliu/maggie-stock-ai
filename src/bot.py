import logging
import re
from telegram import Update
from telegram.ext import ContextTypes
from .provider_yahoo import YahooProvider
from .analyzers import StockAnalyzer

logger = logging.getLogger(__name__)

class StockBot:
    def __init__(self):
        self.yahoo_provider = YahooProvider()
        self.analyzer = StockAnalyzer()
    
    async def handle_stock_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        處理 /stock 命令
        """
        try:
            # 獲取用戶輸入的股票代碼
            if not context.args:
                await update.message.reply_text(
                    "❌ 請提供股票代碼\n\n"
                    "📝 使用方法:\n"
                    "• /stock AAPL\n"
                    "• /stock MSFT\n"
                    "• /stock GOOGL\n\n"
                    "範例: /stock AAPL"
                )
                return
            
            symbol = context.args[0].upper().strip()
            
            # 驗證股票代碼格式
            if not self._validate_symbol(symbol):
                await update.message.reply_text(
                    f"❌ 無效的股票代碼格式: {symbol}\n\n"
                    "✅ 請檢查:\n"
                    "• 股票代碼是否正確\n"
                    "• 是否為美股上市公司\n"
                    "• 嘗試使用完整代碼\n\n"
                    "範例: /stock AAPL"
                )
                return
            
            # 發送處理中訊息
            processing_msg = await update.message.reply_text(
                f"🔍 **正在深度分析 {symbol}...**\n\n"
                f"⏱️ 預計1-3分鐘完成專業分析\n"
                f"📊 正在獲取即時數據..."
            )
            
            # 獲取股票數據
            try:
                stock_data = self.yahoo_provider.get_stock_data(symbol)
                
                # 格式化基本資訊
                basic_info = self._format_basic_info(stock_data)
                
                # 更新訊息顯示基本資訊
                await processing_msg.edit_text(
                    f"{basic_info}\n\n"
                    f"🤖 正在進行AI深度分析...\n"
                    f"📈 技術分析進行中..."
                )
                
                # 進行深度分析
                analysis = await self._perform_analysis(symbol, stock_data)
                
                # 發送完整分析報告
                final_report = self._format_final_report(stock_data, analysis)
                await processing_msg.edit_text(final_report)
                
            except Exception as e:
                logger.error(f"獲取股票數據失敗: {e}")
                await processing_msg.edit_text(
                    f"❌ 找不到股票代碼 {symbol}\n\n"
                    f"💡 請檢查:\n"
                    f"• 股票代碼是否正確\n"
                    f"• 是否為美股上市公司\n"
                    f"• 嘗試使用完整代碼\n\n"
                    f"範例: /stock AAPL"
                )
                
        except Exception as e:
            logger.error(f"處理股票命令時發生錯誤: {e}")
            await update.message.reply_text(
                "❌ 系統暫時無法處理您的請求\n\n"
                "請稍後再試，或聯繫客服協助"
            )
    
    def _validate_symbol(self, symbol: str) -> bool:
        """驗證股票代碼格式"""
        if not symbol or len(symbol) < 1 or len(symbol) > 6:
            return False
        
        # 檢查是否只包含字母和數字
        if not re.match(r'^[A-Z0-9.]+$', symbol):
            return False
        
        return True
    
    def _format_basic_info(self, stock_data: dict) -> str:
        """格式化基本股票資訊"""
        change_emoji = "📈" if stock_data['change'] > 0 else "📉" if stock_data['change'] < 0 else "➡️"
        change_sign = "+" if stock_data['change'] > 0 else ""
        
        return f"""
🔍 **股票查詢結果**

📊 **{stock_data['name']} ({stock_data['symbol']})**
💰 當前價格: ${stock_data['current_price']:.2f}
{change_emoji} 漲跌: {change_sign}${stock_data['change']:.2f} ({change_sign}{stock_data['change_percent']:.2f}%)
📊 成交量: {stock_data['volume']:,}

🕐 數據更新: {stock_data.get('timestamp', 'N/A')}
📡 數據來源: {stock_data.get('data_source', 'Yahoo Finance')}
        """.strip()
    
    async def _perform_analysis(self, symbol: str, stock_data: dict) -> dict:
        """執行深度分析"""
        try:
            # 這裡調用你的分析器
            analysis = await self.analyzer.analyze_stock(symbol, stock_data)
            return analysis
        except Exception as e:
            logger.error(f"分析失敗: {e}")
            return {
                'status': 'error',
                'message': '分析過程中發生錯誤',
                'recommendation': '建議稍後重試'
            }
    
    def _format_final_report(self, stock_data: dict, analysis: dict) -> str:
        """格式化最終報告"""
        change_emoji = "📈" if stock_data['change'] > 0 else "📉" if stock_data['change'] < 0 else "➡️"
        change_sign = "+" if stock_data['change'] > 0 else ""
        
        report = f"""
🔍 **{stock_data['name']} ({stock_data['symbol']}) - 深度分析報告**

💰 **即時價格資訊**
當前價格: ${stock_data['current_price']:.2f}
{change_emoji} 漲跌: {change_sign}${stock_data['change']:.2f} ({change_sign}{stock_data['change_percent']:.2f}%)
成交量: {stock_data['volume']:,}
        """
        
        # 添加分析結果
        if analysis.get('status') == 'success':
            report += f"""

🤖 **AI分析結果**
投資建議: {analysis.get('recommendation', 'N/A')}
信心度: {analysis.get('confidence', 'N/A')}
風險等級: {analysis.get('risk_level', 'N/A')}

📈 **技術分析**
趨勢: {analysis.get('trend', 'N/A')}
支撐位: {analysis.get('support', 'N/A')}
阻力位: {analysis.get('resistance', 'N/A')}
            """
        else:
            report += f"""

⚠️ **分析狀態**
{analysis.get('message', '分析完成，但部分功能暫時不可用')}
            """
        
        report += f"""

⏰ **分析完成時間**: {stock_data.get('timestamp', 'N/A')}
📊 **數據來源**: {stock_data.get('data_source', 'Yahoo Finance')}

---
💎 想要更快速的分析？升級到 Pro Beta 版本！
        """
        
        return report.strip()
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        處理一般文字訊息，檢查是否包含股票代碼
        """
        text = update.message.text.upper()
        
        # 檢查是否看起來像股票代碼
        stock_pattern = r'\b[A-Z]{2,5}\b'
        matches = re.findall(stock_pattern, text)
        
        if matches:
            # 檢查常見股票代碼
            common_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
            found_stocks = [match for match in matches if match in common_stocks]
            
            if found_stocks:
                await update.message.reply_text(
                    f"🔍 偵測到股票代碼: {', '.join(found_stocks)}\n\n"
                    f"使用 /stock {found_stocks[0]} 查詢詳細資訊"
                )

# 錯誤處理裝飾器
def error_handler(func):
    """錯誤處理裝飾器"""
    async def wrapper(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(self, update, context)
        except Exception as e:
            logger.error(f"處理訊息時發生錯誤: {e}")
            if update.message:
                await update.message.reply_text(
                    "❌ 系統暫時發生錯誤\n\n"
                    "請稍後再試，我們會盡快修復問題"
                )
    return wrapper
