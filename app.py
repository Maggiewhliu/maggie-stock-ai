import os
import logging
import requests
from flask import Flask, request, jsonify

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

def handle_start_command(chat_id):
    """處理 /start 指令"""
    message = """👋 嗨！我是 Maggie's Stock AI

🔹 /stock TSLA - 查詢股票
🔹 /help - 顯示幫助

機器人運行正常！"""
    
    send_message(chat_id, message)

def handle_stock_command(chat_id, args):
    """處理 /stock 指令"""
    if not args:
        send_message(chat_id, "用法：/stock TSLA")
        return
    
    symbol = args[0].upper()
    message = f"""📊 {symbol} 分析報告

💰 價格：$250.00
📈 變動：+2.5%
🎯 狀態：測試中

（這是測試數據，功能開發中）"""
    
    send_message(chat_id, message)

def handle_help_command(chat_id):
    """處理 /help 指令"""
    message = """📚 Maggie's Stock AI 指令：

🔹 /start - 開始使用
🔹 /stock TSLA - 股票查詢
🔹 /help - 顯示此幫助

更多功能開發中..."""
    
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
            send_message(chat_id, f"收到訊息：{text}\n請使用 /help 查看可用指令")
        
        logger.info(f"處理訊息成功: {text} from {chat_id}")
        
    except Exception as e:
        logger.error(f"處理更新失敗: {str(e)}")

# Flask 路由
@app.route("/")
def home():
    """首頁"""
    return {
        "status": "running",
        "service": "Maggie's Stock AI Bot",
        "message": "機器人運行中"
    }

@app.route("/health")
def health():
    """健康檢查"""
    return {"status": "healthy"}

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
