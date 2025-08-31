# src/provider_yahoo.py
import datetime as dt
from typing import Dict, Any, List
import pandas as pd
import yfinance as yf

UTC = "UTC"

def _utc_ts(obj) -> pd.Timestamp:
    """Return timezone-aware UTC Timestamp."""
    ts = pd.Timestamp(obj)
    return ts.tz_localize(UTC) if ts.tzinfo is None else ts.tz_convert(UTC)

def _year_fraction_365(now_utc: pd.Timestamp, expiry_utc: pd.Timestamp) -> float:
    return max((expiry_utc - now_utc).total_seconds() / (365.0 * 24 * 3600), 0.0)

class YahooProvider:
    """Thin wrapper around yfinance with safe normalization."""

    # ---------- Quotes ----------
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
