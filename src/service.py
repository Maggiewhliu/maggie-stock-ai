# server.py
import os, json
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
WEBHOOK_URL        = os.getenv("WEBHOOK_URL", "")

app = FastAPI()

# 初始化 bot application
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# 匯入你原本 bot.py 註冊的 handlers
from src.bot import register_handlers
register_handlers(application)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}
