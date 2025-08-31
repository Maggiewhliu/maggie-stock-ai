# tools/send_report.py
import os, asyncio
import httpx
from src.provider_yahoo import YahooProvider
from src.service import maxpain_handler, gex_handler

BOT_TOKEN = os.getenv("8320641094:AAG1JVdI6BaPLgoUIAYmI3QgymnDG6x3hZE")
CHAT_ID = os.getenv("maggie_ai_stock_bot") 
WATCHLIST = os.getenv("WATCHLIST", "AAPL,MSFT,TSLA,NVDA").split(",")
BRAND_NAME = os.getenv("BRAND_NAME", "Maggie's Stock AI")

def _fmt(v):
    return "—" if v is None else f"${v:,.2f}"

async def build_message():
    yp = YahooProvider()
    lines = [f"📣 Daily US Market Report — {BRAND_NAME}", ""]
    for raw in WATCHLIST[:10]:
        s = raw.strip().upper()
        try:
            q = yp.get_quote(s)
            expiry = yp.nearest_expiry(s)
            mp = maxpain_handler(s, expiry)
            g, sup, res = gex_handler(s, expiry, spot=q.get("price") or 0.0)
            lines.append(f"• {s}  Px:{_fmt(q.get('price'))}  MaxPain:{mp['max_pain']}  "
                         f"GEX±(1%):{g.dollar_gamma_1pct:,.0f}  支撐{_fmt(sup)} / 阻力{_fmt(res)}")
        except Exception as e:
            lines.append(f"• {s}  讀取失敗：{e}")
    return "\n".join(lines)

async def send(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.post(url, data={"chat_id": CHAT_ID, "text": text})
        r.raise_for_status()

async def main():
    if not (BOT_TOKEN and CHAT_ID):
        raise SystemExit("Need TELEGRAM_BOT_TOKEN & TELEGRAM_CHAT_ID")
    msg = await build_message()
    await send(msg)

if __name__ == "__main__":
    asyncio.run(main())
