import os
import logging
import requests
from flask import Flask, request

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
        data = {"chat_id": chat_id, "text": text}
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        logger.error(f"發送訊息失敗: {str(e)}")
        return None

@app.route("/")
def home():
    return {
        "status": "running",
        "service": "Maggie's Stock AI Bot",
        "version": "2.0 TEST",
        "message": "新版本測試中"
    }

@app.route("/health")
def health():
    return {"status": "healthy"}

@app.route("/test-stock/<symbol>")
def test_stock(symbol):
    return {"symbol": symbol, "message": "測試端點正常"}

@app.route("/set-webhook")
def set_webhook():
    webhook_url = "https://maggie-stock-ai.onrender.com/webhook"
    url = f"{TELEGRAM_API_URL}/setWebhook"
    response = requests.post(url, json={"url": webhook_url}, timeout=10)
    return response.json()

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        json_data = request.get_json(force=True)
        if "message" in json_data:
            message = json_data["message"]
            chat_id = message["chat"]["id"]
            text = message.get("text", "")
            
            if text.startswith("/start"):
                send_message(chat_id, "機器人運行正常 - 新版本測試中")
            elif text.startswith("/stock"):
                send_message(chat_id, "股票功能開發中 - 新版本已部署")
            else:
                send_message(chat_id, f"收到: {text}")
        
        return "OK"
    except Exception as e:
        logger.error(f"Webhook 錯誤: {str(e)}")
        return "Error", 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
