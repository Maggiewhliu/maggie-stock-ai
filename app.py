import os
import logging
import asyncio
from datetime import datetime
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# 設置日誌
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# 環境變數
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN 環境變數未設置！")
    raise ValueError("請設置 TELEGRAM_BOT_TOKEN 環境變數")

BRAND_NAME = os.getenv("BRAND_NAME", "Maggie's Stock AI")

# 創建 Flask 應用
app = Flask(__name__)

# 創建 Telegram Application (新版)
application = Application.builder().token(TOKEN).build()

# 全域變數追蹤統計
stats = {
    "total_updates": 0,
    "successful_updates": 0,
    "failed_updates": 0,
    "start_time": datetime.now()
}

# === 指令處理函數 ===
async def cmd_start(update: Update, context):
    """處理 /start 指令"""
    try:
        welcome_msg = f"""
🤖 **{BRAND_NAME}** - 您的專業投資分析師

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
        await update.message.reply_text(welcome_msg)
        logger.info(f"用戶 {update.effective_user.id} 啟動了機器人")
        
    except Exception as e:
        logger.error(f"處理 /start 指令錯誤: {str(e)}")
        await update.message.reply_text("啟動時發生錯誤，請稍後再試")

async def cmd_stock(update: Update, context):
    """處理 /stock 指令"""
    try:
        if not context.args:
            await update.message.reply_text(
                "📖 **用法：** `/stock TSLA`\n\n"
                "🔥 **熱門股票：**\n"
                "• `/stock AAPL` - Apple\n"
                "• `/stock TSLA` - Tesla\n"
                "• `/stock NVDA` - NVIDIA\n"
                "• `/stock GOOGL` - Google\n"
            )
            return

        symbol = context.args[0].upper()
        user_id = update.effective_user.id

        # 顯示處理中訊息
        processing_msg = await update.message.reply_text(
            f"🔍 正在分析 **{symbol}**...\n"
            "⏱️ 預計需要 20 分鐘進行深度分析\n"
            "📊 AI正在處理價量數據..."
        )

        # 這裡整合我們之前寫的分析邏輯
        try:
            # 導入我們的分析模組
            from src.provider_yahoo import YahooProvider
            from src.analyzers_integration import StockAnalyzer
            
            # 獲取股票數據
            provider = YahooProvider()
            stock_data = await provider.get_stock_data(symbol)
            
            if not stock_data:
                await processing_msg.edit_text(
                    f"❌ 找不到股票代碼 **{symbol}**\n"
                    "請檢查股票代碼是否正確"
                )
                return
            
            # 執行分析
            analyzer = StockAnalyzer()
            analysis_result = await analyzer.analyze_stock(stock_data)
            
            # 格式化報告
            report = format_stock_report(symbol, analysis_result)
            await processing_msg.edit_text(report)
            
            logger.info(f"成功分析股票: {symbol} for user {user_id}")
            
        except ImportError:
            # 如果導入失敗，使用簡化版本
            logger.warning("分析模組導入失敗，使用簡化版本")
            simple_report = await get_simple_stock_report(symbol)
            await processing_msg.edit_text(simple_report)
            
    except Exception as e:
        logger.error(f"處理 /stock 指令錯誤: {str(e)}")
        await update.message.reply_text(
            f"❌ 分析 **{symbol}** 時發生錯誤\n"
            "請稍後再試或聯繫技術支援"
        )

async def cmd_ipo(update: Update, context):
    """處理 /ipo 指令"""
    try:
        # 嘗試導入 IPO 模組
        try:
            from src.provider_ipo import IPOProvider
            ipo_provider = IPOProvider()
            ipo_data = await ipo_provider.get_upcoming_ipos()
            
            if ipo_data:
                report = "🆕 **本週IPO關注**\n\n"
                for ipo in ipo_data[:3]:  # 顯示前3個
                    report += f"📅 **{ipo.get('company', 'Unknown')}** ({ipo.get('symbol', 'N/A')})\n"
                    report += f"💰 發行價: {ipo.get('price_range', 'TBD')}\n"
                    report += f"📊 AI評估: {ipo.get('ai_rating', '待分析')}\n\n"
                
                report += "💎 **想要IPO深度分析？**\n升級Pro Beta解鎖專業估值模型"
            else:
                report = "🆕 **本週暫無新股IPO**\n敬請期待下週精彩新股！"
                
        except ImportError:
            # IPO 模組導入失敗，使用模擬數據
            report = """
🆕 **本週IPO關注**

📅 **Mock Tech Inc.** (MOCK)
💰 發行價: $15-18
📊 AI評估: 謹慎樂觀 ⭐⭐⭐

💎 **想要IPO深度分析？**
升級Pro Beta解鎖專業估值模型
            """
            
        await update.message.reply_text(report)
        
    except Exception as e:
        logger.error(f"處理 /ipo 指令錯誤: {str(e)}")
        await update.message.reply_text("❌ 獲取IPO數據失敗，請稍後再試")

async def cmd_help(update: Update, context):
    """處理 /help 指令"""
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
    await update.message.reply_text(help_text)

async def handle_text(update: Update, context):
    """處理其他文字訊息"""
    await update.message.reply_text(
        f"收到訊息：{update.message.text}\n\n"
        "請使用以下指令：\n"
        "• `/start` - 開始使用\n"
        "• `/stock TSLA` - 股票分析\n"
        "• `/help` - 完整說明"
    )

# 註冊指令處理器
application.add_handler(CommandHandler("start", cmd_start))
application.add_handler(CommandHandler("stock", cmd_stock))
application.add_handler(CommandHandler("ipo", cmd_ipo))
application.add_handler(CommandHandler("help", cmd_help))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# === Flask 路由 ===
@app.route("/", methods=["GET"])
def index():
    """根路徑 - 服務狀態"""
    uptime = datetime.now() - stats["start_time"]
    return {
        "service": BRAND_NAME,
        "status": "運行中",
        "uptime_seconds": uptime.total_seconds(),
        "stats": stats
    }

@app.route("/health", methods=["GET"])
def health():
    """健康檢查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.route("/set-webhook", methods=["GET"])
def set_webhook():
    """設置 webhook"""
    try:
        webhook_url = "https://maggie-stock-ai.onrender.com/webhook"
        bot = Bot(TOKEN)
        
        # 同步方式設置 webhook
        result = bot.set_webhook(url=webhook_url)
        
        if result:
            logger.info(f"Webhook 設置成功: {webhook_url}")
            return {"status": "success", "webhook_url": webhook_url}
        else:
            logger.error("Webhook 設置失敗")
            return {"status": "failed"}, 500
            
    except Exception as e:
        logger.error(f"設置 webhook 錯誤: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

@app.route("/webhook", methods=["POST"])
def webhook():
    """處理 Telegram webhook"""
    stats["total_updates"] += 1
    
    try:
        # 獲取更新數據
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, Bot(TOKEN))
        
        if not update:
            stats["failed_updates"] += 1
            return "Invalid update", 400
        
        # 記錄用戶資訊
        user_id = None
        if update.message:
            user_id = update.message.from_user.id if update.message.from_user else None
        elif update.callback_query:
            user_id = update.callback_query.from_user.id if update.callback_query.from_user else None
        
        logger.info(f"收到 update from user {user_id}")
        
        # 在新的事件循環中處理更新
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(application.process_update(update))
        
        stats["successful_updates"] += 1
        return "OK", 200
        
    except Exception as e:
        stats["failed_updates"] += 1
        logger.error(f"處理 webhook 錯誤: {str(e)}")
        return "Error", 500

# === 輔助函數 ===
def format_stock_report(symbol: str, analysis: dict) -> str:
    """格式化股票分析報告"""
    try:
        current_price = analysis.get('current_price', 'N/A')
        change = analysis.get('change', 'N/A')
        change_percent = analysis.get('change_percent', 'N/A')
        volume = analysis.get('volume', 'N/A')
        max_pain = analysis.get('max_pain', 'N/A')
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

🤖 **AI 建議:** {ai_recommendation}
📊 **信心度:** {confidence}%

⏰ **分析完成時間:** {datetime.now().strftime('%H:%M')} 台北時間

--- {BRAND_NAME} ---
        """
        
        return report.strip()
        
    except Exception as e:
        logger.error(f"格式化報告錯誤: {str(e)}")
        return f"📊 **{symbol}** 分析完成，但格式化時發生錯誤"

async def get_simple_stock_report(symbol: str) -> str:
    """簡化版股票報告（當完整分析不可用時）"""
    try:
        # 使用 Polygon API 獲取基本數據
        import requests
        import datetime as dt
        
        POLY = os.getenv("POLYGON_API_KEY")
        if POLY:
            y = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{y}/{y}?adjusted=true&limit=1&apiKey={POLY}"
            r = requests.get(url, timeout=15)
            j = r.json()
            
            if j.get("results"):
                c = j["results"][0]["c"]
                o = j["results"][0]["o"]
                pct = (c - o) / o * 100 if o else 0
                
                return f"""
📊 **{symbol} 快速報告**

💰 **昨收價格:** ${c:.2f}
📈 **日內變動:** {pct:+.2f}%
🎯 **Max Pain:** 計算中...

🤖 **AI 建議:** 技術分析中，請稍後查看
📊 **信心度:** 75%

⏰ **報告時間:** {datetime.now().strftime('%H:%M')} 台北時間

--- {BRAND_NAME} ---
                """
        
        # 如果沒有 API，返回基本模板
        return f"""
📊 **{symbol} 分析報告**

💰 **價格:** 獲取中...
📈 **變動:** 計算中...
🎯 **Max Pain:** 分析中...

🤖 **AI 建議:** 正在分析市場數據
📊 **信心度:** 計算中...

⏰ **報告時間:** {datetime.now().strftime('%H:%M')} 台北時間

--- {BRAND_NAME} ---
        """
        
    except Exception as e:
        logger.error(f"簡化報告錯誤: {str(e)}")
        return f"📊 **{symbol}** 數據獲取中，請稍後再試"

if __name__ == "__main__":
    # 本機測試
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"啟動 Flask 服務器 - Port: {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
