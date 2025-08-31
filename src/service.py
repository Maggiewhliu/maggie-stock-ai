# server.py  — FastAPI Webhook server for Telegram (Render/Railway ready)
import os, asyncio, logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# 從你現有專案引入功能（與 src/bot.py 同步）
from src.provider_yahoo import YahooProvider
from src.provider_ipo import IPOProvider
from src.provider_search import yf_search
from src.service import maxpain_handler, gex_handler
from src.analyzers import magnet_strength
from src.strategy import gen_strategy

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("server")

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BRAND_NAME = os.getenv("BRAND_NAME", "Maggie's Stock AI")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # 部署完成後可填入 https://你的域名/webhook

app = FastAPI()
tg_app = None  # telegram Application 物件（全域持有）

# ---- 小工具 ----
def _m(v): return "—" if v is None else f"${v:,.2f}"
def _p(v): return "—" if v is None else f"{v:.2f}%"

# ---- Handlers（與 src/bot.py 相同邏輯）----
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"嗨，我是 {BRAND_NAME}。\n"
        "可用指令：\n"
        "/find tesla  — 模糊找代號\n"
        "/stock TSLA  — 完整報告（含GPT/規則策略）\n"
        "/maxpain TSLA [YYYY-MM-DD]\n"
        "/gex TSLA [YYYY-MM-DD]\n"
        "/ipo AB — 查 IPO"
    )

async def find_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("用法：/find <關鍵字>")
    query = " ".join(context.args)
    hits = await yf_search(query, limit=10, us_only=True)
    if not hits:
        return await update.message.reply_text("找不到相符的美股代號，換個關鍵字試試？")
    lines = ["🔎 搜尋結果（美股）："]
    for h in hits:
        nm = f" — {h['name']}" if h['name'] else ""
        lines.append(f"• {h['symbol']}{nm} 〔{h['exchDisp']}/{h['type']}〕")
    lines.append("\n👉 接著可輸入：/stock 代號 例：/stock TSLA")
    await update.message.reply_text("\n".join(lines))

async def stock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("用法：/stock <TICKER>")
    symbol = context.args[0].upper()
    yp = YahooProvider()

    q = yp.get_quote(symbol)
    spot = q.get("price")
    prev_close = q.get("previous_close")
    chg = q.get("change")
    chg_pct = q.get("change_pct")

    expiry = yp.nearest_expiry(symbol)
    mp = maxpain_handler(symbol, expiry)
    gex, support, resistance = gex_handler(symbol, expiry, spot=spot or 0.0)
    magnet = magnet_strength(spot or mp['max_pain'], mp['max_pain'])

    mood = "📊 震盪整理"
    if chg_pct is not None:
        if abs(chg_pct) < 0.3: mood = "📊 震盪整理"
        elif chg_pct >= 0.3:   mood = "📈 上行偏多"
        else:                  mood = "📉 下行偏空"

    strategy_text = gen_strategy(
        symbol=symbol, spot=spot or mp['max_pain'],
        max_pain=mp['max_pain'], support=support, resistance=resistance
    )

    lines = []
    lines.append(f"🆓 免費版美股查詢 @{context.bot.username}")
    lines.append("")
    lines.append("📊 昨日收盤表現")
    lines.append(f"📉 {symbol} ({symbol})")
    lines.append(f"💰 {_m(prev_close)} ({_m(chg)} | {_p(chg_pct)})")
    lines.append(mood)
    lines.append("")
    lines.append(f"📍 {symbol}: {_m(spot)} {magnet} (距離: {_m(abs((spot or 0) - mp['max_pain']))})")
    lines.append("")
    lines.append("⚡ Gamma 支撐阻力位")
    lines.append(f"🛡️ {symbol}: 支撐 {_m(support)} | 阻力 {_m(resistance)}")
    lines.append(f"💵 Dollar Gamma (1%): {gex.dollar_gamma_1pct:,.0f}")
    lines.append("")
    lines.append(strategy_text)
    lines.append("")
    lines.append("🆕 本週IPO關注")
    lines.append("📅 YYYY公司 (YYYY): 8/20上市")
    lines.append("💰 發行價: $15-18")
    lines.append("📊 AI評估: 中性，建議觀察首日表現")
    lines.append("")
    lines.append("🤖 MM 行為預測")
    lines.append(f"預計今日主力將在 Max Pain（{mp['max_pain']}）附近進行操控，注意{symbol}的量價配合表現。")
    lines.append("")
    lines.append(f"— {BRAND_NAME}")
    await update.message.reply_text("\n".join(lines))

async def maxpain_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("用法：/maxpain <TICKER> [YYYY-MM-DD]")
    symbol = context.args[0].upper()
    yp = YahooProvider()
    expiry = context.args[1] if len(context.args) > 1 else yp.nearest_expiry(symbol)
    res = maxpain_handler(symbol, expiry)
    await update.message.reply_text(
        f"🔎 {res['symbol']} {res['expiry']}\n"
        f"📍 Max Pain：{res['max_pain']}\n"
        f"💰 Min Total Pain：${int(res['min_total_pain']):,}"
    )

async def gex_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("用法：/gex <TICKER> [YYYY-MM-DD]")
    symbol = context.args[0].upper()
    yp = YahooProvider()
    expiry = context.args[1] if len(context.args) > 1 else yp.nearest_expiry(symbol)
    spot = yp.get_spot(symbol)['price']
    g, s, r = gex_handler(symbol, expiry, spot=spot)
    await update.message.reply_text(
        f"🔎 {symbol} {expiry}\n"
        f"📈 Share Gamma：{g.share_gamma:.2f}\n"
        f"💵 Dollar Gamma (1%)：{g.dollar_gamma_1pct:,.0f}\n"
        f"支撐 {s} | 阻力 {r}"
    )

async def ipo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("用法：/ipo <SYMBOL>")
    symbol = context.args[0].upper()
    prov = IPOProvider()
    data = await prov.get_ipo(symbol)
    if not data:
        return await update.message.reply_text(
            "🆕 最新IPO（資料源需 API Key；目前顯示模板）\n"
            "📅 上市日期：YYYY-MM-DD\n"
            "💰 發行價區間：$15-18\n"
            "🏢 公司簡介：—\n"
            "⚠️ 風險提示：新股波動大"
        )
    msg = (
        f"🆕 IPO：{data['symbol']} — {data.get('name','-')}\n"
        f"📅 上市日期：{data.get('date','-')}\n"
        f"💰 發行價區間：{data.get('range','-')}\n"
        f"💼 承銷商：{data.get('underwriters','-')}\n"
        f"📌 狀態：{data.get('status','-')}\n"
        f"📝 備註：{data.get('notes','') or '-'}\n"
        f"— {BRAND_NAME}"
    )
    await update.message.reply_text(msg)

# ---- FastAPI lifecycle ----
@app.on_event("startup")
async def on_startup():
    global tg_app
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 未設定")
    tg_app = ApplicationBuilder().token(TOKEN).updater(None).build()
    # 註冊 handlers（就是你問的「註冊 handlers 的地方」）
    tg_app.add_handler(CommandHandler("start", start_cmd))
    tg_app.add_handler(CommandHandler("find", find_cmd))
    tg_app.add_handler(CommandHandler("stock", stock_cmd))
    tg_app.add_handler(CommandHandler("maxpain", maxpain_cmd))
    tg_app.add_handler(CommandHandler("gex", gex_cmd))
    tg_app.add_handler(CommandHandler("ipo", ipo_cmd))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                      lambda u,c: u.message.reply_text("請輸入 /find 關鍵字 或 /stock TSLA")))
    await tg_app.initialize()
    # 清 webhook（避免殘留）
    try:
        await tg_app.bot.delete_webhook(drop_pending_updates=True)
    except Exception:
        pass
    # 如果你已經知道自己的公開 URL，啟動時就直接 setWebhook
    if WEBHOOK_URL:
        await tg_app.bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
        logger.info(f"Webhook set to {WEBHOOK_URL}")

@app.on_event("shutdown")
async def on_shutdown():
    if tg_app:
        await tg_app.shutdown()

@app.get("/health")
async def health():
    return PlainTextResponse("ok")

@app.get("/set-webhook")
async def set_webhook(url: str):
    """方便你在部署後，用 GET /set-webhook?url=https://xxx/webhook 一鍵設定"""
    await tg_app.bot.set_webhook(url=url, drop_pending_updates=True)
    return JSONResponse({"ok": True, "url": url})

@app.post("/webhook")
async def telegram_webhook(req: Request):
    """Telegram 會把 update JSON 打到這裡"""
    data = await req.json()
    update = Update.de_json(data, tg_app.bot)  # 轉為 Update 物件
    await tg_app.process_update(update)        # 交給 PTB 處理
    return JSONResponse({"ok": True})
