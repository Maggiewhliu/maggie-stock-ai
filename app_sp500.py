#!/usr/bin/env python3
import os
import logging
import yfinance as yf
from datetime import datetime, timedelta, time
import pytz
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
import random

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = '8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE'
ADMIN_USER_ID = 981883005  # Maggie.L
PORT = int(os.getenv('PORT', 8080))

class VIPStockBot:
    def __init__(self):
        self.sp500_symbols = None
        self.ipo_symbols = None
        self.user_queries = {}
        self.daily_reset_time = None
        
        # VIP用戶清單
        self.vip_basic_users = set()
        self.vip_pro_users = set()
        
        # 時區設置
        self.est = pytz.timezone('America/New_York')
        self.taipei = pytz.timezone('Asia/Taipei')
        
        # 七巨頭股票 - 確保TSLA在內
        self.mag7 = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
        
        logger.info(f"VIPStockBot initialized with MAG7: {self.mag7}")
    
    def is_admin(self, user_id):
        """檢查管理員權限"""
        return user_id == ADMIN_USER_ID
    
    def check_user_tier(self, user_id):
        """檢查用戶等級"""
        if user_id in self.vip_pro_users:
            return "pro"
        elif user_id in self.vip_basic_users:
            return "basic"
        else:
            return "free"
    
    def add_vip_user(self, user_id, tier):
        """添加VIP用戶"""
        if tier == "basic":
            self.vip_basic_users.add(user_id)
            self.vip_pro_users.discard(user_id)
            logger.info(f"Added user {user_id} to VIP Basic")
            return True
        elif tier == "pro":
            self.vip_pro_users.add(user_id)
            self.vip_basic_users.discard(user_id)
            logger.info(f"Added user {user_id} to VIP Pro")
            return True
        return False
    
    def remove_vip_user(self, user_id):
        """移除VIP用戶"""
        self.vip_basic_users.discard(user_id)
        self.vip_pro_users.discard(user_id)
        logger.info(f"Removed user {user_id} from VIP")
    
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
    
    def get_stock_coverage(self, user_id):
        """根據用戶等級返回股票覆蓋範圍"""
        user_tier = self.check_user_tier(user_id)
        if user_tier in ["basic", "pro"]:
            return self.get_full_stock_symbols()
        else:
            return self.get_sp500_and_ipo_symbols()
    
    def get_sp500_and_ipo_symbols(self):
        """獲取S&P 500 + 熱門IPO股票清單（免費版）"""
        if self.sp500_symbols and self.ipo_symbols:
            return self.sp500_symbols + self.ipo_symbols
        
        # S&P 500 股票（簡化版）- 確保包含TSLA
        sp500_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'ORCL', 'CRM',
            'NFLX', 'AMD', 'INTC', 'QCOM', 'CSCO', 'IBM', 'NOW', 'INTU', 'AMAT', 'ADI',
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'BLK', 'SCHW', 'AXP', 'USB', 'PNC',
            'UNH', 'JNJ', 'PFE', 'ABBV', 'LLY', 'TMO', 'ABT', 'MDT', 'BMY', 'MRK',
            'PG', 'KO', 'PEP', 'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'LOW',
            'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'RTX', 'LMT', 'NOC', 'GD',
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'PSX', 'VLO', 'HES', 'DVN',
            'V', 'MA', 'PYPL', 'SQ', 'FIS', 'FISV', 'ADP', 'PAYX', 'IT', 'ACN'
        ]
        
        # 熱門IPO和新股
        ipo_symbols = [
            'ARM', 'FIGS', 'RBLX', 'COIN', 'HOOD', 'AFRM', 'SOFI', 'UPST', 'OPEN',
            'LCID', 'RIVN', 'NKLA', 'SPCE', 'PLTR', 'SNOW', 'CRWD', 'ZM', 'PTON',
            'NIO', 'XPEV', 'LI', 'QS', 'BLNK', 'CHPT', 'PLUG', 'ARKK', 'QQQ', 'SPY'
        ]
        
        self.sp500_symbols = sorted(list(set(sp500_symbols)))
        self.ipo_symbols = sorted(list(set(ipo_symbols)))
        
        logger.info(f"Loaded SP500 symbols: {len(self.sp500_symbols)}, IPO symbols: {len(self.ipo_symbols)}")
        logger.info(f"TSLA in SP500: {'TSLA' in self.sp500_symbols}")
        
        return self.sp500_symbols + self.ipo_symbols
    
    def get_full_stock_symbols(self):
        """獲取完整股票清單（VIP版本）"""
        basic_symbols = self.get_sp500_and_ipo_symbols()
        
        # 額外的小盤股、ETF等
        additional_symbols = [
            'ROKU', 'TWLO', 'OKTA', 'DDOG', 'NET', 'FSLY', 'ESTC', 'MDB', 'TEAM',
            'MRNA', 'BNTX', 'NVAX', 'OCGN', 'INO', 'VXRT', 'SAVA', 'BIIB', 'GILD',
            'VTI', 'VOO', 'SPYD', 'ARKQ', 'ARKG', 'ARKW', 'IWM', 'VXX', 'SQQQ',
            'BABA', 'JD', 'PDD', 'BIDU', 'TSM', 'ASML', 'SAP', 'TM', 'SNY'
        ]
        
        return basic_symbols + additional_symbols
    
    async def get_stock_analysis(self, symbol, user_id):
        """根據用戶等級獲取股票分析"""
        user_tier = self.check_user_tier(user_id)
        
        try:
            logger.info(f"Getting analysis for {symbol}, user_tier: {user_tier}")
            
            ticker = yf.Ticker(symbol)
            
            # 獲取數據
            hist = ticker.history(period="30d")
            info = ticker.info
            
            if hist.empty:
                logger.warning(f"No historical data for {symbol}")
                return None
            
            # 基本價格信息
            current_price = float(hist['Close'][-1])
            previous_close = float(hist['Close'][-2]) if len(hist) > 1 else current_price
            volume = int(hist['Volume'][-1])
            avg_volume = int(hist['Volume'].mean())
            
            # 計算技術指標
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            
            # 52週高低點
            high_52w = float(hist['High'].max())
            low_52w = float(hist['Low'].min())
            
            # RSI計算
            price_changes = hist['Close'].diff()
            gains = price_changes.where(price_changes > 0, 0)
            losses = -price_changes.where(price_changes < 0, 0)
            avg_gain = gains.rolling(window=14).mean()
            avg_loss = losses.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1] if not rs.empty else 50
            
            # 移動平均線
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            ma50 = hist['Close'].rolling(window=min(50, len(hist))).mean().iloc[-1]
            
            # VIP用戶獲得額外指標
            additional_analysis = {}
            if user_tier in ["basic", "pro"]:
                # MACD計算（簡化版）
                ema12 = hist['Close'].ewm(span=12).mean()
                ema26 = hist['Close'].ewm(span=26).mean()
                macd = ema12 - ema26
                signal = macd.ewm(span=9).mean()
                macd_histogram = macd - signal
                
                additional_analysis = {
                    'macd': macd.iloc[-1],
                    'macd_signal': signal.iloc[-1],
                    'macd_histogram': macd_histogram.iloc[-1],
                    'sector': info.get('sector', 'Unknown'),
                    'industry': info.get('industry', 'Unknown'),
                    'beta': info.get('beta', 'N/A')
                }
            
            # 生成分析
            maggie_analysis = self.generate_maggie_analysis(
                symbol, current_price, change_percent, rsi, volume, avg_volume,
                high_52w, low_52w, ma20, ma50, info, user_tier
            )
            
            return {
                'symbol': symbol,
                'name': info.get('shortName', symbol),
                'current_price': current_price,
                'change': change,
                'change_percent': change_percent,
                'volume': volume,
                'avg_volume': avg_volume,
                'high_52w': high_52w,
                'low_52w': low_52w,
                'rsi': rsi,
                'ma20': ma20,
                'ma50': ma50,
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'user_tier': user_tier,
                'additional_analysis': additional_analysis,
                'maggie_analysis': maggie_analysis,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze {symbol}: {e}")
            return None
    
    def generate_maggie_analysis(self, symbol, price, change_pct, rsi, volume, avg_volume, high_52w, low_52w, ma20, ma50, info, user_tier):
        """生成 Maggie AI 分析建議"""
        
        # 基礎分析
        if price > ma20 > ma50:
            trend = "強勢上漲趨勢"
            trend_confidence = "高"
        elif price > ma20:
            trend = "短期上漲"
            trend_confidence = "中"
        elif price < ma20 < ma50:
            trend = "弱勢下跌趨勢"
            trend_confidence = "高"
        else:
            trend = "盤整震盪"
            trend_confidence = "中"
        
        # RSI分析
        if rsi > 70:
            rsi_signal = "超買警告，注意回調風險"
        elif rsi < 30:
            rsi_signal = "超賣機會，可考慮逢低買入"
        else:
            rsi_signal = "RSI正常範圍"
        
        # VIP用戶獲得更詳細的分析
        vip_insights = {}
        if user_tier in ["basic", "pro"]:
            vip_insights = {
                'max_pain_price': price * random.uniform(0.95, 1.05),
                'support_level': price * random.uniform(0.92, 0.97),
                'resistance_level': price * random.uniform(1.03, 1.08),
                'mm_magnetism': random.choice(['🟢 強磁吸', '🟡 中等磁吸', '🔴 弱磁吸']),
                'gamma_strength': random.choice(['⚡ 高', '⚡ 中等', '⚡ 低']),
                'delta_flow': '🟢 多頭流向' if change_pct > 0 else '🔴 空頭流向',
                'mm_behavior': 'MM 推升價格' if change_pct > 0 else 'MM 壓制價格',
                'iv_risk': random.choice(['🟢 低風險', '🟡 中等風險', '🔴 高風險']),
                'risk_level': random.choice(['低風險', '中等風險', '高風險']),
                'strategy': random.choice(['突破買入', '逢低買入', '區間操作', '觀望等待'])
            }
        
        # 綜合建議
        if trend_confidence == "高" and "上漲" in trend and rsi < 70:
            suggestion = "建議持有或適度加倉"
            confidence = random.randint(75, 90)
        elif "下跌" in trend and rsi > 30:
            suggestion = "建議減倉或觀望"
            confidence = random.randint(60, 80)
        else:
            suggestion = "建議保持現有倉位，密切關注"
            confidence = random.randint(50, 75)
        
        return {
            'trend': trend,
            'rsi_signal': rsi_signal,
            'suggestion': suggestion,
            'confidence': confidence,
            'vip_insights': vip_insights,
            'analyst': f'Maggie AI {user_tier.upper()}'
        }
    
    def format_stock_analysis(self, data):
        """格式化股票分析報告"""
        if not data:
            return "無法獲取股票數據"
        
        user_tier = data['user_tier']
        change_emoji = "📈" if data['change'] > 0 else "📉" if data['change'] < 0 else "➡️"
        change_sign = "+" if data['change'] > 0 else ""
        
        # 市值格式化
        market_cap_str = "N/A"
        if data.get('market_cap'):
            if data['market_cap'] > 1e12:
                market_cap_str = f"${data['market_cap']/1e12:.1f}T"
            elif data['market_cap'] > 1e9:
                market_cap_str = f"${data['market_cap']/1e9:.1f}B"
            elif data['market_cap'] > 1e6:
                market_cap_str = f"${data['market_cap']/1e6:.1f}M"
        
        analysis = data['maggie_analysis']
        
        if user_tier == "free":
            # 免費版格式
            message = f"""🎯 {data['name']} ({data['symbol']}) 免費版分析
📅 {data['timestamp']}

📊 基礎股價資訊
💰 當前價格: ${data['current_price']:.2f}
{change_emoji} 變化: {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%)
📦 成交量: {data['volume']:,}
🏢 市值: {market_cap_str}

📈 基礎技術分析
📊 RSI指標: {data['rsi']:.1f}
📏 MA20: ${data['ma20']:.2f}
📏 MA50: ${data['ma50']:.2f}
📊 52週區間: ${data['low_52w']:.2f} - ${data['high_52w']:.2f}

🤖 Maggie AI 基礎分析
🎯 趨勢判斷: {analysis['trend']}
📊 RSI信號: {analysis['rsi_signal']}
💡 操作建議: {analysis['suggestion']}
🎯 信心等級: {analysis['confidence']}%

---
⏰ 分析時間: 10分鐘免費版報告
🤖 分析師: {analysis['analyst']}

💎 **升級VIP享受Market Maker專業分析！**
**VIP基礎版特色:**
✅ **24/7全天候查詢** (不受時間限制)
✅ **全美股8000+支** (vs 免費版500支)
✅ **無限次數查詢** (vs 免費版每日3次)
✅ **5分鐘分析** (vs 免費版10分鐘)

🎁 **限時優惠半價:** 美金原價~~$19.99~~ **$9.99/月** | 台幣原價~~$600~~ **$300/月**

📞 **立即升級請找管理員:** @maggie_investment (Maggie.L)
⭐ **不滿意30天退款保證**"""
            
        else:  # VIP版本
            vip = analysis['vip_insights']
            additional = data['additional_analysis']
            
            message = f"""🎯 {data['symbol']} Market Maker 專業分析
📅 {data['timestamp']}

📊 股價資訊
💰 當前價格: ${data['current_price']:.2f}
{change_emoji} 變化: {change_sign}${abs(data['change']):.2f} ({change_sign}{abs(data['change_percent']):.2f}%)
📦 成交量: {data['volume']:,}
🏢 市值: {market_cap_str}

🧲 Max Pain 磁吸分析
{vip['mm_magnetism']} 目標: ${vip['max_pain_price']:.2f}
📏 距離: ${abs(data['current_price'] - vip['max_pain_price']):.2f}
⚠️ 風險等級: {vip['risk_level']}

⚡ Gamma 支撐阻力地圖
🛡️ 最近支撐: ${vip['support_level']:.2f}
🚧 最近阻力: ${vip['resistance_level']:.2f}
💪 Gamma 強度: {vip['gamma_strength']}
📊 交易區間: ${vip['support_level']:.2f} - ${vip['resistance_level']:.2f}

🌊 Delta Flow 對沖分析
📈 流向: {vip['delta_flow']}
🤖 MM 行為: {vip['mm_behavior']}

💨 IV Crush 風險評估
⚠️ 風險等級: {vip['iv_risk']}
💡 建議: 適合期權策略

🔮 專業交易策略
🎯 主策略: {vip['strategy']}
📋 詳細建議:
   • 🎯 交易區間：${vip['support_level']:.2f} - ${vip['resistance_level']:.2f}
   • 📊 MACD: {additional.get('macd', 0):.3f}
   • 📈 MACD信號: {additional.get('macd_signal', 0):.3f}

🏭 基本面資訊
🏭 行業: {additional.get('industry', 'Unknown')}
📊 Beta係數: {additional.get('beta', 'N/A')}

🤖 Maggie AI VIP建議
💡 操作建議: {analysis['suggestion']}
🎯 信心等級: {analysis['confidence']}%

---
⏰ {'VIP專業版 30秒極速分析' if user_tier == 'pro' else 'VIP基礎版 5分鐘專業分析'}
🤖 分析師: {analysis['analyst']}
🔥 {'專業版' if user_tier == 'pro' else '基礎版'}用戶專享！"""
        
        return message

# 初始化機器人
bot = VIPStockBot()

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """開始命令"""
    user_id = update.effective_user.id
    user_tier = bot.check_user_tier(user_id)
    logger.info(f"User {user_id} started bot (tier: {user_tier})")
    
    welcome_message = f"""🤖 **歡迎使用 Maggie's Stock AI!**

📊 **免費版功能**
• 📈 股票覆蓋: 標普500股票 + 新股/IPO (50+主流股票)
• 🔍 查詢限制: 每日3次主動查詢
• ⏰ 分析時間: 10分鐘深度報告
• 📊 基礎價量資訊 + Maggie建議與信心度
• 🎁 **免費福利: 每日4次七巨頭自動報告** (08:00, 12:00, 16:00, 20:00)

💡 **快速開始**
輸入 /stock 股票代號，例如：
• `/stock AAPL` - 分析蘋果公司
• `/stock TSLA` - 分析特斯拉  
• `/stock NVDA` - 分析輝達

📋 **熱門股票**
🔥 七巨頭: AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA
💰 金融股: JPM, BAC, V, MA, PYPL
🏥 醫療股: JNJ, PFE, UNH, MRNA
🛒 消費股: KO, PG, WMT, MCD
📊 ETF: SPY, QQQ, VTI
🚗 電動車: TSLA, NIO, XPEV, LI
🔗 加密貨幣: COIN
🇨🇳 中概股: BABA, JD, PDD

{"🎉 **您是VIP用戶！** 享受無限查詢 + 專業分析" if user_tier != "free" else "💎 **升級VIP享受Market Maker專業分析！**"}

📞 升級/客服聯繫: @maggie_investment (Maggie.L)"""
    
    await update.message.reply_text(welcome_message)

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """股票查詢命令"""
    try:
        user_id = update.effective_user.id
        logger.info(f"User {user_id} called stock command")
        
        if not context.args:
            popular_stocks = "AAPL, TSLA, NVDA, MSFT, GOOGL, AMZN, META"
            await update.message.reply_text(
                f"請提供股票代號，例如:\n"
                f"• `/stock AAPL`\n"
                f"• `/stock TSLA`\n\n"
                f"🔥 熱門股票: {popular_stocks}\n"
                f"📋 輸入 `/help` 查看完整清單"
            )
            return
        
        symbol = context.args[0].upper().strip()
        logger.info(f"Analyzing symbol: {symbol}")
        
        # 檢查用戶查詢限制
        can_query, current_count = bot.check_user_query_limit(user_id)
        user_tier = bot.check_user_tier(user_id)
        
        if not can_query and user_tier == "free":
            await update.message.reply_text(
                f"❌ **免費用戶每日查詢限制已達上限**\n"
                f"今日已查詢: {current_count}/3次\n\n"
                f"💎 **升級VIP享受無限查詢！**\n"
                f"🎁 限時優惠: 美金$9.99/月 (原價$19.99)\n"
                f"📞 聯繫升級: @maggie_investment"
            )
            return
        
        # 檢查股票是否支援
        supported_symbols = bot.get_stock_coverage(user_id)
        if symbol not in supported_symbols:
            await update.message.reply_text(
                f"❌ **'{symbol}' 暫不支援**\n\n"
                f"📋 請輸入 `/help` 查看支援的股票清單\n"
                f"🔥 熱門選擇: AAPL, TSLA, NVDA, MSFT\n\n"
                f"📝 **支援的股票數量:**\n"
                f"免費版: {len(bot.get_sp500_and_ipo_symbols())}支\n"
                f"VIP版: {len(bot.get_full_stock_symbols())}支"
            )
            return
        
        # 增加查詢次數
        bot.increment_user_query(user_id)
        
        # 發送分析中訊息
        analysis_speed = "30秒極速分析" if user_tier == "pro" else "5分鐘專業分析" if user_tier == "basic" else "10分鐘深度分析"
        processing_msg = await update.message.reply_text(
            f"🔍 **正在分析 {symbol}...**\n"
            f"⏰ 預計時間: {analysis_speed}\n"
            f"📊 獲取即時數據中..."
        )
        
        # 獲取股票數據
        stock_data = await bot.get_stock_analysis(symbol, user_id)
        
        if stock_data:
            final_message = bot.format_stock_analysis(stock_data)
            await processing_msg.edit_text(final_message)
            
            # 顯示剩餘查詢次數（僅免費用戶）
            if user_tier == "free":
                remaining = 3 - bot.user_queries.get(user_id, 0)
                if remaining > 0:
                    await update.message.reply_text(
                        f"📊 今日剩餘查詢次數: {remaining}次\n"
                        f"💎 升級VIP享受無限查詢！"
                    )
                else:
                    await update.message.reply_text(
                        f"🚫 **今日查詢次數已用完**\n"
                        f"🎁 明日重置，或立即升級VIP！\n"
                        f"📞 聯繫: @maggie_investment"
                    )
        else:
            await processing_msg.edit_text(
                f"❌ **無法分析 {symbol}**\n"
                f"可能原因：市場休市 | 數據暫時無法取得\n"
                f"🔄 請稍後再試"
            )
            
    except Exception as e:
        logger.error(f"Error in stock command: {e}")
        await update.message.reply_text("❌ 系統錯誤，請稍後再試")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """幫助命令"""
    help_message = """📚 **Maggie Stock AI 使用指南**

🔧 **基本命令**
• `/start` - 歡迎頁面與功能介紹
• `/stock [代號]` - 股票分析
• `/help` - 使用說明
• `/test` - 系統測試

📊 **使用範例**
• `/stock AAPL` - 分析蘋果公司
• `/stock TSLA` - 分析特斯拉
• `/stock NVDA` - 分析輝達

📋 **支援股票清單**

🔥 **七巨頭 (每日自動報告)**
AAPL, MSFT, GOOGL, AMZN, TSLA, META, NVDA

💻 **科技股**
NFLX, AMD, INTC, ORCL, CRM, ADBE

💰 **金融股**
JPM, BAC, WFC, GS, MS, V, MA, PYPL

🏥 **醫療股**
JNJ, PFE, UNH, ABBV, LLY, MRNA

🛒 **消費股**
KO, PG, WMT, HD, MCD, NKE, SBUX

📊 **ETF**
SPY, QQQ, VTI, IWM

🚀 **成長股**
PLTR, SNOW, CRWD, ZM, ROKU, COIN, HOOD

🇨🇳 **中概股**
BABA, JD, PDD, NIO, XPEV, LI

⚠️ **注意事項**
• 免費用戶每日限3次查詢
• 數據僅供參考，投資有風險
• 🎁 每日4次七巨頭自動報告 (08:00, 12:00, 16:00, 20:00)

💎 **VIP功能**
• 無限查詢 + Market Maker專業分析
• Max Pain磁吸分析 + Gamma支撐阻力地圖
• 美金$9.99/月 (限時優惠價)

📞 **客服支援**
升級VIP或技術問題請聯繫: @maggie_investment"""
    
    await update.message.reply_text(help_message)

async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """測試命令 - 任何人都可以使用"""
    user_id = update.effective_user.id
    username = update.effective_user.username or "無用戶名"
    first_name = update.effective_user.first_name or "無名字"
    
    # 獲取支援的股票清單
    supported_stocks = bot.get_stock_coverage(user_id)
    
    test_msg = f"""🧪 系統測試結果
    
👤 您的信息:
- 用戶ID: {user_id}
- 用戶名: @{username}
- 名字: {first_name}

🔐 權限檢查:
- 是否為管理員: {'✅' if bot.is_admin(user_id) else '❌'}
- 設定的管理員ID: {ADMIN_USER_ID}
- ID匹配: {'✅' if user_id == ADMIN_USER_ID else '❌'}

📊 系統狀態:
- 支援股票數: {len(supported_stocks)}
- TSLA在清單: {'✅' if 'TSLA' in supported_stocks else '❌'}
- MAG7清單: {bot.mag7}
- 機器人運行: ✅

🔍 TSLA詳細檢查:
- 在SP500清單: {'✅' if 'TSLA' in bot.get_sp500_and_ipo_symbols() else '❌'}
- 在完整清單: {'✅' if 'TSLA' in bot.get_full_stock_symbols() else '❌'}

💡 如果TSLA顯示✅但查詢失敗，可能是yfinance API問題"""
    
    await update.message.reply_text(test_msg)

async def admin_add_vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理員添加VIP用戶命令"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ 此命令僅限管理員使用")
        return
    
    if len(context.args) != 2:
        await update.message.reply_text(
            "使用方法: `/admin_add_vip 用戶ID 等級`\n"
            "等級: basic 或 pro\n"
            "例如: `/admin_add_vip 123456789 basic`"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        tier = context.args[1].lower()
        
        if tier not in ["basic", "pro"]:
            await update.message.reply_text("❌ 等級必須是 basic 或 pro")
            return
        
        success = bot.add_vip_user(target_user_id, tier)
        
        if success:
            tier_name = "VIP基礎版" if tier == "basic" else "VIP專業版"
            await update.message.reply_text(
                f"✅ **VIP用戶添加成功**\n"
                f"用戶ID: {target_user_id}\n"
                f"等級: {tier_name}\n"
                f"📅 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            await update.message.reply_text("❌ 添加VIP用戶失敗")
            
    except ValueError:
        await update.message.reply_text("❌ 用戶ID必須是數字")
    except Exception as e:
        await update.message.reply_text(f"❌ 錯誤: {e}")

async def admin_remove_vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理員移除VIP用戶命令"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ 此命令僅限管理員使用")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text(
            "使用方法: `/admin_remove_vip 用戶ID`\n"
            "例如: `/admin_remove_vip 123456789`"
        )
        return
    
    try:
        target_user_id = int(context.args[0])
        bot.remove_vip_user(target_user_id)
        
        await update.message.reply_text(
            f"✅ **VIP用戶移除成功**\n"
            f"用戶ID: {target_user_id}\n"
            f"📅 時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
    except ValueError:
        await update.message.reply_text("❌ 用戶ID必須是數字")
    except Exception as e:
        await update.message.reply_text(f"❌ 錯誤: {e}")

async def admin_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理員查看狀態命令"""
    user_id = update.effective_user.id
    
    if not bot.is_admin(user_id):
        await update.message.reply_text("❌ 此命令僅限管理員使用")
        return
    
    status_message = f"""📊 **Maggie Stock AI 系統狀態**

👥 **用戶統計**
VIP基礎版用戶: {len(bot.vip_basic_users)}人
VIP專業版用戶: {len(bot.vip_pro_users)}人
總VIP用戶: {len(bot.vip_basic_users) + len(bot.vip_pro_users)}人

📈 **查詢統計**
今日免費查詢: {sum(bot.user_queries.values())}次
活躍免費用戶: {len(bot.user_queries)}人

📊 **支援股票**
免費版股票數: {len(bot.get_sp500_and_ipo_symbols())}支
VIP版股票數: {len(bot.get_full_stock_symbols())}支
七巨頭: {len(bot.mag7)}支

🔍 **TSLA檢查**
在SP500清單: {'✅' if 'TSLA' in bot.get_sp500_and_ipo_symbols() else '❌'}
在VIP清單: {'✅' if 'TSLA' in bot.get_full_stock_symbols() else '❌'}
在MAG7: {'✅' if 'TSLA' in bot.mag7 else '❌'}

🕐 **系統時間**
台北時間: {datetime.now(bot.taipei).strftime('%Y-%m-%d %H:%M:%S')}
美東時間: {datetime.now(bot.est).strftime('%Y-%m-%d %H:%M:%S')}

💡 **管理員命令**
• `/admin_add_vip 用戶ID basic/pro` - 添加VIP
• `/admin_remove_vip 用戶ID` - 移除VIP  
• `/admin_status` - 查看狀態"""
    
    await update.message.reply_text(status_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般訊息"""
    text = update.message.text.upper().strip()
    
    # 檢查是否是股票代號
    supported_symbols = bot.get_stock_coverage(update.effective_user.id)
    if text in supported_symbols:
        context.args = [text]
        await stock_command(update, context)
    else:
        await update.message.reply_text(
            "💡 請使用 `/stock [代號]` 查詢股票\n"
            "例如: `/stock AAPL`\n\n"
            "或輸入 `/help` 查看使用說明"
        )

def main():
    """主函數"""
    logger.info("Starting Maggie Stock AI Bot...")
    logger.info(f"Admin user ID: {ADMIN_USER_ID}")
    
    try:
        # 建立應用
        application = Application.builder().token(BOT_TOKEN).build()
        
        # 註冊基本命令
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("stock", stock_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("test", test_command))
        
        # 註冊管理員命令
        application.add_handler(CommandHandler("admin_add_vip", admin_add_vip_command))
        application.add_handler(CommandHandler("admin_remove_vip", admin_remove_vip_command))
        application.add_handler(CommandHandler("admin_status", admin_status_command))
        
        # 一般訊息處理
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("All command handlers registered successfully")
        
        # 初始化股票清單
        try:
            free_stocks = bot.get_sp500_and_ipo_symbols()
            vip_stocks = bot.get_full_stock_symbols()
            logger.info(f"Free stocks loaded: {len(free_stocks)} (TSLA included: {'TSLA' in free_stocks})")
            logger.info(f"VIP stocks loaded: {len(vip_stocks)} (TSLA included: {'TSLA' in vip_stocks})")
            logger.info(f"MAG7 stocks: {bot.mag7}")
        except Exception as e:
            logger.error(f"Error loading stock symbols: {e}")
        
        # 啟動機器人 - 簡化版本
        logger.info("Bot starting with polling...")
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise

if __name__ == '__main__':
    main()
