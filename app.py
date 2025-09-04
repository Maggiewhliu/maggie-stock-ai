import os, logging, datetime as dt, requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Dispatcher, CommandHandler, MessageHandler, Filters, CallbackContext

# === 環境變數 ===
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")           # 由 Render Environment 設定
BRAND_NAME = os.getenv("BRAND_NAME", "Maggie's Stock AI")

# === 基礎設定 ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
app = Flask(__name__)
bot = Bot(TOKEN)
dispatcher = Dispatcher(bot, None, workers=0)

# === 健康檢查 ===
@app.route("/", methods=["GET"])
def index():
    return "OK", 200

# === 指令處理 ===
def cmd_start(update: Update, context: CallbackContext):
    update.message.reply_text(f"嗨，我是 {BRAND_NAME}（Webhook 版）✅\n輸入 /stock TSLA 測試。")

def cmd_stock(update: Update, context: CallbackContext):
    args = context.args
    if not args:
        update.message.reply_text("用法：/stock TSLA")
        return
    symbol = args[0].upper()

    # ---- DEMO：只做安全取價（拿不到就 N/A），避免假數據 ----
    price_txt, change_txt = fetch_close_price(symbol)

    text = (
        f"昨收：{symbol}\n"
        f"💰 {price_txt} {change_txt}\n"
        f"🧲 Max Pain：{fetch_max_pain_or_na(symbol)}\n"
        f"— {BRAND_NAME}"
    )
    update.message.reply_text(text)

def any_text(update: Update, context: CallbackContext):
    update.message.reply_text(f"收到：{update.message.text}")

dispatcher.add_handler(CommandHandler("start", cmd_start))
dispatcher.add_handler(CommandHandler("stock", cmd_stock))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, any_text))

# === Webhook 入口 ===
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "OK", 200

# === 資料層（保守：拿不到就回 N/A，不回硬編模板） ===

POLY = os.getenv("POLYGON_API_KEY")  # 可先不填，沒填就 N/A
def fetch_close_price(symbol: str):
    if not POLY:
        return "N/A", "(來源未設定)"
    try:
        y = (dt.date.today() - dt.timedelta(days=1)).strftime("%Y-%m-%d")
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/1/day/{y}/{y}?adjusted=true&limit=1&apiKey={POLY}"
        r = requests.get(url, timeout=15)
        j = r.json()
        if j.get("results"):
            c = j["results"][0]["c"]
            o = j["results"][0]["o"]
            pct = (c - o) / o * 100 if o else 0
            return f"${c:.2f}", f"({pct:+.2f}%)"
        return "N/A", "(無資料)"
    except Exception as e:
        logging.exception("fetch_close_price error")
        return "N/A", "(逾時/錯誤)"

def fetch_max_pain_or_na(symbol: str):
    # 這裡先回 N/A，避免不穩定數據；等你要我再補完整 Max Pain 演算法
    return "N/A"

if __name__ == "__main__":
    # 本機測試時可用：python app.py
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
