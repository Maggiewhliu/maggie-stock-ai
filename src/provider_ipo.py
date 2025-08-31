# src/provider_ipo.py
import os, datetime as dt, httpx

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

class IPOProvider:
    """IPO 資料來源：Polygon.io。"""

    async def _polygon_list_recent(self, days: int = 540):
        if not POLYGON_API_KEY:
            return []
        today = dt.date.today()
        start = today - dt.timedelta(days=days)
        url = ("https://api.polygon.io/v3/reference/ipo"
               f"?apiKey={POLYGON_API_KEY}&market=stocks&sort=offer_date&order=desc"
               f"&from={start}&to={today}&limit=1000")
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(url); r.raise_for_status()
            return r.json().get("results", []) or []

    async def _polygon_ticker_meta(self, symbol: str):
        if not POLYGON_API_KEY:
            return None
        url = f"https://api.polygon.io/v3/reference/tickers/{symbol.upper()}?apiKey={POLYGON_API_KEY}"
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(url); r.raise_for_status()
            return r.json().get("results")

    async def get_ipo(self, symbol: str):
        """優先從近 540 天 IPO 清單找；找不到再用 tickers meta 補上市日。"""
        sym = symbol.upper()
        # 1) 近 540 天清單
        try:
            recents = await self._polygon_list_recent(days=540)
            for item in recents:
                if item.get("ticker", "").upper() == sym:
                    return {
                        "symbol": sym,
                        "name": item.get("name") or sym,
                        "date": item.get("offer_date"),
                        "range": item.get("price_range") or "-",
                        "underwriters": ", ".join(item.get("underwriters") or []) if isinstance(item.get("underwriters"), list) else (item.get("underwriters") or "-"),
                        "status": item.get("status") or "-",
                        "notes": item.get("notes") or "",
                    }
        except Exception:
            pass

        # 2) 時間太久的 IPO（例如 ARM 2023）→ 用 tickers meta 的 list_date
        try:
            meta = await self._polygon_ticker_meta(sym)
            if meta:
                return {
                    "symbol": sym,
                    "name": meta.get("name") or sym,
                    "date": meta.get("list_date") or meta.get("updated_utc", "")[:10],
                    "range": "-",
                    "underwriters": "-",
                    "status": meta.get("active") and "Active" or "Delisted",
                    "notes": "",
                }
        except Exception:
            pass

        # 3) 無金鑰或完全找不到 → None（由 bot 顯示模板）
        return None
