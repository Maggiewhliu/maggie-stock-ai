# src/provider_ipo.py
import os, datetime as dt, httpx

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

class IPOProvider:
    """
    優先用 Polygon.io（有免費 tier）。若無 API key，回傳 None 讓 bot 用模板回覆。
    Docs: https://polygon.io/docs/stocks/get_v3_reference_ipo
    """

    @staticmethod
    async def fetch_polygon(symbol: str):
        if not POLYGON_API_KEY:
            return None
        # Polygon 的 IPO endpoint 是「依日期查列表」，此處簡化為按 symbol 搜索近 180 天內的 IPO 清單
        today = dt.date.today()
        start = today - dt.timedelta(days=180)
        url = ("https://api.polygon.io/v3/reference/ipo"
               f"?apiKey={POLYGON_API_KEY}&market=stocks&sort=offer_date&order=desc"
               f"&limit=100&from={start}&to={today}")
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json().get("results", [])
        symbol = symbol.upper()
        for item in data:
            # 常見欄位：ticker, name, offer_date, price_range, underwriters, status
            if item.get("ticker","").upper() == symbol:
                return {
                    "symbol": symbol,
                    "name": item.get("name") or symbol,
                    "date": item.get("offer_date"),
                    "range": item.get("price_range") or "-",
                    "underwriters": ", ".join(item.get("underwriters") or []) or "-",
                    "status": item.get("status") or "-",
                    "notes": item.get("notes") or "",
                }
        return None

    async def get_ipo(self, symbol: str):
        # 目前只實作 Polygon；日後可擴充 Nasdaq/Finnhub 以 adapter 形式加進來
        res = await self.fetch_polygon(symbol)
        return res
