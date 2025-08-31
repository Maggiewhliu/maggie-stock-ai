# server.py — Webhook server for Telegram
import os, asyncio
from fastapi import FastAPI, Request
from telegram.ext import ApplicationBuilder
from src.bot import start_cmd, stock_cmd, maxpain_cmd, gex_cmd, ipo_cmd  # 直接重用你的 handlers
from telegram.ext import CommandHandler

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
app = FastAPI()
tg_app = ApplicationBuilder().token(TOKEN).updater(None).build()
tg_app.add_handler(CommandHandler("start", start_cmd))
tg_app.add_handler(CommandHandler("stock", stock_cmd))
tg_app.add_handler(CommandHandler("maxpain", maxpain_cmd))
tg_app.add_handler(CommandHandler("gex", gex_cmd))
tg_app.add_handler(CommandHandler("ipo", ipo_cmd))

@app.on_event("startup")
async def startup():
    await tg_app.initialize()
    # 這裡不要 start_polling；我們用 webhook receiver
    # setWebhook 交由部署完成後用 curl 打一次（或在此讀環境變數自動設定也可）

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    await tg_app.update_queue.put(tg_app.bot._build_update(data))  # 交給 PTB 處理
    return {"ok": True}
