mkdir -p src

cat > src/bot.py <<'PY'
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Hi，我是 Maggie's Stock AI 📈\n"
        "指令：\n"
        "• /stock TSLA － 看股票快報\n"
        "• /start － 顯示說明\n"
    )

# /stock <ticker>
async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("用法：/stock TSLA")
        return
    symbol = context.args[0].upper()
    # 這裡先給最小回覆（你的完整分析程式可日後接上）
    await update.message.reply_text(f"📊 {symbol} 快速回報：\n- 功能正常，待接上完整分析模組。")

def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stock", stock))
PY
