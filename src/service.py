cat > server.py <<'PY'
import os, json
from fastapi import FastAPI, Request
import httpx
from telegram import Update
from telegram.ext import Application

# 你給的 Token（先硬寫，方便跑通；日後可改環境變數）
TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN",
    "8320641094:AAGoaTpTlZDnA2wH8Qq5Pqv-8L7thECoR2s",
)

BASE_URL = os.getenv("BASE_URL", "https://maggie-stock-ai.onrender.com")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", f"{BASE_URL}/webhook")

app = FastAPI()

# 建立 Telegram Application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# 匯入並註冊 handlers
from src.bot import register_handlers
register_handlers(application)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"service": "Maggie Stock AI", "webhook": WEBHOOK_URL}

# 一鍵設定 webhook（可用瀏覽器 GET 觸發）
@app.get("/set-webhook")
async def set_webhook(url: str = None):
    target = url or WEBHOOK_URL
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
            params={"url": target},
        )
    return r.json()

@app.get("/delete-webhook")
async def delete_webhook(drop_pending_updates: bool = True):
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook",
            params={"drop_pending_updates": json.dumps(drop_pending_updates).lower()},
        )
    return r.json()

# Telegram webhook 收件口：把 update 交給 bot application
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}
PY
