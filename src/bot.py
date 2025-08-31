# --- 在檔案頂部已經有的 import 後面加 ---
import sys

# ...（保留你原來的 import 與 BRAND_NAME 設定）...

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"嗨，我是 {BRAND_NAME}。\n"
        "可用指令：\n"
        "/stock TSLA\n/maxpain TSLA\n/gex TSLA\n/ipo ABC"
    )

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN 未設定", file=sys.stderr)
        raise SystemExit(1)

    print("[INFO] Starting bot with polling…")
    print(f"[INFO] BRAND_NAME={BRAND_NAME}")
    app = ApplicationBuilder().token(token).build()

    # 新增 /start 指令
    app.add_handler(CommandHandler('start', start_cmd))

    # 你原本已經有的 handlers
    app.add_handler(CommandHandler('stock', stock_cmd))
    app.add_handler(CommandHandler('maxpain', maxpain_cmd))
    app.add_handler(CommandHandler('gex', gex_cmd))
    app.add_handler(CommandHandler('ipo', ipo_cmd))

    # 全域錯誤訊息（可選）
    async def on_error(update, context):
        print(f"[ERROR] {context.error}", file=sys.stderr)
    app.add_error_handler(on_error)

    app.run_polling(drop_pending_updates=True, allowed_updates=["message"])
