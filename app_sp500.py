#!/usr/bin/env python3
import os
import logging
import asyncio
from datetime import datetime, timedelta, time
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import random

# 設置日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 機器人令牌
BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'

class VIPStockBot:
    def __init__(self):
        self.user_queries = {}  # 追蹤用戶每日查詢次數
        self.daily_reset_time = None
        
        # VIP用戶清單
        self.vip_basic_users = set()
        self.vip_pro_users = set()
        
        # 時區設置
        self.est = pytz.timezone('America/New_York')
        self.taipei = pytz.timezone('Asia/Taipei')
        
        # 支援的股票清單
        self.supported_stocks = {
            # 科技股
            'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology'},
            'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Technology'},
            'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Technology'},
            'AMZN': {'name': 'Amazon.com Inc.', 'sector': 'Technology'},
            'TSLA': {'name': 'Tesla Inc.', 'sector': 'Automotive'},
            'META': {'name': 'Meta Platforms Inc.', 'sector': 'Technology'},
            'NVDA': {'name': 'NVIDIA Corporation', 'sector': 'Technology'},
            'NFLX': {'name': 'Netflix Inc.', 'sector': 'Entertainment'},
            'AMD': {'name': 'Advanced Micro Devices', 'sector': 'Technology'},
            'INTC': {'name': 'Intel Corporation', 'sector': 'Technology'},
            
            # 金融股
            'JPM': {'name': 'JPMorgan Chase & Co.', 'sector': 'Financial'},
            'BAC': {'name': 'Bank of America Corp.', 'sector': 'Financial'},
            'WFC': {'name': 'Wells Fargo & Company', 'sector': 'Financial'},
            'GS': {'name': 'Goldman Sachs Group', 'sector': 'Financial'},
            
            # 醫療股
            'JNJ': {'name': 'Johnson & Johnson', 'sector': 'Healthcare'},
            'PFE': {'name': 'Pfizer Inc.', 'sector': 'Healthcare'},
            'UNH': {'name': 'UnitedHealth Group', 'sector': 'Healthcare'},
            
            # 消費股
            'KO': {'name': 'Coca-Cola Company', 'sector': 'Consumer'},
            'PG': {'name': 'Procter & Gamble', 'sector': 'Consumer'},
            'WMT': {'name': 'Walmart Inc.', 'sector': 'Retail'},
            
            # ETF
            'SPY': {'name': 'SPDR S&P 500 ETF', 'sector': 'ETF'},
            'QQQ': {'name': 'Invesco QQQ Trust', 'sector': 'ETF'},
            'VTI': {'name': 'Vanguard Total Stock Market', 'sector': 'ETF'}
        }
        
    def check_user_tier(self, user_id):
        """檢查用戶等級"""
        if user_id in self.vip_pro_users:
            return "pro"
        elif user_id in self.vip_basic_users:
            return "basic"
        else:
            return "free"
    
    def reset_daily_queries(self):
        """重置每日查詢次數"""
        self.user_queries = {}
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        logger.info("Daily query limits reset")
    
    def check_user_query_limit(self, user_id):
        """檢查用戶查詢限制"""
        user_tier = self.check_user_tier(user_id)
        
        # VIP用戶無限制
        if user_tier in ["basic", "pro"]:
            return True, 0
        
        # 免費用戶檢查限制
        if self.daily_reset_time and datetime.now() >= self.daily_reset_time:
            self.reset_daily_queries()
        
        current_count = self.user_queries.get(user_id, 0)
        return current_count < 3, current_count
    
    def increment_user_query(self, user_id):
        """增加用戶查詢次數"""
        user_tier = self.check_user_tier(user_id)
        if user_tier == "free":
            self.user_queries[user_id] = self.user_queries.get(user_id, 0) + 1
    
    async def get_mock_stock_data(self, symbol, user_id):
        """獲取模擬股票數據（替代yfinance）"""
        if symbol not in self.supported_stocks:
            return None
        
        stock_info = self.supported_stocks[symbol]
        user_tier = self.check_user_tier(user_id)
        
        # 生成模擬數據
        base_price = random.uniform(50, 500)
        change_percent = random.uniform(-5, 5)
        change = base_price * (change_percent / 100)
        current_price = base_price + change
        
        rsi = random.uniform(30, 70)
        volume = random.randint(1000000, 50000000)
        
        # 生成分析
        analysis = self.generate_stock_analysis(
            symbol, current_price, change_percent, rsi, user_tier
        )
        
        return {
            'symbol': symbol,
            'name': stock_info['name'],
            'sector': stock_info['sector'],
            'current_price': current_price,
            'change': change,
            'change_percent': change_percent,
            'volume': volume,
            'rsi': rsi,
            'user_tier': user_tier,
            'analysis': analysis,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def generate_stock_analysis(self, symbol, price, change_pct, rsi, user_tier):
        """生成股票分析"""
        
        # 趨勢分析
        if change_pct > 2:
            trend = "強勢上漲"
            trend_emoji = "🚀"
        elif change_pct > 0:
            trend = "溫和上漲"
            trend_emoji = "📈"
        elif change_pct > -2:
            trend = "溫和下跌"
            trend_emoji = "📉"
        else:
            trend = "大幅下跌"
            trend_emoji = "⬇️"
        
        # RSI分析
        if rsi > 70:
            rsi_signal = "超買警告"
            rsi_emoji = "⚠️"
        elif rsi < 30:
            rsi_signal = "超賣機會"
            rsi_emoji = "💎"
        else:
            rsi_signal = "正常範圍"
            rsi_emoji = "✅"
        
        # 操作建議
        if trend == "強勢上漲" and rsi < 70:
            suggestion = "建議持有或適度加倉"
            confidence = random.randint(75, 90)
        elif "下跌" in trend and rsi > 30:
            suggestion = "建議減倉或觀望"
            confidence = random.randint(60, 80)
        else:
            suggestion = "建議保持現有倉位"
            confidence = random.randint(50, 75)
        
        # VIP用戶額外分析
        vip_analysis = {}
        if user_tier in ["basic", "pro"]:
            vip_analysis = {
                'support_level': price * random.uniform(0.92, 0.97),
                'resistance_level': price * random.uniform(1.03, 1.08),
                'target_price': price * random.uniform(1.05, 1.15),
                'stop_loss': price * random.uniform(0.85, 0.95),
                'risk_level': random.choice(['低風險', '中等風險', '高風險']),
                'strategy': random.choice(['突破買入', '逢低買入', '區間操作', '觀望等待'])
            }
        
        return {
            'trend': trend,
            'trend_emoji': trend_emoji,
            'rsi_signal': rsi_signal,
            'rsi_emoji': rsi_emoji,
            'suggestion': suggestion,
            'confidence': confidence,
            'vip_analysis': vip_analysis
        }
    
    def format_stock_message(self, data):
        """格式化股票分析訊息"""
        if not data:
            return "❌ 無法獲取股票數據"
        
        user_tier = data['user_tier']
        analysis = data['analysis']
        
        change_sign = "+" if data['change'] > 0 else ""
        
        if user_tier == "free":
            # 免費版格式
            message = f"""🎯 {data['name']} ({data['symbol']})
📅 {data['timestamp']}

💰 當前價格: ${data['current_price']:.2f}
{analysis['trend_emoji']} 變化: {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%)
📦 成交量: {data['volume']:,}
🏭 行業: {data['sector']}

📊 技術分析
{analysis['rsi_emoji']} RSI: {data['rsi']:.1f} ({analysis['rsi_signal']})
📈 趨勢: {analysis['trend']}

🤖 Maggie AI 建議
💡 操作建議: {analysis['suggestion']}
🎯 信心等級: {analysis['confidence']}%

---
⏰ 免費版 10分鐘分析報告
🤖 分析師: Maggie AI FREE

💎 **升級VIP享受專業分析！**
✅ 24/7全天候查詢
✅ 8000+支股票覆蓋
✅ 無限次查詢
✅ 進階技術指標

🎁 限時優惠: $9.99/月 (原價$19.99)
📞 升級請聯繫: @maggie_investment"""
            
        else:  # VIP版本
            vip = analysis['vip_analysis']
            
            message = f"""🎯 {data['name']} ({data['symbol']}) - VIP分析
📅 {data['timestamp']}

💰 當前價格: ${data['current_price']:.2f}
{analysis['trend_emoji']} 變化: {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%)
📦 成交量: {data['volume']:,}
🏭 行業: {data['sector']}

📊 技術分析
{analysis['rsi_emoji']} RSI: {data['rsi']:.1f} ({analysis['rsi_signal']})
📈 趨勢: {analysis['trend']}

🎯 VIP 交易策略
🛡️ 支撐位: ${vip['support_level']:.2f}
🚧 阻力位: ${vip['resistance_level']:.2f}
🎯 目標價: ${vip['target_price']:.2f}
🛑 停損位: ${vip['stop_loss']:.2f}
⚠️ 風險等級: {vip['risk_level']}
📋 建議策略: {vip['strategy']}

🤖 Maggie AI VIP建議
💡 操作建議: {analysis['suggestion']}
🎯 信心等級: {analysis['confidence']}%

---
⏰ VIP {'30秒極速分析' if user_tier == 'pro' else '5分鐘專業分析'}
🤖 分析師: Maggie AI {user_tier.upper()}
🔥 VIP專享深度分析！"""
        
        return message

# 初始化機器人
bot = VIPStockBot()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """開始命令"""
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started bot")
    
    welcome_message = """🤖 歡迎使用 Maggie Stock AI!

📊 **免費版功能**
• 📈 支援股票: 20+支熱門美股
• 🔍 查詢限制: 每日3次
• ⏰ 分析時間: 10分鐘報告
• 📊 基礎技術分析

💡 **快速開始**
輸入 /stock 股票代號，例如：
• /stock AAPL - 蘋果公司
• /stock TSLA - 特斯拉
• /stock NVDA - 輝達

📋 **支援股票清單**
• 科技股: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA
• 金融股: JPM, BAC, WFC, GS
• 醫療股: JNJ, PFE, UNH
• 消費股: KO, PG, WMT
• ETF: SPY, QQQ, VTI

💎 **升級VIP解鎖更多功能！**
🎁 現在升級享50%折扣！"""
    
    await update.message.reply_text(welcome_message)

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """股票查詢命令"""
    try:
        user_id = update.effective_user.id
        logger.info(f"User {user_id} called stock command")
        
        if not context.args:
            supported_list = ", ".join(list(bot.supported_stocks.keys())[:10])
            await update.message.reply_text(
                f"請提供股票代號，例如:\n"
                f"• /stock AAPL\n"
                f"• /stock TSLA\n\n"
                f"支援的股票: {supported_list}..."
            )
            return
        
        symbol = context.args[0].upper().strip()
        logger.info(f"Analyzing symbol: {symbol}")
        
        # 檢查用戶查詢限制
        can_query, current_count = bot.check_user_query_limit(user_id)
        user_tier = bot.check_user_tier(user_id)
        
        if not can_query and user_tier == "free":
            await update.message.reply_text(
                f"❌ 免費用戶每日查詢限制已達上限 (3次)\n"
                f"今日已查詢: {current_count}次\n\n"
                f"💎 升級VIP享受無限查詢！\n"
                f"📞 聯繫: @maggie_investment"
            )
            return
        
        # 檢查股票是否支援
        if symbol not in bot.supported_stocks:
            await update.message.reply_text(
                f"❌ '{symbol}' 暫不支援\n\n"
                f"📋 支援的股票代號:\n"
                f"{', '.join(list(bot.supported_stocks.keys()))}"
            )
            return
        
        # 增加查詢次數
        bot.increment_user_query(user_id)
        
        # 發送分析中訊息
        analysis_speed = "30秒極速分析" if user_tier == "pro" else "5分鐘分析" if user_tier == "basic" else "10分鐘分析"
        processing_msg = await update.message.reply_text(
            f"🔍 正在分析 {symbol}...\n⏰ 預計時間: {analysis_speed}"
        )
        
        # 模擬分析延遲
        await asyncio.sleep(2)
        
        # 獲取股票數據
        stock_data = await bot.get_mock_stock_data(symbol, user_id)
        
        if stock_data:
            final_message = bot.format_stock_message(stock_data)
            await processing_msg.edit_text(final_message)
            
            # 顯示剩餘查詢次數（僅免費用戶）
            if user_tier == "free":
                remaining = 3 - bot.user_queries.get(user_id, 0)
                if remaining > 0:
                    await update.message.reply_text(
                        f"📊 今日剩餘查詢次數: {remaining}次"
                    )
        else:
            await processing_msg.edit_text(f"❌ 無法分析 {symbol}")
            
    except Exception as e:
        logger.error(f"Error in stock command: {e}")
        await update.message.reply_text("❌ 系統錯誤，請稍後再試")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """幫助命令"""
    help_message = """📚 **Maggie Stock AI 使用指南**

🔧 **基本命令**
• /start - 歡迎頁面與功能介紹
• /stock [代號] - 股票分析
• /help - 使用說明

📊 **使用範例**
• /stock AAPL - 分析蘋果公司
• /stock TSLA - 分析特斯拉
• /stock NVDA - 分析輝達

📋 **支援股票**
科技股、金融股、醫療股、消費股、ETF等

⚠️ **注意事項**
• 免費用戶每日限3次查詢
• 數據僅供參考，投資有風險
• 升級VIP享受更多功能

💎 **需要協助？**
聯繫客服: @maggie_investment"""
    
    await update.message.reply_text(help_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般訊息"""
    text = update.message.text.upper()
    
    # 檢查是否是股票代號
    if text in bot.supported_stocks:
        # 模擬 /stock 命令
        context.args = [text]
        await stock_command(update, context)
    else:
        await update.message.reply_text(
            "💡 請使用 /stock [代號] 查詢股票\n"
            "例如: /stock AAPL\n\n"
            "或輸入 /help 查看使用說明"
        )

def main():
    """主函數"""
    logger.info("Starting Maggie Stock AI Bot...")
    
    try:
        # 建立應用
        application = Application.builder().token(BOT_TOKEN).build()
        
        # 註冊命令處理器
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("stock", stock_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # 啟動機器人
        logger.info("Bot starting with polling...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == '__main__':
    main()
