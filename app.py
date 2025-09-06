import os
import logging
import requests
from flask import Flask, request
from datetime import datetime, timedelta
import json
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("請設置 TELEGRAM_BOT_TOKEN 環境變數")

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"
app = Flask(__name__)

def send_message(chat_id, text):
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"發送訊息失敗: {str(e)}")
        return None

def get_stock_data_yahoo(symbol):
    """使用 Yahoo Finance API 獲取股票數據"""
    try:
        # 基本股票資訊
        base_url = "https://query1.finance.yahoo.com/v8/finance/chart"
        params = {
            'symbol': symbol,
            'interval': '1d',
            'range': '5d'
        }
        
        response = requests.get(base_url, params=params, timeout=15)
        data = response.json()
        
        if 'chart' not in data or not data['chart']['result']:
            return None
            
        result = data['chart']['result'][0]
        meta = result['meta']
        
        # 歷史價格數據
        quotes = result['indicators']['quote'][0]
        timestamps = result['timestamp']
        
        if not quotes['close']:
            return None
            
        # 計算技術指標
        closes = [price for price in quotes['close'] if price is not None]
        volumes = [vol for vol in quotes['volume'] if vol is not None]
        
        if len(closes) < 2:
            return None
            
        current_price = closes[-1]
        previous_close = meta.get('previousClose', closes[-2] if len(closes) > 1 else current_price)
        
        change = current_price - previous_close
        change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
        
        # 計算技術指標
        sma_5 = sum(closes[-5:]) / min(5, len(closes)) if len(closes) >= 3 else None
        sma_20 = sum(closes[-20:]) / min(20, len(closes)) if len(closes) >= 10 else None
        
        # RSI 計算
        rsi = calculate_rsi(closes) if len(closes) >= 14 else None
        
        # 支撐阻力位
        high_prices = [price for price in quotes['high'] if price is not None]
        low_prices = [price for price in quotes['low'] if price is not None]
        
        resistance = max(high_prices[-5:]) if len(high_prices) >= 5 else None
        support = min(low_prices[-5:]) if len(low_prices) >= 5 else None
        
        return {
            'symbol': symbol.upper(),
            'company_name': meta.get('longName', symbol),
            'current_price': current_price,
            'previous_close': previous_close,
            'change': change,
            'change_percent': change_percent,
            'volume': volumes[-1] if volumes else 0,
            'market_cap': meta.get('marketCap', 0),
            'currency': meta.get('currency', 'USD'),
            'exchange': meta.get('exchangeName', 'Unknown'),
            'sma_5': sma_5,
            'sma_20': sma_20,
            'rsi': rsi,
            'resistance': resistance,
            'support': support,
            'high_52w': meta.get('fiftyTwoWeekHigh'),
            'low_52w': meta.get('fiftyTwoWeekLow'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logger.error(f"Yahoo Finance API 錯誤: {str(e)}")
        return None

def calculate_rsi(prices, period=14):
    """計算 RSI 指標"""
    if len(prices) < period + 1:
        return None
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < period:
        return None
        
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100
        
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)

def get_options_data(symbol):
    """獲取期權數據並計算 Max Pain"""
    try:
        # 先獲取期權到期日
        url = f"https://query1.finance.yahoo.com/v7/finance/options/{symbol}"
        response = requests.get(url, timeout=15)
        data = response.json()
        
        if 'optionChain' not in data or not data['optionChain']['result']:
            return None
            
        options_data = data['optionChain']['result'][0]
        
        if 'expirationDates' not in options_data or not options_data['expirationDates']:
            return None
            
        # 使用最近的到期日
        expiry_timestamp = options_data['expirationDates'][0]
        
        # 獲取該到期日的期權鏈
        url_with_date = f"{url}?date={expiry_timestamp}"
        response = requests.get(url_with_date, timeout=15)
        data = response.json()
        
        if 'optionChain' not in data or not data['optionChain']['result']:
            return None
            
        result = data['optionChain']['result'][0]
        
        calls = result['options'][0].get('calls', [])
        puts = result['options'][0].get('puts', [])
        
        if not calls and not puts:
            return None
            
        # 計算 Max Pain
        max_pain = calculate_max_pain(calls, puts)
        
        # 計算 Put/Call 比率
        total_call_oi = sum([opt.get('openInterest', 0) for opt in calls])
        total_put_oi = sum([opt.get('openInterest', 0) for opt in puts])
        
        pc_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else 0
        
        # 到期日轉換
        expiry_date = datetime.fromtimestamp(expiry_timestamp).strftime('%Y-%m-%d')
        
        return {
            'max_pain': max_pain,
            'put_call_ratio': pc_ratio,
            'total_call_oi': total_call_oi,
            'total_put_oi': total_put_oi,
            'expiry_date': expiry_date,
            'calls_count': len(calls),
            'puts_count': len(puts)
        }
        
    except Exception as e:
        logger.error(f"期權數據獲取錯誤: {str(e)}")
        return None

def calculate_max_pain(calls, puts):
    """計算 Max Pain 價位"""
    try:
        strikes = set()
        
        # 收集所有執行價
        for call in calls:
            if call.get('strike'):
                strikes.add(call['strike'])
        for put in puts:
            if put.get('strike'):
                strikes.add(put['strike'])
        
        if not strikes:
            return None
            
        strikes = sorted(strikes)
        min_pain = float('inf')
        max_pain_strike = None
        
        for strike in strikes:
            pain = 0
            
            # 計算 Call 方的損失
            for call in calls:
                if call.get('strike', 0) < strike:
                    pain += (strike - call['strike']) * call.get('openInterest', 0) * 100
            
            # 計算 Put 方的損失
            for put in puts:
                if put.get('strike', 0) > strike:
                    pain += (put['strike'] - strike) * put.get('openInterest', 0) * 100
            
            if pain < min_pain:
                min_pain = pain
                max_pain_strike = strike
        
        return max_pain_strike
        
    except Exception as e:
        logger.error(f"Max Pain 計算錯誤: {str(e)}")
        return None

def generate_investment_advice(stock_data, options_data=None):
    """生成投資建議"""
    try:
        advice = {
            'trend_analysis': '',
            'technical_signals': [],
            'risk_assessment': '',
            'time_horizon': {
                'short_term': '',
                'long_term': ''
            },
            'portfolio_suggestion': ''
        }
        
        # 趨勢分析
        change_pct = stock_data['change_percent']
        rsi = stock_data.get('rsi')
        
        if change_pct > 2:
            advice['trend_analysis'] = '強勢上漲趨勢，動能強勁'
        elif change_pct > 0.5:
            advice['trend_analysis'] = '溫和上漲，趨勢向好'
        elif change_pct > -0.5:
            advice['trend_analysis'] = '震盪整理，方向不明'
        elif change_pct > -2:
            advice['trend_analysis'] = '下跌調整，存在壓力'
        else:
            advice['trend_analysis'] = '大幅下跌，風險較高'
        
        # 技術訊號
        if rsi:
            if rsi > 70:
                advice['technical_signals'].append('RSI超買訊號')
            elif rsi < 30:
                advice['technical_signals'].append('RSI超賣訊號')
            else:
                advice['technical_signals'].append('RSI處於中性區間')
        
        # 移動平均線分析
        current_price = stock_data['current_price']
        sma_5 = stock_data.get('sma_5')
        sma_20 = stock_data.get('sma_20')
        
        if sma_5 and sma_20:
            if current_price > sma_5 > sma_20:
                advice['technical_signals'].append('多頭排列，趨勢向上')
            elif current_price < sma_5 < sma_20:
                advice['technical_signals'].append('空頭排列，趨勢向下')
        
        # 風險評估
        if options_data and options_data.get('put_call_ratio'):
            pc_ratio = options_data['put_call_ratio']
            if pc_ratio > 1.2:
                advice['risk_assessment'] = '市場情緒偏空，Put/Call比率偏高'
            elif pc_ratio < 0.8:
                advice['risk_assessment'] = '市場情緒偏多，存在過度樂觀'
            else:
                advice['risk_assessment'] = '市場情緒中性，風險適中'
        else:
            advice['risk_assessment'] = '需要更多數據進行風險評估'
        
        # 時間框架建議
        if change_pct > 0 and rsi and rsi < 70:
            advice['time_horizon']['short_term'] = '短期可持續關注上漲動能'
            advice['time_horizon']['long_term'] = '長期投資需觀察基本面支撐'
        elif change_pct < -2:
            advice['time_horizon']['short_term'] = '短期避險，等待反彈訊號'
            advice['time_horizon']['long_term'] = '長期可考慮逢低佈局'
        else:
            advice['time_horizon']['short_term'] = '短期保持觀望'
            advice['time_horizon']['long_term'] = '長期投資需評估公司基本面'
        
        # 投資組合建議
        market_cap = stock_data.get('market_cap', 0)
        if market_cap > 100e9:  # 大型股
            advice['portfolio_suggestion'] = '大型股，適合作為核心持股，建議5-15%配置'
        elif market_cap > 10e9:  # 中型股
            advice['portfolio_suggestion'] = '中型股，成長潛力較大，建議3-8%配置'
        else:  # 小型股
            advice['portfolio_suggestion'] = '小型股，風險較高，建議1-3%配置'
        
        return advice
        
    except Exception as e:
        logger.error(f"投資建議生成錯誤: {str(e)}")
        return None

def format_enhanced_stock_report(stock_data, options_data=None, advice=None):
    """格式化增強版股票報告"""
    if not stock_data:
        return "❌ 無法獲取股票數據，請檢查股票代碼是否正確"
    
    symbol = stock_data['symbol']
    company_name = stock_data['company_name']
    current_price = stock_data['current_price']
    change = stock_data['change']
    change_percent = stock_data['change_percent']
    
    # 判斷漲跌趨勢
    if change > 0:
        trend_emoji = "📈"
        trend_text = "上漲"
    elif change < 0:
        trend_emoji = "📉"
        trend_text = "下跌"
    else:
        trend_emoji = "➡️"
        trend_text = "持平"
    
    # 格式化市值
    market_cap = stock_data.get('market_cap', 0)
    if market_cap > 1e12:
        market_cap_text = f"{market_cap/1e12:.2f}T"
    elif market_cap > 1e9:
        market_cap_text = f"{market_cap/1e9:.2f}B"
    elif market_cap > 1e6:
        market_cap_text = f"{market_cap/1e6:.2f}M"
    else:
        market_cap_text = "N/A"
    
    # 基本資訊部分
    report = f"""📊 <b>{symbol} 深度股票分析</b>

🏢 <b>公司:</b> {company_name}
💰 <b>當前價格:</b> ${current_price:.2f}
{trend_emoji} <b>變動:</b> {change:+.2f} ({change_percent:+.2f}%) {trend_text}
📦 <b>成交量:</b> {stock_data.get('volume', 0):,}
📈 <b>市值:</b> ${market_cap_text}
📍 <b>交易所:</b> {stock_data.get('exchange', 'Unknown')}

📊 <b>技術指標分析:</b>"""
    
    # 技術指標
    if stock_data.get('rsi'):
        rsi_status = "超買" if stock_data['rsi'] > 70 else "超賣" if stock_data['rsi'] < 30 else "中性"
        report += f"\n🔍 <b>RSI (14日):</b> {stock_data['rsi']:.1f} ({rsi_status})"
    
    if stock_data.get('sma_5'):
        report += f"\n📊 <b>5日均線:</b> ${stock_data['sma_5']:.2f}"
    
    if stock_data.get('sma_20'):
        report += f"\n📊 <b>20日均線:</b> ${stock_data['sma_20']:.2f}"
    
    # 支撐阻力位
    if stock_data.get('support') and stock_data.get('resistance'):
        report += f"\n\n🎯 <b>關鍵價位:</b>"
        report += f"\n🛡️ <b>支撐位:</b> ${stock_data['support']:.2f}"
        report += f"\n🚧 <b>阻力位:</b> ${stock_data['resistance']:.2f}"
    
    # 52週高低點
    if stock_data.get('high_52w') and stock_data.get('low_52w'):
        report += f"\n📊 <b>52週高點:</b> ${stock_data['high_52w']:.2f}"
        report += f"\n📊 <b>52週低點:</b> ${stock_data['low_52w']:.2f}"
    
    # 期權分析
    if options_data:
        report += f"\n\n⚡ <b>期權分析:</b>"
        if options_data.get('max_pain'):
            distance = abs(current_price - options_data['max_pain'])
            distance_pct = (distance / current_price) * 100
            
            if distance_pct < 2:
                magnet_strength = "🔴 極強磁吸"
            elif distance_pct < 5:
                magnet_strength = "🟡 中等磁吸"
            else:
                magnet_strength = "⚪ 弱磁吸"
                
            report += f"\n🧲 <b>Max Pain:</b> ${options_data['max_pain']:.2f} {magnet_strength}"
        
        if options_data.get('put_call_ratio'):
            pc_ratio = options_data['put_call_ratio']
            sentiment = "看空" if pc_ratio > 1 else "看多" if pc_ratio < 0.8 else "中性"
            report += f"\n📊 <b>Put/Call比率:</b> {pc_ratio:.2f} ({sentiment})"
        
        report += f"\n📅 <b>期權到期日:</b> {options_data.get('expiry_date', 'N/A')}"
    
    # AI投資建議
    if advice:
        report += f"\n\n🤖 <b>AI投資建議:</b>"
        report += f"\n📈 <b>趨勢分析:</b> {advice.get('trend_analysis', 'N/A')}"
        
        if advice.get('technical_signals'):
            report += f"\n🔍 <b>技術訊號:</b>"
            for signal in advice['technical_signals'][:2]:  # 只顯示前2個
                report += f"\n   • {signal}"
        
        report += f"\n⚠️ <b>風險評估:</b> {advice.get('risk_assessment', 'N/A')}"
        
        if advice.get('time_horizon'):
            report += f"\n\n⏰ <b>投資時間框架:</b>"
            if advice['time_horizon'].get('short_term'):
                report += f"\n📅 <b>短期(1-3月):</b> {advice['time_horizon']['short_term']}"
            if advice['time_horizon'].get('long_term'):
                report += f"\n📅 <b>長期(1年+):</b> {advice['time_horizon']['long_term']}"
        
        if advice.get('portfolio_suggestion'):
            report += f"\n💼 <b>配置建議:</b> {advice['portfolio_suggestion']}"
    
    report += f"\n\n⏰ <b>更新時間:</b> {stock_data['timestamp']} (台北時間)"
    report += f"\n📡 <b>數據來源:</b> Yahoo Finance"
    report += f"\n\n<b>--- Maggie's Stock AI Pro ---</b>"
    report += f"\n<i>※ 此為技術分析建議，投資有風險，請謹慎決策</i>"
    
    return report

def handle_start_command(chat_id):
    """處理 /start 指令"""
    message = """👋 歡迎使用 <b>Maggie's Stock AI Pro</b>

📊 <b>功能介紹:</b>
🔹 /stock TSLA - 深度股票分析
🔹 /options AAPL - 期權分析
🔹 /analysis GOOGL - 完整分析報告
🔹 /help - 顯示完整幫助

🚀 <b>Pro版特色:</b>
• 深度技術分析 (RSI, 移動平均線)
• 支撐阻力位識別
• Max Pain 期權分析
• AI投資建議與風險評估
• 投資組合配置建議

💡 <b>使用範例:</b>
• /stock AAPL - Apple完整分析
• /options TSLA - Tesla期權分析
• /analysis NVDA - NVIDIA深度報告

立即體驗專業級股票分析！ 📈"""
    
    send_message(chat_id, message)

def handle_stock_command(chat_id, args):
    """處理 /stock 指令 - 基礎股票分析"""
    if not args:
        send_message(chat_id, """📖 <b>用法:</b> /stock TSLA

🔥 <b>熱門股票範例:</b>
• /stock AAPL - Apple Inc.
• /stock TSLA - Tesla Inc.
• /stock NVDA - NVIDIA Corp.
• /stock GOOGL - Alphabet Inc.
• /stock MSFT - Microsoft Corp.

<i>支援全美股8000+股票查詢</i>""")
        return
    
    symbol = args[0].upper()
    
    # 發送處理中訊息
    processing_msg = f"🔍 正在深度分析 <b>{symbol}</b>...\n⏱️ 預計1-3分鐘完成專業分析"
    send_message(chat_id, processing_msg)
    
    # 獲取股票數據
    stock_data = get_stock_data_yahoo(symbol)
    
    if stock_data:
        # 生成投資建議
        advice = generate_investment_advice(stock_data)
        
        # 格式化報告
        report = format_enhanced_stock_report(stock_data, advice=advice)
        
        send_message(chat_id, report)
        logger.info(f"成功分析股票: {symbol} for chat {chat_id}")
    else:
        error_msg = f"""❌ <b>找不到股票代碼 {symbol}</b>

💡 <b>請檢查:</b>
• 股票代碼是否正確
• 是否為美股上市公司
• 嘗試使用完整代碼

<b>範例:</b> /stock AAPL"""
        
        send_message(chat_id, error_msg)

def handle_options_command(chat_id, args):
    """處理 /options 指令 - 期權分析"""
    if not args:
        send_message(chat_id, """📖 <b>用法:</b> /options TSLA

⚡ <b>期權分析功能:</b>
• Max Pain 磁吸價位計算
• Put/Call 比率分析
• 市場情緒評估
• 期權到期日追蹤

🔥 <b>適用股票:</b>
• /options AAPL - Apple期權分析
• /options TSLA - Tesla期權數據
• /options NVDA - NVIDIA期權鏈

<i>僅支援有活躍期權交易的股票</i>""")
        return
    
    symbol = args[0].upper()
    
    processing_msg = f"⚡ 正在分析 <b>{symbol}</b> 期權數據...\n🔍 計算Max Pain與市場情緒"
    send_message(chat_id, processing_msg)
    
    # 獲取基礎股票數據
    stock_data = get_stock_data_yahoo(symbol)
    if not stock_data:
        send_message(chat_id, f"❌ 無法獲取 {symbol} 的股票數據")
        return
    
    # 獲取期權數據
    options_data = get_options_data(symbol)
    
    if options_data:
        # 格式化期權報告
        report = format_enhanced_stock_report(stock_data, options_data=options_data)
        send_message(chat_id, report)
        logger.info(f"成功分析期權: {symbol} for chat {chat_id}")
    else:
        error_msg = f"""⚠️ <b>{symbol} 期權數據不可用</b>

可能原因:
• 該股票沒有期權交易
• 期權流動性不足
• 數據源暫時不可用

請嘗試其他有活躍期權的股票，如 AAPL, TSLA, NVDA"""
        
        send_message(chat_id, error_msg)

def handle_analysis_command(chat_id, args):
    """處理 /analysis 指令 - 完整分析報告"""
    if not args:
        send_message(chat_id, """📖 <b>用法:</b> /analysis TSLA

📊 <b>完整分析包含:</b>
• 深度股票技術分析
• 期權鏈Max Pain分析
• AI投資建議
• 風險評估與配置建議

這是最全面的分析功能，整合所有數據源。""")
        return
    
    symbol = args[0].upper()
    
    processing_msg = f"📊 正在進行 <b>{symbol}</b> 完整分析...\n⏱️ 整合股票+期權數據，請稍等"
    send_message(chat_id, processing_msg)
    
    # 獲取股票數據
    stock_data = get_stock_data_yahoo(symbol)
    if not stock_data:
        send_message(chat_id, f"❌ 無法獲取 {symbol} 的股票數據")
        return
    
    # 獲取期權數據（可選）
    options_data = get_options_data(symbol)
    
    # 生成投資建議
    advice = generate_investment_advice(stock_data, options_data)
    
    # 格式化完整報告
    report = format_enhanced_stock_report(stock_data, options_data, advice)
    
    send_message(chat_id, report)
    logger.info(f"成功完整分析: {symbol} for chat {chat_id}")

def handle_help_command(chat_id):
    """處理 /help 指令"""
    message = """📚 <b>Maggie's Stock AI Pro 完整指令</b>

📊 <b>股票分析:</b>
• /stock AAPL - 基礎技術分析
• /options TSLA - 期權鏈分析  
• /analysis GOOGL - 完整深度報告

🎯 <b>分析功能:</b>
• 技術指標 (RSI, 移動平均線)
• 支撐阻力位識別
• Max Pain 磁吸價位
• Put/Call 市場情緒
• AI投資建議

⏰ <b>投資時間框架:</b>
• 短期交易建議 (1-3個月)
• 長期投資評估 (1年以上)
• 投資組合配置比例

🌍 <b>支援範圍:</b>
• 全美股8000+支股票
• 活躍期權交易股票
• 主要交易所 (NYSE, NASDAQ)

💡 <b>專業提示:</b>
• 使用 /analysis 獲得最全面的報告
• 期權分析最適合在開盤前查詢
• 所有建議僅供參考，投資需謹慎

<b>--- Maggie's Stock AI Pro ---</b>
<i>專業級股票分析，助您投資決策</i>"""
    
    send_message(chat_id, message)

def process_telegram_update(update_data):
    """處理 Telegram 更新"""
    try:
        if "message" not in update_data:
            return
        
        message = update_data["message"]
        chat_id = message["chat"]["id"]
        
        if "text" not in message:
            return
        
        text = message["text"]
        
        # 處理指令
        if text.startswith("/start"):
            handle_start_command(chat_id)
        elif text.startswith("/stock"):
            parts = text.split()
            args = parts[1:] if len(parts) > 1 else []
            handle_stock_command(chat_id, args)
        elif text.startswith("/options"):
            parts = text.split()
            args = parts[1:] if len(parts) > 1 else []
            handle_options_command(chat_id, args)
        elif text.startswith("/analysis"):
            parts = text.split()
            args = parts[1:] if len(parts) > 1 else []
            handle_analysis_command(chat_id, args)
        elif text.startswith("/help"):
            handle_help_command(chat_id)
        else:
            # 處理一般訊息
            send_message(chat_id, f"""收到訊息: <b>{text}</b>

請使用以下指令:
• /stock TSLA - 股票分析
• /options AAPL - 期權分析
• /analysis GOOGL - 完整報告
• /help - 查看完整說明""")
        
        logger.info(f"處理訊息成功: {text} from {chat_id}")
        
    except Exception as e:
        logger.error(f"處理更新失敗: {str(e)}")

# Flask 路由
@app.route("/")
def home():
    """首頁"""
    return {
        "status": "running",
        "service": "Maggie's Stock AI Pro v3.0",
        "message": "專業股票分析機器人",
        "features": [
            "深度技術分析",
            "期權Max Pain分析", 
            "AI投資建議",
            "風險評估",
            "投資組合建議"
        ],
        "version": "3.0",
        "supported_commands": ["/stock", "/options", "/analysis", "/help"]
    }

@app.route("/health")
def health():
    """健康檢查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.route("/test-stock/<symbol>")
def test_stock(symbol):
    """測試股票數據獲取"""
    stock_data = get_stock_data_yahoo(symbol)
    return {"symbol": symbol, "data": stock_data}

@app.route("/test-options/<symbol>")
def test_options(symbol):
    """測試期權數據獲取"""
    options_data = get_options_data(symbol)
    return {"symbol": symbol, "options": options_data}

@app.route("/set-webhook")
def set_webhook():
    """設置 webhook"""
    try:
        webhook_url = "https://maggie-stock-ai.onrender.com/webhook"
        url = f"{TELEGRAM_API_URL}/setWebhook"
        
        response = requests.post(url, json={"url": webhook_url}, timeout=10)
        result = response.json()
        
        if result.get("ok"):
            logger.info(f"Webhook 設置成功: {webhook_url}")
            return {"status": "success", "webhook": webhook_url}
        else:
            logger.error(f"Webhook 設置失敗: {result}")
            return {"status": "failed", "error": result}, 500
            
    except Exception as e:
        logger.error(f"設置 webhook 錯誤: {str(e)}")
        return {"status": "error", "message": str(e)}, 500

@app.route("/webhook", methods=["POST"])
def webhook():
    """處理 webhook"""
    try:
        json_data = request.get_json(force=True)
        
        if not json_data:
            return "No data", 400
        
        # 處理 Telegram 更新
        process_telegram_update(json_data)
        
        return "OK"
        
    except Exception as e:
        logger.error(f"Webhook 錯誤: {str(e)}")
        return "Error", 500

@app.route("/bot-info")
def bot_info():
    """獲取機器人資訊"""
    try:
        url = f"{TELEGRAM_API_URL}/getMe"
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
