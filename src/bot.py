from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import logging
import asyncio
from datetime import datetime
import os

# 導入你的其他模組
try:
    from .service import StockService
    from .analyzers import StockAnalyzer
    from .provider_yahoo import YahooProvider
    from .provider_ipo import IPOProvider
    from .cache import CacheManager
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from service import StockService
    from analyzers import StockAnalyzer
    from provider_yahoo import YahooProvider
    from provider_ipo import IPOProvider
    from cache import CacheManager

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaggieStockBot:
    def __init__(self):
        self.stock_service = StockService()
        self.analyzer = StockAnalyzer()
        self.yahoo_provider = YahooProvider()
        self.ipo_provider = IPOProvider()
        self.cache = CacheManager()
        
        # 用戶權限管理（簡單版本）
        self.user_limits = {}  # user_id: {"daily_count": 0, "plan": "free"}
        
    async def check_user_limit(self, user_id: int) -> tuple[bool, str]:
        """檢查用戶查詢限制"""
        today = datetime.now().strftime("%Y-%m-%d")
        user_key = f"{user_id}_{today}"
        
        if user_key not in self.user_limits:
            self.user_limits[user_key] = {"daily_count": 0, "plan": "free"}
        
        user_data = self.user_limits[user_key]
        
        # 免費用戶每日限制 10 次
        if user_data["plan"] == "free" and user_data["daily_count"] >= 10:
            return False, "🚫 免費版每日查詢限制 10 次已用完\n💎 升級 Pro Beta 解鎖無限查詢"
        
        return True, ""

# 創建全局 bot 實例
maggie_bot = MaggieStockBot()

# /start 指令
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_msg = """
🤖 **Maggie's Stock AI** - 您的專業投資分析師

📊 **功能介紹：**
• `/stock TSLA` - 20分鐘深度分析報告
• `/ipo` - 最新IPO資訊和分析
• `/help` - 完整指令說明

🆓 **免費版特色：**
• 標普500股票分析
• 每日10次查詢限制
• 新股/IPO風險評估
• 每日4次七巨頭自動報告

💎 **想要更多功能？**
Pro Beta: 無限查詢 + 2分鐘快速分析
VIP: 30秒即時分析 + 期權深度分析

現在開始您的投資分析之旅吧！ 📈
    """
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

# /stock <ticker> 指令 - 核心功能
async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "📖 **用法：** `/stock TSLA`\n\n"
            "🔥 **熱門股票：**\n"
            "• `/stock AAPL` - Apple\n"
            "• `/stock TSLA` - Tesla\n"
            "• `/stock NVDA` - NVIDIA\n"
            "• `/stock GOOGL` - Google\n",
            parse_mode='Markdown'
        )
        return
    
    user_id = update.effective_user.id
    symbol = context.args[0].upper()
    
    # 檢查用戶查詢限制
    can_query, limit_msg = await maggie_bot.check_user_limit(user_id)
    if not can_query:
        await update.message.reply_text(limit_msg)
        return
    
    # 顯示分析開始訊息
    processing_msg = await update.message.reply_text(
        f"🔍 正在分析 **{symbol}**...\n"
        "⏱️ 預計需要 20 分鐘進行深度分析\n"
        "📊 AI正在處理價量數據...",
        parse_mode='Markdown'
    )
    
    try:
        # 更新用戶查詢計數
        today = datetime.now().strftime("%Y-%m-%d")
        user_key = f"{user_id}_{today}"
        maggie_bot.user_limits[user_key]["daily_count"] += 1
        
        # 從快取檢查
        cached_result = maggie_bot.cache.get(f"stock_{symbol}")
        
        if cached_result:
            logger.info(f"使用快取數據: {symbol}")
            analysis_result = cached_result
        else:
            # 獲取實時數據
            logger.info(f"獲取 {symbol} 的實時數據...")
            stock_data = await maggie_bot.yahoo_provider.get_stock_data(symbol)
            
            if not stock_data:
                await processing_msg.edit_text(
                    f"❌ 找不到股票代碼 **{symbol}**\n"
                    "請檢查股票代碼是否正確",
                    parse_mode='Markdown'
                )
                return
            
            # 執行分析
            logger.info(f"分析 {symbol} 數據...")
            analysis_result = await maggie_bot.analyzer.analyze_stock(stock_data)
            
            # 快取結果（5分鐘）
            maggie_bot.cache.set(f"stock_{symbol}", analysis_result, 300)
        
        # 格式化回報
        report = format_stock_report(symbol, analysis_result)
        
        # 更新訊息為最終結果
        await processing_msg.edit_text(report, parse_mode='Markdown')
        
        logger.info(f"成功分析股票: {symbol} for user {user_id}")
        
    except Exception as e:
        logger.error(f"分析股票 {symbol} 時發生錯誤: {str(e)}")
        await processing_msg.edit_text(
            f"❌ 分析 **{symbol}** 時發生錯誤\n"
            "請稍後再試或聯繫技術支援",
            parse_mode='Markdown'
        )

# /ipo 指令 - IPO資訊
async def ipo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        ipo_data = await maggie_bot.ipo_provider.get_upcoming_ipos()
        ipo_report = format_ipo_report(ipo_data)
        await update.message.reply_text(ipo_report, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"獲取IPO數據錯誤: {str(e)}")
        await update.message.reply_text("❌ 獲取IPO數據失敗，請稍後再試")

# /help 指令
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
📚 **Maggie's Stock AI 完整指令**

**📊 股票分析：**
• `/stock AAPL` - 股票深度分析
• `/stock TSLA` - Tesla 分析報告

**🆕 IPO功能：**
• `/ipo` - 最新IPO資訊

**ℹ️ 系統資訊：**
• `/start` - 歡迎訊息
• `/help` - 這個說明

**🔄 自動功能：**
• 每日4次七巨頭自動推送
• IPO上市提醒
• Max Pain磁吸分析

**💡 使用技巧：**
• 免費版每日可查詢10次
• 支援標普500所有股票
• 建議在美股開盤時間使用

有問題嗎？聯繫 @maggiewhliu
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

def format_stock_report(symbol: str, analysis: dict) -> str:
    """格式化股票分析報告"""
    try:
        current_price = analysis.get('current_price', 'N/A')
        change = analysis.get('change', 'N/A')
        change_percent = analysis.get('change_percent', 'N/A')
        volume = analysis.get('volume', 'N/A')
        max_pain = analysis.get('max_pain', 'N/A')
        gamma_levels = analysis.get('gamma_levels', {})
        ai_recommendation = analysis.get('ai_recommendation', '無建議')
        confidence = analysis.get('confidence', 'N/A')
        
        # 判斷漲跌 emoji
        trend_emoji = "📈" if isinstance(change, (int, float)) and change > 0 else "📉" if isinstance(change, (int, float)) and change < 0 else "📊"
        
        report = f"""
📊 **{symbol} 深度分析報告**

💰 **當前價格:** ${current_price}
{trend_emoji} **變動:** {change} ({change_percent}%)
📦 **成交量:** {volume:,} 股

⚡ **Max Pain 分析:**
🎯 磁吸價位: ${max_pain}

🛡️ **Gamma 支撐阻力:**
• 支撐位: ${gamma_levels.get('support', 'N/A')}
• 阻力位: ${gamma_levels.get('resistance', 'N/A')}

🤖 **AI 建議:** {ai_recommendation}
📊 **信心度:** {confidence}%

⏰ **分析完成時間:** {datetime.now().strftime('%H:%M')} 台北時間
📈 **數據延遲:** 1-3分鐘

--- Maggie's Stock AI ---
        """
        
        return report.strip()
        
    except Exception as e:
        logger.error(f"格式化報告錯誤: {str(e)}")
        return f"📊 **{symbol}** 分析完成，但格式化時發生錯誤"

def format_ipo_report(ipo_data: list) -> str:
    """格式化IPO報告"""
    if not ipo_data:
        return "🆕 **本週暫無新股IPO**\n敬請期待下週精彩新股！"
    
    report = "🆕 **本週IPO關注**\n\n"
    
    for ipo in ipo_data[:3]:  # 顯示前3個
        report += f"📅 **{ipo.get('company', 'Unknown')}** ({ipo.get('symbol', 'N/A')})\n"
        report += f"💰 發行價: ${ipo.get('price_range', 'TBD')}\n"
        report += f"📊 AI評估: {ipo.get('ai_rating', '待分析')}\n\n"
    
    report += "💎 **想要IPO深度分析？**\n升級Pro Beta解鎖專業估值模型"
    
    return report

def register_handlers(application: Application) -> None:
    """註冊所有指令處理器"""
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stock", stock))
    application.add_handler(CommandHandler("ipo", ipo))
    application.add_handler(CommandHandler("help", help_command))

# 自動報告功能（定時任務）
async def send_daily_report(application: Application) -> None:
    """發送每日自動報告"""
    try:
        # 獲取七巨頭數據
        magnificent_seven = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
        
        report = "🎁 **免費用戶專享：七巨頭晨報**\n\n"
        report += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} 台北時間\n\n"
        
        for symbol in magnificent_seven[:3]:  # 顯示前3個
            try:
                data = await maggie_bot.yahoo_provider.get_stock_data(symbol)
                if data:
                    price = data.get('current_price', 'N/A')
                    change = data.get('change', 0)
                    change_pct = data.get('change_percent', 'N/A')
                    emoji = "📈" if change > 0 else "📉" if change < 0 else "📊"
                    
                    report += f"{emoji} **{symbol}** ${price} ({change_pct}%)\n"
            except:
                report += f"📊 **{symbol}** 數據載入中...\n"
        
        report += "\n🔄 下次報告: 12:00 台北時間"
        
        # 這裡需要你的用戶ID列表來發送報告
        # 暫時使用日誌輸出
        logger.info(f"自動報告生成: {datetime.now()}")
        print(report)  # 開發階段用 print，實際部署時發送給用戶
        
    except Exception as e:
        logger.error(f"自動報告生成錯誤: {str(e)}")

if __name__ == "__main__":
    # 測試模式
    print("Maggie Stock Bot 已載入")
    print("請確保所有依賴模組都已正確實現")
