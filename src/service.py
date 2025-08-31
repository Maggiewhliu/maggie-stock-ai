import time
from typing import List, Tuple, Optional
from src.provider_yahoo import YahooProvider
from src.cache import get_json, set_json, lock
from src.analyzers import (
    OptionRow, OptionGreeksRow, compute_max_pain, compute_gex,
    compute_gamma_levels
)

def get_option_chain_cached(symbol: str, expiry: str, ttl=900) -> dict:
    key=f'v1:options:{symbol}:{expiry}'
    data=get_json(key)
    if data and (time.time()-data.get('fetched_at',0))<ttl:
        return data
    with lock(key, ttl=30):
        data=get_json(key)
        if data and (time.time()-data.get('fetched_at',0))<ttl:
            return data
        raw=YahooProvider().get_options_chain(symbol, expiry)
        payload={'fetched_at': time.time(), 'data': raw, 'source':'yahoo'}
        set_json(key, payload, ttl=ttl)
        return payload

def maxpain_handler(symbol: str, expiry: str):
    oc=get_option_chain_cached(symbol, expiry)
    rows: List[OptionRow]=[]
    for r in oc['data']['calls']: rows.append(OptionRow(r['strike'],'call',r.get('openInterest',0) or 0))
    for r in oc['data']['puts']:  rows.append(OptionRow(r['strike'],'put', r.get('openInterest',0) or 0))
    mp=compute_max_pain(rows, contract_multiplier=100)
    return {'symbol': symbol.upper(), 'expiry': oc['data']['expiry'], 'max_pain': mp.max_pain, 'min_total_pain': mp.min_total_pain}

def gex_handler(symbol: str, expiry: str, spot: float, r: float=0.045, q: float=0.0):
    oc=get_option_chain_cached(symbol, expiry)
    rows: List[OptionGreeksRow]=[]
    for src, ttype in (('calls','call'),('puts','put')):
        for rr in oc['data'][src]:
            rows.append(OptionGreeksRow(rr['strike'], ttype, rr.get('openInterest',0) or 0, rr.get('impliedVolatility'), rr.get('T',0.0)))
    gex = compute_gex(rows, spot=spot, r=r, q=q, contract_multiplier=100)
    support, resistance = compute_gamma_levels(rows, spot=spot, r=r, q=q, contract_multiplier=100)
    return gex, support, resistance
