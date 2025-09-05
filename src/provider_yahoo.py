# src/provider_yahoo.py
import datetime as dt
from typing import Dict, Any, List, Optional
import pandas as pd
import yfinance as yf
import asyncio
import logging

UTC = "UTC"
logger = logging.getLogger(__name__)

def _utc_ts(obj) -> pd.Timestamp:
    """Return timezone-aware UTC Timestamp."""
    ts = pd.Timestamp(obj)
    return ts.tz_localize(UTC) if ts.tzinfo is None else ts.tz_convert(UTC)

def _year_fraction_365(now_utc: pd.Timestamp, expiry_utc: pd.Timestamp) -> float:
    return max((expiry_utc - now_utc).total_seconds() / (365.0 * 24 * 3600), 0.0)

class YahooProvider:
    """Thin wrapper around yfinance with safe normalization."""

    def __init__(self):
        """初始化 Yahoo Finance 提供者"""
        self.cache = {}  # 簡單的內存快取
        self.cache_timeout = 300  # 5分鐘快取
    
    # ---------- 新增：Bot所需的核心方法 ----------
    async def get_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        獲取股票完整數據，用於 bot.py
        返回格式化的股票數據字典
        """
        try:
            # 使用 asyncio 運行同步函數
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._fetch_stock_data, symbol)
            return result
        except Exception as e:
            logger.error(f"獲取 {symbol} 股票數據失敗: {str(e)}")
            return None
    
    def _fetch_stock_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """同步獲取股票數據的實際實現"""
        try:
            ticker = yf.Ticker(symbol)
            
            # 獲取基本報價資訊
            quote_data = self.get_quote(symbol)
            if not quote_data or quote_data.get('price') is None:
                logger.warning(f"無法獲取 {symbol} 的價格數據")
                return None
            
            # 獲取詳細資訊
            info = ticker.info or {}
            hist = ticker.history(period="5d")
            
            # 計算技術指標
            volume = 0
            if len(hist) > 0:
                volume = int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0
            
            # 獲取市值等資訊
            market_cap = info.get('marketCap', 0)
            pe_ratio = info.get('trailingPE', None)
            
            # 計算移動平均線
            sma_20 = None
            sma_50 = None
            if len(hist) >= 20:
                sma_20 = float(hist['Close'].rolling(20).mean().iloc[-1])
            if len(hist) >= 50:
                sma_50 = float(hist['Close'].rolling(50).mean().iloc[-1])
            
            # 構建返回數據
            stock_data = {
                'symbol': symbol.upper(),
                'current_price': quote_data.get('price'),
                'previous_close': quote_data.get('previous_close'),
                'change': quote_data.get('change'),
                'change_percent': f"{quote_data.get('change_pct', 0):.2f}" if quote_data.get('change_pct') else "0.00",
                'volume': volume,
                'market_cap': market_cap,
                'pe_ratio': pe_ratio,
                'currency': quote_data.get('currency', 'USD'),
                'sma_20': sma_20,
                'sma_50': sma_50,
                'company_name': info.get('longName', symbol),
                'sector': info.get('sector', '未知'),
                'industry': info.get('industry', '未知'),
                'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S'),
                'raw_info': info,  # 保留原始資訊供其他分析使用
                'history': hist   # 保留歷史數據供技術分析使用
            }
            
            logger.info(f"成功獲取 {symbol} 股票數據")
            return stock_data
            
        except Exception as e:
            logger.error(f"獲取 {symbol} 股票數據時發生錯誤: {str(e)}")
            return None
    
    async def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """批量獲取多個股票的報價"""
        results = {}
        tasks = []
        
        for symbol in symbols:
            task = self.get_stock_data(symbol)
            tasks.append((symbol, task))
        
        for symbol, task in tasks:
            try:
                data = await task
                if data:
                    results[symbol] = data
            except Exception as e:
                logger.error(f"批量獲取 {symbol} 失敗: {str(e)}")
                results[symbol] = None
        
        return results
    
    # ---------- 技術分析輔助方法 ----------
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> Optional[float]:
        """計算 RSI 指標"""
        try:
            if len(prices) < period + 1:
                return None
            
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return float(rsi.iloc[-1]) if not rsi.empty else None
        except Exception as e:
            logger.error(f"計算 RSI 失敗: {str(e)}")
            return None
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, Optional[float]]:
        """計算布林帶"""
        try:
            if len(prices) < period:
                return {'upper': None, 'middle': None, 'lower': None}
            
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            
            upper = sma + (std * std_dev)
            lower = sma - (std * std_dev)
            
            return {
                'upper': float(upper.iloc[-1]) if not upper.empty else None,
                'middle': float(sma.iloc[-1]) if not sma.empty else None,
                'lower': float(lower.iloc[-1]) if not lower.empty else None
            }
        except Exception as e:
            logger.error(f"計算布林帶失敗: {str(e)}")
            return {'upper': None, 'middle': None, 'lower': None}

    # ---------- 原有方法保持不變 ----------
    def get_spot(self, symbol: str) -> Dict[str, Any]:
        """Return last price (best-effort)."""
        t = yf.Ticker(symbol)
        info = t.fast_info or {}
        price = info.get("last_price", None)
        if price is None:
            # fallback to latest close
            try:
                h = t.history(period="1d")
                if len(h) > 0:
                    price = float(h["Close"].iloc[-1])
            except Exception:
                price = 0.0
        return {"symbol": symbol.upper(), "price": float(price or 0.0)}

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Return price / previous_close / change / change_pct / currency (best-effort)."""
        t = yf.Ticker(symbol)
        info = t.fast_info or {}
        currency = info.get("currency") or "USD"

        price = info.get("last_price", None)
        prev_close = info.get("previous_close", None)

        # fallbacks
        try:
            if prev_close is None:
                h = t.history(period="2d")
                if len(h) >= 2:
                    prev_close = float(h["Close"].iloc[-2])
        except Exception:
            prev_close = None
        try:
            if price is None:
                h = t.history(period="1d")
                if len(h) >= 1:
                    price = float(h["Close"].iloc[-1])
        except Exception:
            price = None

        chg = None
        chg_pct = None
        if price is not None and prev_close not in (None, 0):
            chg = float(price) - float(prev_close)
            chg_pct = (chg / float(prev_close)) * 100.0

        return {
            "symbol": symbol.upper(),
            "price": float(price) if price is not None else None,
            "previous_close": float(prev_close) if prev_close is not None else None,
            "change": float(chg) if chg is not None else None,
            "change_pct": float(chg_pct) if chg_pct is not None else None,
            "currency": currency,
        }

    # ---------- Expirations ----------
    def _list_expirations(self, symbol: str) -> List[str]:
        exps = yf.Ticker(symbol).options or []
        return [str(x) for x in exps]

    def nearest_expiry(self, symbol: str) -> str:
        """
        Pick the nearest *upcoming* expiry (>= now). If all are in the past,
        fallback to the absolute-closest one.
        Always return YYYY-MM-DD.
        """
        exps = self._list_expirations(symbol)
        if not exps:
            raise ValueError(f"No expirations for {symbol}")
        now = _utc_ts(pd.Timestamp.utcnow())

        upcoming, past = [], []
        for d in exps:
            ts = _utc_ts(d)
            (upcoming if ts >= now else past).append(ts)

        if upcoming:
            target = min(upcoming, key=lambda ts: ts - now)
        else:
            target = min(past, key=lambda ts: abs(ts - now))

        return str(target.date())

    # ---------- Options chain ----------
    def get_options_chain(self, symbol: str, expiry: str) -> Dict[str, Any]:
        """
        Return normalized options chain:
        {
          symbol, expiry,
          calls: [{type, strike, openInterest, impliedVolatility, T}],
          puts:  [{...}],
        }
        """
        tk = yf.Ticker(symbol)
        exps = self._list_expirations(symbol)
        if not exps:
            raise ValueError(f"No options for {symbol}")

        # snap expiry to closest available
        if expiry not in exps:
            exp_target = _utc_ts(expiry)
            expiry = min(exps, key=lambda d: abs(_utc_ts(d) - exp_target))

        chain = tk.option_chain(expiry)
        calls = chain.calls.copy()
        puts = chain.puts.copy()

        for df in (calls, puts):
            if "openInterest" not in df:
                df["openInterest"] = 0
            df["openInterest"] = df["openInterest"].fillna(0).astype(int)
            df["strike"] = df["strike"].astype(float)
            if "impliedVolatility" in df:
                df["impliedVolatility"] = pd.to_numeric(df["impliedVolatility"], errors="coerce")

        now = _utc_ts(pd.Timestamp.utcnow())
        exp_ts = _utc_ts(expiry)
        T = _year_fraction_365(now, exp_ts)

        def recs(df, typ):
            out = []
            for _, r in df.iterrows():
                out.append(
                    {
                        "type": typ,
                        "strike": float(r["strike"]),
                        "openInterest": int(r.get("openInterest", 0) or 0),
                        "impliedVolatility": float(r["impliedVolatility"])
                        if ("impliedVolatility" in r and pd.notna(r["impliedVolatility"]))
                        else None,
                        "T": float(T),
                    }
                )
            return out

        return {
            "symbol": symbol.upper(),
            "expiry": str(exp_ts.date()),
            "calls": recs(calls, "call"),
            "puts": recs(puts, "put"),
        }
    
    # ---------- 測試方法 ----------
    def test_connection(self) -> bool:
        """測試 Yahoo Finance 連接"""
        try:
            test_data = self.get_quote("AAPL")
            return test_data.get('price') is not None
        except Exception as e:
            logger.error(f"Yahoo Finance 連接測試失敗: {str(e)}")
            return False

if __name__ == "__main__":
    # 測試代碼
    import asyncio
    
    async def test():
        provider = YahooProvider()
        
        # 測試連接
        print("測試 Yahoo Finance 連接...")
        if provider.test_connection():
            print("✅ 連接成功")
        else:
            print("❌ 連接失敗")
            return
        
        # 測試獲取股票數據
        print("\n測試獲取 TSLA 數據...")
        data = await provider.get_stock_data("TSLA")
        if data:
            print(f"✅ 成功獲取 TSLA 數據:")
            print(f"   價格: ${data['current_price']}")
            print(f"   變動: {data['change']} ({data['change_percent']}%)")
            print(f"   成交量: {data['volume']:,}")
        else:
            print("❌ 獲取數據失敗")
    
    # 運行測試
    asyncio.run(test())
