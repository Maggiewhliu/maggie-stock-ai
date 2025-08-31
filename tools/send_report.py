# tools/send_report.py
import os, asyncio, datetime as dt
import httpx

from src.provider_yahoo import YahooProvider
from src.service import maxpain_handler, gex_handler
from src.analyzers import magnet_strength
from src.strategy import gen_strategy

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # e.g., 123456789
WATCHLIST = [s.strip().upper() for s in os.getenv("WATCHLIST", "AAPL,MSFT,TSLA,NVDA").split(",") if s.strip()]
BRAND_NAME = os.getenv("BRAND_NAME", "Maggie's Stock AI")
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

def _m(v): return "—" if v is None else f"${v:,.2f}"
def _p(v): return "—" if v is None else f"{v:.2f}%"

async def _send_text(text: str):
    if not (BOT_TOKEN and CHAT_ID):
        raise SystemExit("Need TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID for send_report.py")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(url, data={"chat_id": CHAT_ID, "text": text})
        r.raise_for_status()

def _week_range_utc(today=None):
    """回傳本週(一)~(日)的UTC日期字串 (YYYY-MM-DD)。"""
    if today is None:
        today = dt.date.today()
    # 週一=0
    start = today - dt.timedelta(days=today.weekday())
    end = start + dt.timedelta(days=6)
    return start.isoformat(), end.isoformat()

async def _fetch_weekly_ipo_polygon():
    """抓本週 IPO 清單（需要 POLYGON_API_KEY）。"""
    if not POLYGON_API_KEY:
        return None, "（未設定 POLYGON_API_KEY）"
    start, end = _week_range_utc()
    url = (
        "https://api.polygon.io/v3/reference/ipo"
        f"?apiKey={POLYGON_API_KEY}&market=stocks&sort=offer_date&order=asc"
        f"&from={start}&to={end}&limit=50"
    )
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(url)
        r.raise_for_status()
        data = r.json().get("results", [])
    # 精簡欄位
    out = []
    for x in data:
        out.append({
            "ticker": x.get("ticker"),
            "name": x.get("name"),
            "date": x.get("offer_date"),
            "range": x.get("price_range"),
            "underwriters": ", ".join(x.get("underwriters") or []) if isinstance(x.get("underwriters"), list) else (x.get("underwriters") or ""),
            "status": x.get("status"),
        })
    return out, None

async def _build_symbol_block(symbol: str) -> str:
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

    # 市場情緒
    mood = "📊 震盪整理"
    if chg_pct is not None:
        if abs(chg_pct) < 0.3: mood = "📊 震盪整理"
        elif chg_pct >= 0.3:   mood = "📈 上行偏多"
        else:                  mood = "📉 下行偏空"

    # GPT/規則 產生策略（無 OPENAI_API_KEY 會自動走規則版）
    strategy_text = gen_strategy(
        symbol=symbol, spot=spot or mp['max_pain'],
        max_pain=mp['max_pain'], support=support, resistance=resistance
    )

    lines = []
    lines.append(f"📉 {symbol}")
    lines.append(f"💰 即時 {_m(spot)} | 昨收 {_m(prev_close)} | 變動 {_m(chg)} ({_p(chg_pct)})")
    lines.append(mood)
    lines.append("")
    lines.append(f"📍 {symbol}: {_m(spot)} {magnet} (距離: {_m(abs((spot or 0) - mp['max_pain']))})")
    lines.append("")
    lines.append("⚡ Gamma 支撐阻力位")
    lines.append(f"🛡️ {symbol}: 支撐 {_m(support)} | 阻力 {_m(resistance)}")
    lines.append(f"💵 Dollar Gamma (1%): {gex.dollar_gamma_1pct:,.0f}")
    lines.append("")
    lines.append(strategy_text)
    return "\n".join(lines)

async def build_report():
    header = f"📣 Daily US Market Report — {BRAND_NAME}\n"
    date_str = dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    parts = [header + f"⌚ {date_str}\n"]

    for s in WATCHLIST[:12]:
        try:
            block = await _build_symbol_block(s)
        except Exception as e:
            block = f"📉 {s}\n讀取失敗：{e}"
        parts.append(block)
        parts.append("-" * 20)

    # 本週 IPO 段落
    try:
        ipos, err = await _fetch_weekly_ipo_polygon()
        parts.append("🆕 本週 IPO")
        if ipos:
            for x in ipos:
                parts.append(f"• {x['ticker']} — {x.get('name','-')} | {x.get('date','-')} | {x.get('range','-')} | {x.get('status','-')}")
        else:
            parts.append("（本週查無資料或未設定金鑰）" if err else "（本週查無資料）")
    except Exception as e:
        parts.append(f"🆕 本週 IPO：讀取失敗：{e}")

    parts.append(f"\n— {BRAND_NAME}")
    return "\n".join(parts)

async def main():
    text = await build_report()
    await _send_text(text)

if __name__ == "__main__":
    asyncio.run(main())
