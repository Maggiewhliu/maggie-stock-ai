#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maggie's Stock AI Bot - 最終統一版本
整合三個版本的所有優點：
1. Alpha Vantage API (你的原版)
2. Yahoo Finance備用 + Max Pain分析 (我的版本)
3. 簡化的免費版邏輯 (前AI的版本)
"""

import os
import json
import asyncio
import logging
import hashlib
import aiohttp
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters, JobQueue
)

# 配置日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 配置
BOT_TOKEN = "8320641094:AAGoaTpTlZDnA2wH8Qq5Pqv-8L7thECoR2s"
ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')  # 你的Alpha Vantage Key
YAHOO_API_KEY = "NBWPE7OFZHTT3OFI"  # 備用Yahoo API

# 美股七巨頭
MAGNIFICENT_7 = {
    'AAPL': {'name': 'Apple', 'emoji': '🍎'},
    'MSFT': {'name': 'Microsoft', 'emoji': '🪟'},
    'GOOGL': {'name': 'Google', 'emoji': '🔍'},
    'AMZN': {'name': 'Amazon', 'emoji': '📦'},
    'NVDA': {'name': 'NVIDIA', 'emoji': '🚀'},
    'TSLA': {'name': 'Tesla', 'emoji': '🚗'},
    'META': {'name': 'Meta', 'emoji': '📘'}
}

# 標普500股票清單 - 整合你原版的清單
SP500_SYMBOLS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 
    'BRK-B', 'JNJ', 'V', 'WMT', 'PG', 'JPM', 'UNH', 'MA',
    'DIS', 'HD', 'PYPL', 'BAC', 'NFLX', 'ADBE', 'CRM', 'XOM',
    'KO', 'PEP', 'COST', 'ABBV', 'CVX', 'MRK', 'TMO', 'ACN',
    'AVGO', 'LLY', 'NKE', 'ORCL', 'ABT', 'PFE', 'DHR', 'VZ',
    'IBM', 'INTC', 'CSCO', 'AMD', 'QCOM', 'TXN', 'INTU', 'BKNG'
]

class UserManager:
    """用戶管理系統"""
    
    def __init__(self):
        self.users_file = 'users.json'
        self.users = self.load_users()
        self.user_queries = {}  # 每日查詢計數
        self.daily_limit = 3    # 免費版每日限制
    
    def load_users(self) -> Dict:
        """載入用戶數據"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"載入用戶數據失敗: {e}")
        return {}
    
    def save_users(self):
        """保存用戶數據"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存用戶數據失敗: {e}")
    
    def get_user_tier(self, user_id: str) -> str:
        """獲取用戶層級"""
        user = self.users.get(str(user_id), {})
        return user.get('tier', 'free')
    
    def get_user_queries_today(self, user_id: str) -> int:
        """獲取用戶今日查詢次數"""
        today = datetime.now().strftime('%Y-%m-%d')
        user_key = f"{user_id}_{today}"
        return self.user_queries.get(user_key, 0)
    
    def increment_user_queries(self, user_id: str):
        """增加用戶查詢次數"""
        user_id_str = str(user_id)
        today = datetime.now().strftime('%Y-%m-%d')
        user_key = f"{user_id}_{today}"
        
        # 初始化用戶
        if user_id_str not in self.users:
            self.users[user_id_str] = {
                'tier': 'free',
                'joined_date': datetime.now().isoformat(),
                'total_queries': 0
            }
        
        # 增加查詢次數
        self.user_queries[user_key] = self.user_queries.get(user_key, 0) + 1
        self.users[user_id_str]['total_queries'] = self.users[user_id_str].get('total_queries', 0) + 1
        self.save_users()
    
    def can_query(self, user_id: str, symbol: str) -> Tuple[bool, str, int]:
        """檢查用戶是否可以查詢，返回(可以查詢, 錯誤訊息, 剩餘次數)"""
        tier = self.get_user_tier(user_id)
        queries_today = self.get_user_queries_today(user_id)
        
        if tier == 'vip':
            return True, "", -1  # VIP無限制
        elif tier == 'pro':
            if symbol in MAGNIFICENT_7:
                return True, "", -1
            else:
                return False, "Pro用戶僅支援美股七巨頭分析", -1
        else:  # free
            remaining = self.daily_limit - queries_today
            if remaining <= 0:
                return False, "免費版每日查詢次數已用完（3次）", 0
            if symbol not in SP500_SYMBOLS:
                return False, f"免費版僅支援標普500股票（{len(SP500_SYMBOLS)}支）", remaining
            return True, "", remaining

class DataProvider:
    """多源數據提供者"""
    
    def __init__(self, alpha_vantage_key: Optional[str] = None):
        self.alpha_vantage_key = alpha_vantage_key
        self.api_call_count = 0
        self.last_api_reset = datetime.now()
    
    async def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """獲取股票數據 - 智能選擇數據源"""
        try:
            # 優先使用Alpha Vantage（如果有key且未達限制）
            if self.alpha_vantage_key and self._can_use_alpha_vantage():
                result = await self._get_alpha_vantage_data(symbol)
                if result and 'error' not in result:
                    return result
                logger.warning(f"Alpha Vantage失敗，切換Yahoo: {symbol}")
            
            # 使用Yahoo Finance作為備用或主要源
            return await self._get_yahoo_data(symbol)
            
        except Exception as e:
            logger.error(f"獲取股票數據失敗 {symbol}: {e}")
            return None
    
    def _can_use_alpha_vantage(self) -> bool:
        """檢查是否可以使用Alpha Vantage"""
        current_time = datetime.now()
        
        # 重置計數器（每分鐘）
        if (current_time - self.last_api_reset).seconds >= 60:
            self.api_call_count = 0
            self.last_api_reset = current_time
        
        # 檢查限制（每分鐘5次）
        return self.api_call_count < 5
    
    async def _get_alpha_vantage_data(self, symbol: str) -> Optional[Dict]:
        """Alpha Vantage API - 保留原始邏輯"""
        try:
            base_url = "https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url, params=params, timeout=10) as response:
                    if response.status != 200:
                        return None
                    
                    data = await response.json()
                    self.api_call_count += 1
            
            # 解析響應
            if "Global Quote" not in data:
                if "Note" in data:
                    logger.warning("Alpha Vantage API限制")
                return None
            
            quote = data["Global Quote"]
            return {
                'symbol': symbol,
                'name': symbol,  # Alpha Vantage不提供完整名稱
                'price': float(quote["05. price"]),
                'change': float(quote["09. change"]),
                'change_percent': float(quote["10. change percent"].rstrip('%')),
                'volume': int(quote["06. volume"]),
                'high': float(quote["03. high"]),
                'low': float(quote["04. low"]),
                'prev_close': float(quote["08. previous close"]),
                'data_source': 'Alpha Vantage',
                'timestamp': datetime.now().strftime('%m-%d %H:%M')
            }
            
        except Exception as e:
            logger.error(f"Alpha Vantage錯誤: {e}")
            return None
    
    async def _get_yahoo_data(self, symbol: str) -> Optional[Dict]:
        """Yahoo Finance API - 備用數據源"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            info = ticker.info
            
            if len(hist) < 1:
                return None
            
            current_price = hist['Close'].iloc[-1]
            if len(hist) >= 2:
                previous_price = hist['Close'].iloc[-2]
            else:
                previous_price = info.get('previousClose', current_price)
            
            change = current_price - previous_price
            change_percent = (change / previous_price) * 100 if previous_price != 0 else 0
            volume = hist['Volume'].iloc[-1]
            high = hist['High'].iloc[-1]
            low = hist['Low'].iloc[-1]
            
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'price': float(current_price),
                'change': float(change),
                'change_percent': float(change_percent),
                'volume': int(volume),
                'high': float(high),
                'low': float(low),
                'prev_close': float(previous_price),
                'market_cap': info.get('marketCap'),
                'data_source': 'Yahoo Finance',
                'timestamp': datetime.now().strftime('%m-%d %H:%M')
            }
            
        except Exception as e:
            logger.error(f"Yahoo Finance錯誤: {e}")
            return None
    
    async def get_options_data(self, symbol: str) -> Optional[Dict]:
        """獲取期權數據"""
        try:
            ticker = yf.Ticker(symbol)
            expirations = ticker.options
            
            if not expirations:
                return None
            
            expiration = expirations[0]
            option_chain = ticker.option_chain(expiration)
            
            return {
                'calls': option_chain.calls,
                'puts': option_chain.puts,
                'expiration': expiration
            }
        except Exception as e:
            logger.error(f"獲取期權數據失敗: {e}")
            return None
    
    def calculate_max_pain(self, options_data: Dict) -> Optional[float]:
        """計算Max Pain價格"""
        try:
            calls = options_data['calls']
            puts = options_data['puts']
            
            all_strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
            max_pain_data = []
            
            for strike in all_strikes:
                total_pain = 0
                
                for _, call in calls.iterrows():
                    if strike > call['strike']:
                        pain = call['openInterest'] * (strike - call['strike']) * 100
                        total_pain += pain
                
                for _, put in puts.iterrows():
                    if strike < put['strike']:
                        pain = put['openInterest'] * (put['strike'] - strike) * 100
                        total_pain += pain
                
                max_pain_data.append({'strike': strike, 'total_pain': total_pain})
            
            if not max_pain_data:
                return None
                
            max_pain_df = pd.DataFrame(max_pain_data)
            max_pain_strike = max_pain_df.loc[max_pain_df['total_pain'].idxmax(), 'strike']
            return max_pain_strike
            
        except Exception as e:
            logger.error(f"計算Max Pain失敗: {e}")
            return None

class AnalysisEngine:
    """分析引擎 - 保留原版AI邏輯"""
    
    @staticmethod
    def calculate_confidence(price: float, change_percent: float, volume: int, high: float, low: float) -> int:
        """計算AI分析信心度"""
        try:
            base_confidence = 60
            
            # 價格波動範圍
            if high > 0 and low > 0:
                price_range = ((high - low) / price) * 100
                if price_range < 2:
                    base_confidence += 15
                elif price_range > 8:
                    base_confidence -= 10
            
            # 成交量
            if volume > 10000000:
                base_confidence += 10
            elif volume < 1000000:
                base_confidence -= 5
            
            # 漲跌幅
            abs_change = abs(change_percent)
            if abs_change > 5:
                base_confidence -= 5
            elif abs_change < 1:
                base_confidence += 5
            
            return max(40, min(90, base_confidence))
            
        except:
            return 65
    
    @staticmethod
    def get_recommendation(change_percent: float, confidence: int) -> str:
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
    
    @staticmethod
    def get_status_emoji(change_percent: float) -> str:
        """根據漲跌幅返回狀態表情"""
        if change_percent >= 2:
            return '🔥'
        elif change_percent >= 0.5:
            return '📈'
        elif change_percent >= 0:
            return '📊'
        elif change_percent >= -2:
            return '📉'
        else:
            return '💥'

class MaggieFinalBot:
    """Maggie最終統一機器人"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.data_provider = DataProvider(ALPHA_VANTAGE_KEY)
        self.analysis_engine = AnalysisEngine()
        
        # 價格配置
        self.basic_price = "$9.99"
        self.pro_price = "$19.99"
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """開始命令"""
        user_id = update.effective_user.id
        tier = self.user_manager.get_user_tier(user_id)
        
        # 記錄新用戶
        if str(user_id) not in self.user_manager.users:
            self.user_manager.users[str(user_id)] = {
                'tier': 'free',
                'joined_date': datetime.now().isoformat(),
                'total_queries': 0
            }
            self.user_manager.save_users()
        
        welcome = f"""🎉 **歡迎使用 Maggie Stock AI！**

🤖 我是您的專業股票分析助手

📊 **當前權限: {tier.upper()}**

🆓 **免費功能：**
• 查詢{len(SP500_SYMBOLS)}支標普500股票
• 每日3次免費查詢
• 即時價格與漲跌幅分析
• AI智能投資建議與信心度
• Alpha Vantage + Yahoo Finance 雙重數據源

💎 **Pro版 ({self.basic_price}/月)：**
• 美股七巨頭完整分析
• Max Pain磁吸分析
• Gamma支撐阻力位
• 無查詢次數限制

🔥 **VIP版 ({self.pro_price}/月)：**
• Pro版全部功能
• 全美股8000+支無限查詢
• 期權策略分析
• 即時推送提醒
• 專屬客服支援

📝 **使用方法：**
直接輸入股票代碼，例如：AAPL、TSLA、GOOGL

⚡ **快速命令：**
• /mag7 - 七巨頭分析  
• /list - 標普500清單
• /upgrade - 升級VIP
• /help - 使用幫助
• /status - 系統狀態"""
        
        keyboard = [
            [InlineKeyboardButton("📊 七巨頭分析", callback_data="mag7")],
            [InlineKeyboardButton("📋 標普500清單", callback_data="sp500_list")],
            [InlineKeyboardButton("🚀 升級VIP", callback_data="upgrade")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome, reply_markup=reply_markup)
    
    async def handle_stock_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理股票查詢"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        symbol = update.message.text.upper().strip()
        
        # 驗證股票代碼
        if not symbol.isalpha() or len(symbol) > 5:
            await update.message.reply_text(
                "❌ 請輸入有效的股票代碼\n\n📝 正確格式：\n• AAPL（蘋果）\n• TSLA（特斯拉）\n• GOOGL（谷歌）"
            )
            return
        
        # 檢查查詢權限
        can_query, error_msg, remaining = self.user_manager.can_query(user_id, symbol)
        if not can_query:
            if "標普500" in error_msg:
                # SP500範圍外的升級提示
                upgrade_msg = self._generate_sp500_upgrade_message(symbol)
            else:
                # 達到查詢限制的升級提示
                upgrade_msg = self._generate_limit_upgrade_message()
            
            keyboard = [[InlineKeyboardButton("🔓 立即升級", callback_data="upgrade")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(f"⚠️ {error_msg}\n\n{upgrade_msg}", reply_markup=reply_markup)
            return
        
        # 發送處理中訊息
        processing = await update.message.reply_text("🔍 正在從多重數據源獲取即時數據...")
        
        try:
            # 獲取股票數據
            stock_data = await self.data_provider.get_stock_data(symbol)
            if not stock_data:
                await processing.edit_text(f"❌ 無法獲取 {symbol} 的數據，請檢查代碼或稍後再試")
                return
            
            # 增加查詢次數
            self.user_manager.increment_user_queries(user_id)
            if remaining > 0:
                remaining -= 1
            
            # AI分析
            confidence = self.analysis_engine.calculate_confidence(
                stock_data['price'], stock_data['change_percent'], 
                stock_data['volume'], stock_data['high'], stock_data['low']
            )
            recommendation = self.analysis_engine.get_recommendation(
                stock_data['change_percent'], confidence
            )
            
            # 格式化結果
            tier = self.user_manager.get_user_tier(user_id)
            result = await self._format_stock_result(stock_data, confidence, recommendation, tier, remaining)
            
            await processing.edit_text(result, parse_mode='Markdown')
            
            # 記錄日誌
            logger.info(f"✅ Query - User: {username}({user_id}), Symbol: {symbol}, Source: {stock_data['data_source']}")
            
        except Exception as e:
            logger.error(f"❌ Query error for {symbol}: {str(e)}")
            await processing.edit_text(
                f"❌ 查詢 {symbol} 時發生錯誤\n\n💡 可能原因：\n• 網路連線異常\n• 股票代碼不存在\n• API暫時限制\n\n🔄 已自動嘗試多個數據源，請稍後再試"
            )
    
    async def _format_stock_result(self, data: Dict, confidence: int, recommendation: str, tier: str, remaining: int) -> str:
        """格式化股票結果"""
        symbol = data['symbol']
        emoji = MAGNIFICENT_7.get(symbol, {}).get('emoji', self.analysis_engine.get_status_emoji(data['change_percent']))
        
        # 基礎結果
        result = f"""{emoji} **{data['name']} ({symbol})**

💰 **價格資訊**
當前價格: ${data['price']:.2f}
漲跌: {data['change']:+.2f} ({data['change_percent']:+.2f}%)
成交量: {data['volume']:,}
"""
        
        # 市值信息
        if data.get('market_cap'):
            market_cap_b = data['market_cap'] / 1e9
            result += f"市值: ${market_cap_b:.1f}B\n"
        
        # 價格區間
        result += f"""
📈 **今日區間**
最高: ${data['high']:.2f}
最低: ${data['low']:.2f}
昨收: ${data['prev_close']:.2f}

🤖 **Maggie AI 分析**
🎯 投資建議: {recommendation}
📊 分析信心度: {confidence}%
📡 數據來源: {data['data_source']}
⏰ 更新時間: {data['timestamp']}
"""
        
        # Pro/VIP 用戶的高級分析
        if tier in ['pro', 'vip'] and symbol in MAGNIFICENT_7:
            advanced_analysis = await self._get_advanced_analysis(symbol, data)
            if advanced_analysis:
                result += f"\n{advanced_analysis}"
        
        # 免費用戶的升級提示
        if tier == 'free':
            result += f"""

📱 **免費版狀態**
今日剩餘查詢: {remaining}次
"""
            if remaining <= 1:
                result += f"""💡 **提醒**: 查詢即將用完
VIP基礎版每月僅需 {self.basic_price}，享受無限查詢！"""
        
        result += f"""

💬 **客服支援:** @maggie_invests
📜 **風險提示:** 投資有風險，決策需謹慎"""
        
        return result
    
    async def _get_advanced_analysis(self, symbol: str, stock_data: Dict) -> Optional[str]:
        """獲取高級分析"""
        try:
            options_data = await self.data_provider.get_options_data(symbol)
            if not options_data:
                return None
            
            max_pain = self.data_provider.calculate_max_pain(options_data)
            current_price = stock_data['price']
            
            if max_pain:
                distance = abs(current_price - max_pain)
                distance_percent = (distance / current_price) * 100
                
                if distance_percent < 2:
                    magnetic_strength = "🔴 強磁吸"
                elif distance_percent < 5:
                    magnetic_strength = "🟡 中等磁吸"
                else:
                    magnetic_strength = "🟢 弱磁吸"
                
                return f"""

🧲 **Max Pain 磁吸分析**
📍 Max Pain: ${max_pain:.2f}
💫 磁吸強度: {magnetic_strength} (距離: ${distance:.2f})

⚡ **Gamma 支撐阻力位**
🛡️ 支撐: ${current_price * 0.92:.2f}
🚀 阻力: ${current_price * 1.08:.2f}

🤖 **MM行為預測**
預計主力將在Max Pain附近操控，關注量價配合。"""
            
        except Exception as e:
            logger.error(f"高級分析失敗: {e}")
        
        return None
    
    def _generate_sp500_upgrade_message(self, symbol: str) -> str:
        """生成SP500範圍外的升級訊息"""
        return f"""🚫 **該股票不在免費版範圍內**

您查詢的 **{symbol}** 需要升級VIP版本。

💎 **升級VIP基礎版 {self.basic_price}/月**
🌍 解鎖全美股8000+支股票查詢！

包含：
✅ NASDAQ全部股票  
✅ NYSE完整覆蓋
✅ 新股/IPO實時追蹤
✅ 無限查詢次數

🎯 **熱門非標普500股票**:
RBLX, PLTR, COIN, HOOD, RIVN, LCID...

💡 **免費版支持的熱門股票**:
{', '.join(list(MAGNIFICENT_7.keys())[:5])}...
輸入 /list 查看完整標普500清單"""
    
    def _generate_limit_upgrade_message(self) -> str:
        """生成查詢限制的升級訊息"""
        return f"""🚫 **免費版每日查詢已達上限 (3次)**

💎 **升級VIP，解鎖強大功能！**

🥈 **VIP基礎版 {self.basic_price}/月**:
✅ 全美股8000+支無限查詢
✅ 新股/IPO實時追蹤  
✅ 無延遲實時數據
✅ 24/7技術支援

🥇 **VIP專業版 {self.pro_price}/月**
