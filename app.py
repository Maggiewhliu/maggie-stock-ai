import os
import logging
import requests
from flask import Flask, request, jsonify
from datetime import datetime
import json

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 環境變數
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("請設置 TELEGRAM_BOT_TOKEN 環境變數")

# Telegram API 基礎 URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TOKEN}"

# 創建 Flask 應用
app = Flask(__name__)

def send_message(chat_id, text):
    """發送訊息到 Telegram"""
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"發送訊息失敗: {str(e)}")
        return None

def get_stock_data_alphavantage(symbol):
    """使用 Alpha Vantage API 獲取股票數據"""
    try:
        # 使用 Alpha Vantage 免費 API (demo key)
        api_key = "demo"
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": api_key
        }
        
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if "Global Quote" in data:
            quote = data["Global Quote"]
            
            current_price = float(quote.get("05. price", 0))
            change = float(quote.get("09. change", 0))
            change_percent = quote.get("10. change percent", "0%").replace("%", "")
            
            return {
                "symbol": quote.get("01. symbol", symbol).upper(),
                "current_price": current_price,
                "change": change,
                "change_percent": float(change_percent),
                "volume": int(float(quote.get("06. volume", 0))),
                "previous_close": float(quote.get("08. previous close", 0)),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "source": "Alpha Vantage"
            }
        else:
            # API 限制或無效股票代碼時返回 None
            return None
            
    except Exception as e:
        logger.error(f"Alpha Vantage API 錯誤: {str(e)}")
        return None

def get_stock_data_finnhub(symbol):
    """使用 Finnhub API 獲取股票數據"""
    try:
        # 使用 Finnhub sandbox API
        api_key = "sandbox_c0dc1h748v6pfihfog40"
        url = f"https://finnhub.io/api/v1/quote"
        params = {
            "symbol": symbol,
            "token": api_key
        }
        
        response = requests.get(url, params=params, timeout=15)
        data = response.json()
        
        if data.get("c") is not None:
            current_price = data["c"]
            previous_close = data["pc"]
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close != 0 else 0
            
            return {
                "symbol": symbol.upper(),
                "current_price": current_price,
                "change": change,
                "change_percent": change_percent,
                "high": data.get("h", 0),
                "low": data.get("l", 0),
                "open": data.get("o", 0),
                "previous_close": previous_close,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "source": "Finnhub (Sandbox)"
            }
        else:
            return None
            
    except Exception as e:
        logger.error(f"Finnhub API 錯誤: {str(e)}")
        return None

def get_real_stock_data(symbol):
    """獲取真實股票數據 - 多重 API 備援"""
    
    # 嘗試 Alpha Vantage (但會有 API 限制)
    data = get_stock_data_alphavantage(symbol)
    if data:
        return data
    
    # 如果 Alpha Vantage 失敗，嘗試 Finnhub
    data = get_stock_data_finnhub(symbol)
    if data:
        return data
    
    # 如果所有 API 都失敗，返回模擬數據
    logger.warning(f"所有 API 都失敗，返回 {symbol} 的模擬數據")
    return generate_mock_data(symbol)

def generate_mock_data(symbol):
    """生成合理的模擬數據"""
    import random
    
    # 根據股票代碼生成基礎價格
    base_prices = {
        "AAPL": 175,
        "TSLA": 250,
        "GOOGL": 135,
        "MSFT": 330,
        "NVDA": 450,
        "AMZN": 140
    }
    
    base_price = base_prices.get(symbol.upper(), 100)
    
    # 添加隨機波動
    random_factor = random.uniform(0.95, 1.05)
    current_price = round(base_price * random_factor, 2)
    
    # 生成變動
    change = round(random.uniform(-5, 5), 2)
    previous_close = round(current_price - change, 2)
    change_percent = round((change / previous_close * 100), 2) if previous_close != 0 else 0
    
    return {
        "symbol": symbol.upper(),
        "current_price": current_price,
        "change": change,
        "change_percent": change_percent,
        "volume": random.randint(1000000, 50000000),
        "previous_close": previous_close,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "source": "模擬數據"
    }

def format_stock_report(stock_data):
    """格式化股票報告"""
    if not stock_data:
        return "❌ 無法獲取股票數據，請檢查股票代碼是否正確"
    
    symbol = stock_data['symbol']
    current_price = stock_data['current_price']
    change = stock_data['change']
    change_percent = stock_data['change_percent']
    volume = stock_data.get('volume', 0)
    source = stock_data.get('source', 'Unknown')
    
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
    
    report = f"""📊 <b>{symbol} 股票分析</b>

💰 <b>當前價格:</b> ${current_price:.2f}
{trend_emoji} <b>變動:</b> {change:+.2f} ({change_percent:+.2f}%) {trend_text}
📦 <b>成交量:</b> {volume:,}
"""
    
    # 添加額外資訊（如果有的話）
    if 'high' in stock_data:
        report += f"📊 <b>日高:</b> ${stock_data['high']:.2f}\n"
    if 'low' in stock_data:
        report += f"📊 <b>日低:</b> ${stock_data['low']:.2f}\n"
    
    report += f"""
⏰ <b>更新時間:</b> {stock_data['timestamp']} (台北時間)
📡 <b>數據來源:</b> {source}

<b>--- Maggie's Stock AI ---</b>"""
    
    return report

def generate_simple_ai_recommendation(stock_data):
    """生成簡單的 AI 投資建議"""
    if not stock_data:
        return "無法提供建議"
    
    change_percent = stock_data['change_percent']
    
    # 簡單的建議邏輯
    if change_percent > 3:
        sentiment = "強勢上漲，但需注意回調風險"
        score = "樂觀 ⭐⭐⭐⭐"
    elif change_percent > 1:
        sentiment = "溫和上漲，表現穩健"
        score = "謹慎樂觀 ⭐⭐⭐"
    elif change_percent > -1:
        sentiment = "震盪整理，觀望為主"
        score = "中性 ⭐⭐"
    elif change_percent > -3:
        sentiment = "下跌調整，可考慮逢低佈局"
        score = "謹慎 ⭐⭐"
    else:
        sentiment = "大幅下跌，需要謹慎評估"
        score = "風險較高 ⭐"
    
    return f"""
🤖 <b>AI 投資建議:</b>
📈 <b>趨勢分析:</b> {sentiment}
⭐ <b>評級:</b> {score}

<i>※ 此為技術分析建議，投資有風險，請謹慎決策</i>"""

def handle_start_command(chat_id):
    """處理 /start 指令"""
    message = """👋 嗨！我是 <b>Maggie's Stock AI</b>

📊 <b>功能介紹:</b>
🔹 /stock TSLA - 查詢股票實時數據
🔹 /help - 顯示完整幫助

🆓 <b>免費版特色:</b>
• 實時股價查詢
• AI 投資建議  
• 技術分析評級
• 支援全球主要股票

💡 <b>使用範例:</b>
• /stock AAPL (蘋果)
• /stock TSLA (特斯拉)  
• /stock GOOGL (谷歌)
• /stock MSFT (微軟)

立即開始您的投資分析之旅！ 🚀"""
    
    send_message(chat_id, message)

def handle_stock_command(chat_id, args):
    """處理 /stock 指令"""
    if not args:
        send_message(chat_id, """📖 <b>用法:</b> /stock TSLA

🔥 <b>熱門股票範例:</b>
• /stock AAPL - Apple Inc.
• /stock TSLA - Tesla Inc.
• /stock NVDA - NVIDIA Corp.
• /stock GOOGL - Alphabet Inc.
• /stock MSFT - Microsoft Corp.

<i>支援美股主要股票</i>""")
        return
    
    symbol = args[0].upper()
    
    # 發送處理中訊息
    processing_msg = f"🔍 正在獲取 <b>{symbol}</b> 的股票數據...\n請稍等片刻"
    send_message(chat_id, processing_msg)
    
    # 獲取真實股票數據
    stock_data = get_real_stock_data(symbol)
    
    if stock_data:
        # 格式化股票報告
        report = format_stock_report(stock_data)
        
        # 生成 AI 建議
        ai_recommendation = generate_simple_ai_recommendation(stock_data)
        
        # 合併報告
        full_report = report + ai_recommendation
        
        send_message(chat_id, full_report)
        
        logger.info(f"成功查詢股票: {symbol} for chat {chat_id}")
    else:
        error_msg = f"""❌ <b>暫時無法獲取 {symbol} 的數據</b>

💡 <b>請嘗試:</b>
• 檢查股票代碼是否正確
• 稍後再試
• 嘗試其他熱門股票如 AAPL, TSLA

<b>範例:</b> /stock AAPL"""
        
        send_message(chat_id, error_msg)

def handle_help_command(chat_id):
    """處理 /help 指令"""
    message = """📚 <b>Maggie's Stock AI 完整指令</b>

📊 <b>股票查詢:</b>
• /stock AAPL - 查詢 Apple 股票
• /stock TSLA - 查詢 Tesla 股票  
• /stock GOOGL - 查詢 Google 股票

🌍 <b>支援股票:</b>
• 美股主要公司 (NASDAQ, NYSE)
• 科技股、金融股等

📈 <b>分析功能:</b>
• 實時股價與變動
• 成交量分析
• AI 投資建議

ℹ️ <b>系統指令:</b>
• /start - 歡迎訊息
• /help - 顯示此幫助

💡 <b>使用技巧:</b>
• 股票代碼不區分大小寫
• 支援主要美股代碼

<b>--- Maggie's Stock AI ---</b>
<i>專業股票分析，助您投資決策</i>"""
    
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
            # 解析參數
            parts = text.split()
            args = parts[1:] if len(parts) > 1 else []
            handle_stock_command(chat_id, args)
        elif text.startswith("/help"):
            handle_help_command(chat_id)
        else:
            # 處理一般訊息
            send_message(chat_id, f"""收到訊息: <b>{text}</b>

請使用以下指令:
• /stock TSLA - 查詢股票
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
        "service": "Maggie's Stock AI Bot v2.0",
        "message": "機器人運行中",
        "features": ["real-time stock data", "AI recommendations", "multiple APIs"],
        "version": "2.0",
        "apis": ["Alpha Vantage", "Finnhub", "Mock Data"]
    }

@app.route("/health")
def health():
    """健康檢查"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.route("/test-stock/<symbol>")
def test_stock(symbol):
    """測試股票數據獲取"""
    stock_data = get_real_stock_data(symbol)
    return {"symbol": symbol, "data": stock_data}

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
