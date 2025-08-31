import datetime as dt
from typing import Dict, Any
import pandas as pd
import yfinance as yf

def _year_fraction_365(now: dt.datetime, expiry: dt.datetime) -> float:
    return max((expiry - now).total_seconds()/(365.0*24*3600), 0.0)

class YahooProvider:
    def nearest_expiry(self, symbol: str) -> str:
        tk = yf.Ticker(symbol)
        exps = tk.options
        if not exps: raise ValueError(f'No expirations for {symbol}')
        now = pd.Timestamp.utcnow()
        return min(exps, key=lambda d: abs(pd.Timestamp(d) - now))

    def get_spot(self, symbol: str) -> Dict[str, Any]:
        info = yf.Ticker(symbol).fast_info
        return {'symbol': symbol.upper(), 'price': float(info.get('last_price', 0.0))}

    def get_options_chain(self, symbol: str, expiry: str) -> Dict[str, Any]:
        tk = yf.Ticker(symbol)
        exps = tk.options
        if not exps: raise ValueError(f'No options for {symbol}')
        if expiry not in exps:
            expiry = min(exps, key=lambda d: abs(pd.Timestamp(d) - pd.Timestamp(expiry)))
        chain = tk.option_chain(expiry)
        calls, puts = chain.calls.copy(), chain.puts.copy()
        for df in (calls, puts):
            if 'openInterest' not in df: df['openInterest']=0
            df['openInterest'] = df['openInterest'].fillna(0).astype(int)
            df['strike'] = df['strike'].astype(float)
            if 'impliedVolatility' in df: df['impliedVolatility'] = df['impliedVolatility'].astype(float)
        T = _year_fraction_365(dt.datetime.utcnow(), pd.Timestamp(expiry).to_pydatetime())
        def recs(df, typ):
            out=[]
            for _, r in df.iterrows():
                out.append({
                    'type': typ,
                    'strike': float(r['strike']),
                    'openInterest': int(r.get('openInterest',0) or 0),
                    'impliedVolatility': float(r['impliedVolatility']) if 'impliedVolatility' in r and pd.notna(r['impliedVolatility']) else None,
                    'T': T
                })
            return out
        return {'symbol': symbol.upper(), 'expiry': expiry, 'calls': recs(calls,'call'), 'puts': recs(puts,'put')}
