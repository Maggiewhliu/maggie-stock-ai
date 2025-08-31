# src/provider_search.py
import httpx
from typing import List, Dict

YF_SEARCH = "https://query2.finance.yahoo.com/v1/finance/search"

# 常見美股交易所縮寫（Yahoo 的 exchDisp / exchange）
_US_EXCH = {"NYSE", "NASDAQ", "AMEX"}
_US_EXCH_CODES = {"NYQ", "NMS", "NCM", "NGM", "ASE", "PCX"}  # 有些資料用代碼

def _is_us_equity(hit: dict) -> bool:
    qt = (hit.get("quoteType") or "").upper()
    exch = (hit.get("exchDisp") or hit.get("exchange") or "").upper()
    return (qt in {"EQUITY", "ETF", "MUTUALFUND"} and
            (exch in _US_EXCH or exch in _US_EXCH_CODES))

async def yf_search(query: str, limit: int = 10, us_only: bool = True) -> List[Dict]:
    """
    用 Yahoo Finance 搜尋字串（模糊），回傳精簡清單：
    [{symbol, name, exchDisp, type}]
    """
    params = {
        "q": query,
        "quotesCount": limit,
        "newsCount": 0,
        "listsCount": 0,
        "lang": "zh-TW",
        "region": "US",
    }
    async with httpx.AsyncClient(timeout=12) as client:
        r = await client.get(YF_SEARCH, params=params)
        r.raise_for_status()
        data = r.json()

    results = []
    for q in (data.get("quotes") or []):
        if us_only and not _is_us_equity(q):
            continue
        results.append({
            "symbol": q.get("symbol"),
            "name": q.get("shortname") or q.get("longname") or q.get("quoteSourceName") or "",
            "exchDisp": q.get("exchDisp") or q.get("exchange") or "",
            "type": (q.get("quoteType") or "").upper(),
        })
        if len(results) >= limit:
            break
    return results
