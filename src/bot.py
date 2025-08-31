import os, sys, asyncio, logging, datetime as dt
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, filters
)

from src.provider_yahoo import YahooProvider
from src.service import maxpain_handler, gex_handler
from src.analyzers import magnet_strength

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s"
)
BRAND_NAME = os.getenv("BRAND_NAME", "Maggie's Stock AI")

# ---------- helpers ----------
def _fmt_money(v):
    return "—" if v is None else f"${v:,.2f}"

def _fmt_pct(p):
    return "—" if p is None else f"{p:.2f}%"

# ---------- commands ----------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"嗨，我是 {BRAND_NAME}。\n"
        "可用指令：\n"
        "/stock TSLA\n/maxpain TSLA\n/gex TSLA\n/ipo ABC"
    )

async def stock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            return await update.message.reply_text("用法：/stock <TICKER>")
        symbol = context.args[0].upper()
        yp = YahooProvider()
        q = yp.get_quote(symbol)
        spot = q.get("price")
        expiry = yp.nearest_expiry(symbol)
        mp = maxpain_handler(symbol, expiry)
        gex, support, resistance = gex_handler(symbol, expiry, spot=spot or 0.0)
        magnet = magnet_strength(spot or mp['max_pain'], mp['max_pain'])
        msg = (
            f"📉 {symbol}\n"
            f"💰 即時 { _fmt_money(spot) } | 昨收 { _fmt_money(q.get('previous_close')) } | 變動 {_fmt_money(q.get('change'))} ({_fmt_pct(q.get('change_pct'))})\n"
            f"📍 Max Pain {mp['max_pain']}  {magnet}  (距離: {_fmt_money(abs((spot or 0) - mp['max_pain']))})\n"
            f"⚡ Gamma 支撐/阻力：支撐 {support} | 阻力 {resistance}\n"
            f"💵 Dollar Gamma (1%)：{gex.dollar_gamma_1pct:,.0f}\n"
            f"— {BRAND_NAME}"
        )
        await update.message.reply_text(msg)
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
        await update.message.reply_text(
            "🆕 最新IPO（示例模板）\n"
            "📅 上市日期：YYYY-MM-DD\n"
            "💰 發行價區間：$15-18\n"
            "🏢 公司簡介：—\n"
            "⚠️ 風險提示：新股波動大\n"
        )
    except Exception as e:
        await update.message.reply_text(f"錯誤：{e}")

# ---------- runner ----------
async def run():
    token = os.
