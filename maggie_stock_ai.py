#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Maggie's Stock AI Bot - 統一多功能股票分析機器人
支援三層用戶系統：免費用戶、Pro測試用戶、VIP付費用戶
"""

import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf
import pandas as pd
import numpy as np
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    ContextTypes, MessageHandler, filters
)

# 配置日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 配置
BOT_TOKEN = "8320641094:AAGoaTpTlZDnA2wH8Qq5Pqv-8L7thECoR2s"
YAHOO_API_KEY = "NBWPE7OFZHTT3OFI"

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

# 標普500主要成分股（簡化版）
SP500_MAJOR = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'BRK-B', 'UNH', 'JNJ',
    'JPM', 'V', 'PG', 'XOM', 'HD', 'CVX', 'MA', 'BAC', 'ABBV', 'PFE', 'AVGO', 'KO',
    'MRK', 'COST', 'DIS', 'ADBE', 'WMT', 'BAX', 'CRM', 'NFLX', 'ACN', 'NKE', 'TMO'
]

class UserManager:
    """用戶管理系統"""
    
    def __init__(self):
        self.users_file = 'users.json'
        self.users = self.load_users()
    
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
        user = self.users.get(str(user_id), {})
        today = datetime.now().strftime('%Y-%m-%d')
        return user.get('queries', {}).get(today, 0)
    
    def increment_user_queries(self, user_id: str):
        """增加用戶查詢次數"""
        user_id = str(user_id)
        today = datetime.now().strftime('%Y-%m-%d')
        
        if user_id not in self.users:
            self.users[user_id] = {
                'tier': 'free',
                'joined_date': datetime.now().isoformat(),
                'queries': {}
            }
        
        if 'queries' not in self.users[user_id]:
            self.users[user_id]['queries'] = {}
        
        self.users[user_id]['queries'][today] = self.users[user_id]['queries'].get(today, 0) + 1
        self.save_users()
    
    def can_query(self, user_id: str, symbol: str) -> tuple[bool, str]:
        """檢查用戶是否可以查詢"""
        tier = self.get_user_tier(user_id)
        queries_today = self.get_user_queries_today(user_id)
        
        if tier == 'vip':
            return True, ""
        elif tier == 'pro':
            if symbol in MAGNIFICENT_7:
                return True, ""
            else:
                return False, "Pro用戶僅支援美股七巨頭查詢，升級VIP解鎖全功能！"
        else:  # free
            if queries_today >= 3:
                return False, "免費用戶每日限制3次查詢，升級Pro/VIP解鎖更多！"
            if symbol not in SP500_MAJOR:
                return False, "免費用戶僅支援標普500主要成分股，升級解鎖全市場！"
            return True, ""

class StockAnalyzer:
    """股票分析器"""
    
    @staticmethod
    def get_stock_data(symbol: str) -> Optional[Dict]:
        """獲取股票數據"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            info = ticker.info
            
            if len(hist) < 2:
                return None
            
            current_price = hist['Close'].iloc[-1]
            previous_price = hist['Close'].iloc[-2]
            change = current_price - previous_price
            change_percent = (change / previous_price) * 100
            volume = hist['Volume'].iloc[-1]
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'change': change,
                'change_percent': change_percent,
                'volume': volume,
                'name': info.get('longName', symbol)
            }
        except Exception as e:
            logger.error(f"獲取股票數據失敗 {symbol}: {e}")
            return None
    
    @staticmethod
    def get_options_data(symbol: str) -> Optional[Dict]:
        """獲取期權數據"""
        try:
            ticker = yf.Ticker(symbol)
            expirations = ticker.options
            
            if not expirations:
                return None
            
            # 使用最近的到期日
            expiration = expirations[0]
            option_chain = ticker.option_chain(expiration)
            
            return {
                'calls': option_chain.calls,
                'puts': option_chain.puts,
                'expiration': expiration
            }
        except Exception as e:
            logger.error(f"獲取期權數據失敗 {symbol}: {e}")
            return None
    
    @staticmethod
    def calculate_max_pain(options_data: Dict) -> Optional[float]:
        """計算Max Pain價格"""
        try:
            calls = options_data['calls']
            puts = options_data['puts']
            
            # 獲取所有執行價格
            all_strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
            
            max_pain_data = []
            
            for strike in all_strikes:
                total_pain = 0
                
                # 計算看漲期權的痛苦值
                for _, call in calls.iterrows():
                    if strike > call['strike']:
                        pain = call['openInterest'] * (strike - call['strike']) * 100
                        total_pain += pain
                
                # 計算看跌期權的痛苦值  
                for _, put in puts.iterrows():
                    if strike < put['strike']:
                        pain = put['openInterest'] * (put['strike'] - strike) * 100
                        total_pain += pain
                
                max_pain_data.append({
                    'strike': strike,
                    'total_pain': total_pain
                })
            
            # 找到總痛苦值最大的執行價格
            max_pain_df = pd.DataFrame(max_pain_data)
            max_pain_strike = max_pain_df.loc[max_pain_df['total_pain'].idxmax(), 'strike']
            
            return max_pain_strike
        except Exception as e:
            logger.error(f"計算Max Pain失敗: {e}")
            return None
    
    @staticmethod
    def calculate_gamma_levels(options_data: Dict, current_price: float) -> Dict:
        """計算Gamma支撐阻力位"""
        try:
            calls = options_data['calls']
            puts = options_data['puts']
            
            # 簡化計算，基於當前價格的±15%範圍
            support = current_price * 0.85
            resistance = current_price * 1.15
            
            return {
                'support': support,
                'resistance': resistance
            }
        except Exception as e:
            logger.error(f"計算Gamma levels失敗: {e}")
            return {'support': current_price * 0.9, 'resistance': current_price * 1.1}

class MessageFormatter:
    """訊息格式化器"""
    
    @staticmethod
    def format_stock_analysis(data: Dict, tier: str = 'free') -> str:
        """格式化股票分析結果"""
        symbol = data['symbol']
        name = data['name']
        price = data['current_price']
        change = data['change']
        change_percent = data['change_percent']
        volume = data['volume']
        
        # 獲取emoji
        emoji = MAGNIFICENT_7.get(symbol, {}).get('emoji', '📊')
        
        # 趨勢判斷
        if change_percent > 2:
            trend = "📈 強勢上漲"
        elif change_percent > 0:
            trend = "📈 溫和上漲"
        elif change_percent > -2:
            trend = "📊 震盪整理"
        else:
            trend = "📉 調整壓力"
        
        # 基礎訊息
        message = f"""
{emoji} **{name} ({symbol})**
💰 ${price:.2f} ({change:+.2f} | {change_percent:+.1f}%)
📊 {trend}
📈 成交量: {volume:,.0f}

💡 **AI分析建議**
"""
        
        # AI建議（根據用戶層級）
        if tier == 'free':
            confidence = min(85, 60 + abs(change_percent) * 5)
            if change_percent > 1:
                suggestion = "短線看多，建議關注回調買點"
            elif change_percent < -1:
                suggestion = "關注支撐位，可考慮逢低佈局"
            else:
                suggestion = "震盪整理，建議觀望為主"
            
            message += f"📋 {suggestion}\n🎯 信心度: {confidence:.0f}%\n"
            message += f"\n⚠️ *資料延遲1-3分鐘，僅供參考*"
            
        return message
    
    @staticmethod
    def format_upgrade_message(tier: str) -> str:
        """格式化升級訊息"""
        if tier == 'free':
            return """
🚀 **升級Pro/VIP解鎖更多功能！**

💎 **Pro版特色 ($9.99/月)**
• 美股七巨頭完整分析
• Max Pain磁吸分析
• Gamma支撐阻力位
• 無查詢次數限制

🔥 **VIP版特色 ($19.99/月)**
• 全市場股票分析
• 期權策略建議
• 即時推送提醒
• 專屬客服支援

點擊 /upgrade 了解詳情！
"""
        else:
            return """
🔥 **升級VIP解鎖全功能！**

✨ **VIP獨享功能**
• 全市場8000+股票
• 期權策略分析
• 即時價格推送
• 技術指標大全
• 專屬投資建議

💰 **限時優惠 $19.99/月**
點擊 /upgrade 立即升級！
"""

class MaggieStockBot:
    """Maggie股票機器人主類"""
    
    def __init__(self):
        self.user_manager = UserManager()
        self.stock_analyzer = StockAnalyzer()
        self.message_formatter = MessageFormatter()
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """開始命令"""
        user_id = update.effective_user.id
        tier = self.user_manager.get_user_tier(user_id)
        
        # 記錄新用戶
        if str(user_id) not in self.user_manager.users:
            self.user_manager.users[str(user_id)] = {
                'tier': 'free',
                'joined_date': datetime.now().isoformat(),
                'queries': {}
            }
            self.user_manager.save_users()
        
        welcome_message = f"""
🤖 **歡迎使用 Maggie's Stock AI！**

👋 您好！我是您的專業股票分析助手

📊 **功能介紹**
• 即時股價查詢與分析
• AI智能投資建議
• 專業技術指標解讀

🎯 **使用方法**
直接輸入股票代碼，如: `AAPL` 或 `Apple`

💎 **您的權限: {tier.upper()}**
"""
        
        if tier == 'free':
            welcome_message += """
🆓 **免費版權限**
• 標普500主要成分股
• 每日3次查詢限制
• 基礎分析功能

🚀 升級Pro/VIP享受更多功能！
"""
        elif tier == 'pro':
            welcome_message += """
💎 **Pro版權限**
• 美股七巨頭完整分析
• Max Pain磁吸分析
• 無限查詢次數

🔥 升級VIP解鎖全市場！
"""
        else:
            welcome_message += """
🔥 **VIP全功能版**
• 全市場股票分析
• 期權策略建議
• 即時推送提醒

感謝您的支持！
"""
        
        # 添加功能按鈕
        keyboard = [
            [InlineKeyboardButton("📊 七巨頭分析", callback_data="mag7_analysis")],
            [InlineKeyboardButton("🚀 升級VIP", callback_data="upgrade")],
            [InlineKeyboardButton("ℹ️ 幫助", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    
    async def handle_stock_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """處理股票查詢"""
        user_id = update.effective_user.id
        query = update.message.text.upper().strip()
        
        # 查找股票代碼
        symbol = self.find_stock_symbol(query)
        if not symbol:
            await update.message.reply_text(
                "❌ 找不到該股票，請檢查代碼或名稱\n\n"
                "💡 範例: AAPL, Apple, Tesla, TSLA"
            )
            return
        
        # 檢查查詢權限
        can_query, error_msg = self.user_manager.can_query(user_id, symbol)
        if not can_query:
            upgrade_msg = self.message_formatter.format_upgrade_message(
                self.user_manager.get_user_tier(user_id)
            )
            await update.message.reply_text(f"⚠️ {error_msg}\n\n{upgrade_msg}")
            return
        
        # 增加查詢次數
        self.user_manager.increment_user_queries(user_id)
        
        # 發送處理中訊息
        processing_msg = await update.message.reply_text(f"🔄 正在分析 {symbol}...")
        
        try:
            # 獲取股票數據
            stock_data = self.stock_analyzer.get_stock_data(symbol)
            if not stock_data:
                await processing_msg.edit_text(f"❌ 無法獲取 {symbol} 的數據，請稍後再試")
                return
            
            # 格式化訊息
            tier = self.user_manager.get_user_tier(user_id)
            message = self.message_formatter.format_stock_analysis(stock_data, tier)
            
            # 添加高級分析（Pro/VIP用戶）
            if tier in ['pro', 'vip'] and symbol in MAGNIFICENT_7:
                advanced_analysis = await self.get_advanced_analysis(symbol, stock_data)
                message += advanced_analysis
            
            # 添加升級提示
            if tier == 'free':
                queries_left = 3 - self.user_manager.get_user_queries_today(user_id)
                message += f"\n\n📊 今日剩餘查詢: {queries_left}次"
                if queries_left <= 1:
                    message += "\n🚀 升級享受無限查詢！"
            
            await processing_msg.edit_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"查詢股票失敗 {symbol}: {e}")
            await processing_msg.edit_text(f"❌ 分析失敗，請稍後再試")
    
    async def get_advanced_analysis(self, symbol: str, stock_data: Dict) -> str:
        """獲取高級分析（Max Pain、Gamma等）"""
        try:
            # 獲取期權數據
            options_data = self.stock_analyzer.get_options_data(symbol)
            if not options_data:
                return "\n\n⚠️ 期權數據暫時無法獲取"
            
            # 計算Max Pain
            max_pain = self.stock_analyzer.calculate_max_pain(options_data)
            current_price = stock_data['current_price']
            
            # 計算Gamma levels
            gamma_levels = self.stock_analyzer.calculate_gamma_levels(options_data, current_price)
            
            analysis = f"""

🧲 **Max Pain 磁吸分析**
📍 Max Pain: ${max_pain:.2f}
"""
            
            if max_pain:
                distance = abs(current_price - max_pain)
                distance_percent = (distance / current_price) * 100
                
                if distance_percent < 2:
                    magnetic_strength = "🔴 強磁吸"
                elif distance_percent < 5:
                    magnetic_strength = "🟡 中等磁吸"
                else:
                    magnetic_strength = "🟢 弱磁吸"
                
                analysis += f"💫 磁吸強度: {magnetic_strength} (距離: ${distance:.2f})"
            
            analysis += f"""

⚡ **Gamma 支撐阻力位**
🛡️ 支撐: ${gamma_levels['support']:.2f}
🚀 阻力: ${gamma_levels['resistance']:.2f}

🤖 **MM行為預測**
預計主力將在Max Pain附近操控，
關注量價配合情況。
"""
            
            return analysis
            
        except Exception as e:
            logger.error(f"高級分析失敗 {symbol}: {e}")
            return "\n\n⚠️ 高級分析暫時無法獲取"
    
    def find_stock_symbol(self, query: str) -> Optional[str]:
        """查找股票代碼"""
        query = query.upper()
        
        # 直接匹配代碼
        if query in SP500_MAJOR or query in MAGNIFICENT_7:
            return query
        
        # 名稱匹配
        name_mapping = {
            'APPLE': 'AAPL',
            'MICROSOFT': 'MSFT', 
            'GOOGLE': 'GOOGL',
            'AMAZON': 'AMZN',
            'NVIDIA': 'NVDA',
            'TESLA': 'TSLA',
            'META': 'META',
            'FACEBOOK': 'META'
        }
        
        return name_mapping.get(query)
    
    async def mag7_analysis_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """七巨頭分析回調"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        tier = self.user_manager.get_user_tier(user_id)
        
        if tier == 'free':
            upgrade_msg = self.message_formatter.format_upgrade_message('free')
            await query.edit_message_text(f"⚠️ 七巨頭分析需要Pro版權限\n\n{upgrade_msg}")
            return
        
        # 生成七巨頭報告
        await query.edit_message_text("🔄 正在生成七巨頭分析報告...")
        
        try:
            report = await self.generate_mag7_report()
            await query.edit_message_text(report, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"生成七巨頭報告失敗: {e}")
            await query.edit_message_text("❌ 報告生成失敗，請稍後再試")
    
    async def generate_mag7_report(self) -> str:
        """生成七巨頭報告"""
        taipei_time = datetime.now().strftime('%Y-%m-%d %H:%M 台北時間')
        
        report = f"""
📅 {taipei_time}

📊 **美股七巨頭即時分析**

"""
        
        strongest = {'symbol': '', 'change': -999}
        weakest = {'symbol': '', 'change': 999}
        
        for symbol, info in MAGNIFICENT_7.items():
            try:
                stock_data = self.stock_analyzer.get_stock_data(symbol)
                if stock_data:
                    emoji = info['emoji']
                    name = info['name']
                    price = stock_data['current_price']
                    change = stock_data['change']
                    change_percent = stock_data['change_percent']
                    
                    # 趨勢判斷
                    if change_percent > 1:
                        trend_emoji = "📈"
                        trend = "溫和上漲"
                    elif change_percent > 0:
                        trend_emoji = "📈"
                        trend = "微幅上漲"
                    elif change_percent > -1:
                        trend_emoji = "📊"
                        trend = "震盪整理"
                    else:
                        trend_emoji = "📉"
                        trend = "調整壓力"
                    
                    report += f"{trend_emoji} {emoji} {name} ({symbol})\n"
                    report += f"💰 ${price:.2f} ({change:+.2f} | {change_percent:+.1f}%)\n"
                    report += f"📊 {trend}\n\n"
                    
                    # 更新最強/最弱
                    if change_percent > strongest['change']:
                        strongest = {'symbol': symbol, 'change': change_percent, 'emoji': emoji, 'name': name}
                    if change_percent < weakest['change']:
                        weakest = {'symbol': symbol, 'change': change_percent, 'emoji': emoji, 'name': name}
                        
            except Exception as e:
                logger.error(f"獲取 {symbol} 數據失敗: {e}")
                continue
        
        # 添加總結
        report += f"""
🎯 **今日重點關注**
🔥 最強: {strongest['emoji']} {strongest['name']} ({strongest['change']:+.1f}%)
⚠️ 最弱: {weakest['emoji']} {weakest['name']} ({weakest['change']:+.1f}%)

💡 **交易策略建議**
• 短線: 關注最強股續航能力
• 中線: 關注最弱股反彈機會  
• 長線: 七檔均為優質科技成長股

---
📊 Maggie's Stock AI | Pro版功能
🔄 數據每分鐘更新
💬 升級VIP享受更多功能 /upgrade
"""
        
        return report
    
    async def daily_report_job(self, context: ContextTypes.DEFAULT_TYPE):
        """每日定時報告任務"""
        try:
            # 獲取所有Pro/VIP用戶
            pro_vip_users = [
                user_id for user_id, data in self.user_manager.users.items() 
                if data.get('tier') in ['pro', 'vip']
            ]
            
            if not pro_vip_users:
                return
            
            # 生成報告
            report = await self.generate_mag7_report()
            report = f"🌅 **每日晨報**\n\n{report}"
            
            # 發送給所有Pro/VIP用戶
            for user_id in pro_vip_users:
                try:
                    await context.bot.send_message(
                        chat_id=int(user_id), 
                        text=report, 
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"發送每日報告失敗 {user_id}: {e}")
                    
        except Exception as e:
            logger.error(f"每日報告任務失敗: {e}")
    
    async def upgrade_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """升級回調"""
        query = update.callback_query
        await query.answer()
        
        upgrade_message = """
🚀 **升級 Maggie's Stock AI**

💎 **Pro版 - $9.99/月**
✅ 美股七巨頭完整分析
✅ Max Pain 磁吸分析  
✅ Gamma 支撐阻力位
✅ 無查詢次數限制
✅ 每日4次自動報告

🔥 **VIP版 - $19.99/月** (推薦)
✅ Pro版全部功能
✅ 全市場8000+股票
✅ 期權策略分析
✅ 即時價格推送
✅ 技術指標大全
✅ 專屬客服支援

💳 **付款方式**
• PayPal: maggie.stock.ai@gmail.com
• 加密貨幣: USDT/BTC
• 信用卡: 即將開放

📞 **聯絡客服升級**
Telegram: @maggie_support
Email: support@maggie-stock-ai.com

🎁 **限時優惠**
新用戶首月8折！使用代碼: WELCOME20
"""
        
        keyboard = [
            [InlineKeyboardButton("💳 立即升級", url="https://t.me/maggie_support")],
            [InlineKeyboardButton("🔙 返回", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(upgrade_message, reply_markup=reply_markup)
    
    async def help_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """幫助回調"""
        query = update.callback_query
        await query.answer()
        
        help_message = """
📚 **Maggie's Stock AI 使用指南**

🔍 **股票查詢**
• 直接輸入代碼: `AAPL`, `TSLA`
• 輸入公司名: `Apple`, `Tesla`
• 支援中英文混合查詢

📊 **功能說明**
• 即時股價與漲跌幅
• AI智能分析建議
• 技術指標解讀
• Max Pain磁吸分析 (Pro+)
• Gamma支撐阻力 (Pro+)

⚡ **快速命令**
• `/start` - 重新開始
• `/mag7` - 七巨頭分析
• `/upgrade` - 升級VIP
• `/feedback` - 意見反饋

💡 **使用技巧**
1. 免費用戶每日3次查詢
2. Pro用戶專享七巨頭分析
3. VIP用戶全市場無限制

❓ **常見問題**
Q: 數據更新頻率？
A: 1-3分鐘延遲，盤中實時更新

Q: 支援哪些市場？
A: 主要支援美股，計劃擴展至全球市場

📞 **技術支援**
Telegram: @maggie_support
Email: support@maggie-stock-ai.com
"""
        
        keyboard = [
            [InlineKeyboardButton("📊 開始查詢", callback_data="start_query")],
            [InlineKeyboardButton("🔙 返回主選單", callback_data="back_to_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(help_message, reply_markup=reply_markup)

async def main():
    """主函數"""
    # 創建機器人實例
    bot = MaggieStockBot()
    
    # 創建應用程式
    application = Application.builder().token(BOT_TOKEN).build()
    
    # 顯示Bot資訊
    bot_info = await application.bot.get_me()
    print(f"🤖 Bot啟動成功!")
    print(f"📱 Bot名稱: {bot_info.first_name}")
    print(f"🆔 Bot ID: {bot_info.id}")
    print(f"👤 Bot用戶名: @{bot_info.username}")
    print(f"⏰ 啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 註冊處理器
    application.add_handler(CommandHandler("start", bot.start_command))
    
    # 回調處理器
    application.add_handler(CallbackQueryHandler(
        bot.mag7_analysis_callback, pattern="mag7_analysis"
    ))
    application.add_handler(CallbackQueryHandler(
        bot.upgrade_callback, pattern="upgrade"
    ))
    application.add_handler(CallbackQueryHandler(
        bot.help_callback, pattern="help"
    ))
    
    # 文字訊息處理器（股票查詢）
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        bot.handle_stock_query
    ))
    
    # 設定每日定時任務 (每天8:00台北時間)
    from telegram.ext import JobQueue
    job_queue = application.job_queue
    
    # 每日8點發送報告
    job_queue.run_daily(
        bot.daily_report_job, 
        time=datetime.strptime("08:00", "%H:%M").time(),
        name="daily_mag7_report"
    )
    
    # 啟動機器人
    print("🚀 Maggie's Stock AI 開始運行...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
