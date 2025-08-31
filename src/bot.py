import os, logging, datetime as dt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from src.provider_yahoo import YahooProvider
from src.service import maxpain_handler, gex_handler
from src.analyzers import magnet_strength

logging.basicConfig(level=os.getenv('LOG_LEVEL','INFO'))

BRAND_NAME = os.getenv("BRAND_NAME", "Maggie's Stock AI")

# ---- 小工具區 ----
def _fmt_pct(p):
    return f"{p:.2f}%" if p is not None else "—"

def _fmt_money(v):
    return f"${v:,.2f}" if v is not None else "—"

def _yesterday_close_line(q):
    # e.g. "💰 $339.38 (-1.46 | -0.43%)"
    price = _fmt_money(q.get("previous_close"))
    chg = q.get("change")
    chg_pct = q.get("change_pct")
    # 將昨日漲跌取負的直覺換成「昨日收盤 vs 前一日」；若無資料，用 "—"
    if chg is not None:
        # 這裡用當日價 vs 昨收；在「昨日收盤表現」段落，我們只展示昨收價即可
        pass
    return f"💰 {price} ({_fmt_money(q.get('change')) or '—'} | {_fmt_pct(chg_pct)})"

def _market_mood_label(change_pct):
    if change_pct is None:
        return "📊 數據不足"
    if abs(change_pct) < 0.3:
        return "📊 震盪整理"
    if change_pct >= 0.3:
        return "📈 上行偏多"
    return "📉 下行偏空"

def _strong_weak_examples():
    # 先放示例；之後可接你的榜單計算或外部 API
    strongest = "🍎 Apple (+1.60%)"
    weakest = "🚀 NVIDIA (-0.83%)"
    return strongest, weakest

def _ipo_weekly_highlight():
    # 占位：你之後可以接納斯達克 / 券商 API
    return {
        "name": "YYYY公司 (YYYY)",
        "date": "8/20",
        "price_range": "15-18",
        "ai_view": "中性，建議觀察首日表現"
    }

def _ipo_detail_template(symbol: str):
    # 占位詳細模板；/ipo 指令會用
    return {
        "symbol": symbol.upper(),
        "date": "2025-08-20",
        "range": "15-18",
        "intro": "AI醫療診斷技術公司",
        "sector": "醫療科技",
        "underwriter": "Goldman Sachs",
        "risk": "新股波動大，請謹慎投資",
        "fundamentals": {
            "rev_yoy": "+45%",
            "gross_margin": "68%",
            "net_margin": "15%",
            "tam": "$50B",
            "edge": "專利技術護城河",
        },
        "valuation": {
            "dcf": "$16-19",
            "comp_pe": "12-15x",
            "fair": "$16-20",
            "up": "$25 (+39%)",
            "down": "$12 (-20%)"
        },
        "technical": {
            "vol_day1": "±30%",
            "entry": "$14-16",
            "stop": "$11 (-25%)"
        },
        "advice": {
            "rating": "謹慎樂觀 ⭐⭐⭐",
            "strategy": "觀察首日表現，如跌破發行價可考慮分批進場",
            "risk": "中等（新股波動、行業競爭）"
        }
    }

# ---- /stock：主模板 ----
async def stock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            return await update.message.reply_text('用法：/stock <TICKER>')
        symbol = context.args[0].upper()
        yp = YahooProvider()

        # Quote + 衍生
        q = yp.get_quote(symbol)
        spot = q.get("price")
        prev_close = q.get("previous_close")
        chg = None if (spot is None or prev_close in (None, 0)) else (spot - prev_close)
        chg_pct = None if (chg is None or prev_close in (None, 0)) else (chg/prev_close*100.0)

        # 衍生：磁吸 / Max Pain / GEX 支撐阻力
        expiry = yp.nearest_expiry(symbol)
        mp = maxpain_handler(symbol, expiry)
        gex, support, resistance = gex_handler(symbol, expiry, spot=spot or 0.0)
        magnet = magnet_strength(spot or mp['max_pain'], mp['max_pain'])
        s_line = f"🛡️ {symbol}: 支撐 {_fmt_money(support)} | 阻力 {_fmt_money(resistance)}"

        # 今日強弱（示例）
        strongest, weakest = _strong_weak_examples()

        # IPO 本週關注（示例）
        wh = _ipo_weekly_highlight()

        # 模板輸出
        title_line = f"📉 {symbol} ({symbol})"  # 這裡可替換成公司名，需額外資料源
        y_close_block = (
            "📊 昨日收盤表現\n"
            f"{title_line}\n"
            f"{_yesterday_close_line(q)}\n"
            f"{_market_mood_label(chg_pct)}\n"
        )

        magnet_line = f"📍 {symbol}: {_fmt_money(spot)} {magnet} (距離: {_fmt_money(abs((spot or 0) - mp['max_pain']))})"
        gamma_block = f"⚡ Gamma 支撐阻力位\n{s_line}\n"

        focus_block = (
            "🎯 今日重點關注\n"
            f"🔥 最強: {strongest}\n"
            f"⚠️ 最弱: {weakest}\n"
        )

        advice_block = (
            "💡 交易策略建議\n"
            "‧ 短線: \n"
            "‧ 中線: \n"
            "‧ 長線: \n"
        )

        ipo_block = (
            "🆕 本週IPO關注\n"
            f"📅 {wh['name']}: {wh['date']}上市\n"
            f"💰 發行價: ${wh['price_range']}\n"
            f"📊 AI評估: {wh['ai_view']}\n"
        )

        mm_block = (
            "🤖 MM 行為預測\n"
            f"預計今日主力將在 Max Pain（{mp['max_pain']}）附近進行操控，注意{symbol}的量價配合表現。\n"
        )

        footer = f"— {BRAND_NAME}"

        msg = (
            f"{y_close_block}\n"
            f"{magnet_line}\n\n"
            f"{gamma_block}\n"
            f"{focus_block}\n"
            f"{advice_block}\n"
            f"{ipo_block}\n"
            f"{mm_block}\n"
            f"{footer}"
        )

        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f'錯誤：{e}')

# ---- /maxpain 與 /gex 保留 ----
async def maxpain_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            return await update.message.reply_text('用法：/maxpain <TICKER> [YYYY-MM-DD]')
        symbol = context.args[0].upper()
        yp = YahooProvider(); expiry = context.args[1] if len(context.args)>1 else yp.nearest_expiry(symbol)
        res = maxpain_handler(symbol, expiry)
        await update.message.reply_text(
            f"🔎 {res['symbol']} {res['expiry']}\n"
            f"📍 Max Pain：{res['max_pain']}\n"
            f"💰 Min Total Pain：${int(res['min_total_pain']):,}"
        )
    except Exception as e:
        await update.message.reply_text(f'錯誤：{e}')

async def gex_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            return await update.message.reply_text('用法：/gex <TICKER> [YYYY-MM-DD]')
        symbol = context.args[0].upper()
        yp = YahooProvider(); expiry = context.args[1] if len(context.args)>1 else yp.nearest_expiry(symbol)
        spot = yp.get_spot(symbol)['price']
        g, s, r = gex_handler(symbol, expiry, spot=spot)
        await update.message.reply_text(
            f'🔎 {symbol} {expiry}\n'
            f'📈 Share Gamma：{g.share_gamma:.2f}\n'
            f'💵 Dollar Gamma (1%)：{g.dollar_gamma_1pct:,.0f}\n'
            f'支撐 {s} | 阻力 {r}'
        )
    except Exception as e:
        await update.message.reply_text(f'錯誤：{e}')

# ---- /ipo：輸出你給的長模板 ----
async def ipo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not context.args:
            return await update.message.reply_text('用法：/ipo <SYMBOL>')
        symbol = context.args[0].upper()
        d = _ipo_detail_template(symbol)
        msg = (
            f"🆕 最新IPO: {d['symbol']}\n"
            f"📅 上市日期: {d['date']}\n"
            f"💰 發行價區間: ${d['range']}\n"
            f"🏢 公司簡介: {d['intro']}\n"
            f"📊 行業: {d['sector']}\n"
            f"💼 主承銷商: {d['underwriter']}\n"
            f"⚠️ 風險提示: {d['risk']}\n\n"
            f"📊 基本面分析:\n"
            f"• 營收成長: {d['fundamentals']['rev_yoy']}\n"
            f"• 毛利率: {d['fundamentals']['gross_margin']}\n"
            f"• 淨利率: {d['fundamentals']['net_margin']}\n"
            f"• 市場規模: {d['fundamentals']['tam']}\n"
            f"• 競爭優勢: {d['fundamentals']['edge']}\n\n"
            f"🎯 估值分析 (AI模型):\n"
            f"• DCF估值: {d['valuation']['dcf']}\n"
            f"• 同業比較: {d['valuation']['comp_pe']}\n"
            f"• 合理價位: {d['valuation']['fair']}\n"
            f"• 上檔目標: {d['valuation']['up']}\n"
            f"• 下檔支撐: {d['valuation']['down']}\n\n"
            f"📈 技術面預測:\n"
            f"• 預期首日波動: {d['technical']['vol_day1']}\n"
            f"• 建議進場點: {d['technical']['entry']}\n"
            f"• 止損設定: {d['technical']['stop']}\n\n"
            f"💡 投資建議:\n"
            f"等級: {d['advice']['rating']}\n"
            f"策略: {d['advice']['strategy']}\n"
            f"風險: {d['advice']['risk']}\n\n"
            f"⏰ 5分鐘深度分析完成\n"
            f"— {BRAND_NAME}"
        )
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f'錯誤：{e}')

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise SystemExit('請設定 TELEGRAM_BOT_TOKEN')
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler('stock', stock_cmd))
    app.add_handler(CommandHandler('maxpain', maxpain_cmd))
    app.add_handler(CommandHandler('gex', gex_cmd))
    app.add_handler(CommandHandler('ipo', ipo_cmd))
    app.run_polling()

if __name__ == '__main__':
    main()
