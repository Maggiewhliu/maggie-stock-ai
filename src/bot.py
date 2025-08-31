# src/bot.py
import os, sys, asyncio, logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)

from src.provider_yahoo import YahooProvider
from src.provider_ipo import IPOProvider           # 若未設 POLYGON_API_KEY 會自動回模板
from src.service import maxpain_handler, gex_handler
from src.analyzers import magnet_strength
from src.strategy import gen_strategy              # 產生「短/中/長線」＋提醒

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s"
)
BRAND_NAME = os.getenv("BRAND_NAME", "Maggie's Stock AI")

# ---------- 格式工具 ----------
def _m(v):  # money
    return "—" if v is None else f"${v:,.2f}"

def _p(v):  # percent
    return "—" if v is None else f"{v:.2f}%"

# ---------- 指令 ----------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"嗨，我是 {BRAND_NAME}。\n"
        "可用指令：\n"
        "/stock TSLA  — 完整報告\n"
        "/maxpain TSLA [YYYY-MM-DD]\n"
        "/gex TSLA [YYYY-MM-DD]\n"
        "/ipo AB — 查 IPO"
    )

async def stock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            return await update.message.reply_text("用法：/stock <TICKER>")
        symbol = context.args[0].upper()
        yp = YahooProvider()

        # 即時行情/漲跌
        q = yp.get_quote(symbol)
        spot = q.get("price")
        prev_close = q.get("previous_close")
        chg = q.get("change")
        chg_pct = q.get("change_pct")

        # 期權衍生：到期日、Max Pain、Gamma 支撐阻力
        expiry = yp.nearest_expiry(symbol)
        mp = maxpain_handler(symbol, expiry)
        gex, support, resistance = gex_handler(symbol, expiry, spot=spot or 0.0)
        magnet = magnet_strength(spot or mp['max_pain'], mp['max_pain'])

        # —— 市場情緒簡標
        mood = "📊 震盪整理"
        if chg_pct is not None:
            if abs(chg_pct) < 0.3:
                mood = "📊 震盪整理"
            elif chg_pct >= 0.3:
                mood = "📈 上行偏多"
            else:
                mood = "📉 下行偏空"

        # —— AI 策略與提醒
        strategy_text = gen_strategy(
            symbol=symbol,
            spot=spot or mp['max_pain'],
            max_pain=mp['max_pain'],
            support=support,
            resistance=resistance
        )

        # —— 組裝訊息（依你提供的大綱）
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
        lines.append("")
        lines.append("🎯 今日重點關注")
        lines.append("🔥 最強: 🍎 Apple (+1.60%)")
        lines.append("⚠️ 最弱: 🚀 NVIDIA (-0.83%)")
        lines.append("")
        lines.append(strategy_text)  # <<— 含「🧲 Max Pain 提醒」「短/中/長線」「交易策略提醒」
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
    except Exception as e:
        await update.message.reply_text(f"錯誤：{e}")

async def maxpain_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
    except Exception as e:
        await update.message.reply_text(f"錯誤：{e}")

async def gex_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
    except Exception as e:
        await update.message.reply_text(f"錯誤：{e}")

async def ipo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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
    except Exception as e:
        await update.message.reply_text(f"錯誤：{e}")

# ---------- 啟動（顯式 async 流程，解決 ExtBot.initialize 問題） ----------
async def run():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN 未設定", file=sys.stderr)
        raise SystemExit(1)

    app = ApplicationBuilder().token(token).build()
    # handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("stock", stock_cmd))
    app.add_handler(CommandHandler("maxpain", maxpain_cmd))
    app.add_handler(CommandHandler("gex", gex_cmd))
    app.add_handler(CommandHandler("ipo", ipo_cmd))
    # 非指令文字：提示用法
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   lambda u,c: u.message.reply_text("請輸入 /stock TSLA、/maxpain TSLA 等指令")))

    print("[INFO] Initializing…")
    await app.initialize()

    # 確保沒有殘留 webhook（否則 polling 收不到）
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        print("[INFO] Webhook cleared.")
    except Exception as e:
        print(f"[WARN] delete_webhook failed: {e}")

    print(f"[INFO] BRAND_NAME={BRAND_NAME}")
    print("[INFO] Starting…")
    await app.start()
    print("[INFO] Polling…（到 Telegram 輸入 /start）")
    await app.updater.start_polling(allowed_updates=["message"], drop_pending_updates=True)

    # 阻塞
    await asyncio.Event().wait()

def main():
    asyncio.run(run())

if __name__ == "__main__":
    main()
