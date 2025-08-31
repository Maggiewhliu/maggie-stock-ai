import math
from dataclasses import dataclass
from typing import Iterable, Literal, Optional, Tuple, List, Dict
from math import log, sqrt, exp

# ---------- Black–Scholes & IV ----------
def _phi(x): return math.exp(-0.5*x*x)/math.sqrt(2*math.pi)
def _Phi(x): return 0.5*(1+math.erf(x/math.sqrt(2)))

def bs_price(S, K, r, q, sigma, T, opt_type: str):
    if sigma <= 0 or T <= 0:
        fwd = S*exp(-q*T) - K*exp(-r*T)
        return max(0.0, fwd) if opt_type == 'call' else max(0.0, -fwd)
    d1 = (log(S/K)+(r-q+0.5*sigma*sigma)*T)/(sigma*sqrt(T))
    d2 = d1 - sigma*sqrt(T)
    return S*exp(-q*T)*_Phi(d1) - K*exp(-r*T)*_Phi(d2) if opt_type=='call' \
        else K*exp(-r*T)*_Phi(-d2) - S*exp(-q*T)*_Phi(-d1)

def bs_gamma(S, K, r, q, sigma, T):
    if sigma <= 0 or T <= 0 or S <= 0: return 0.0
    d1 = (log(S/K)+(r-q+0.5*sigma*sigma)*T)/(sigma*sqrt(T))
    return exp(-q*T) * _phi(d1) / (S * sigma * sqrt(T))

def implied_vol_from_price(S, K, r, q, T, price, opt_type,
                           lo=1e-4, hi=5.0, tol=1e-6, max_iter=100):
    def f(sig): return bs_price(S,K,r,q,sig,T,opt_type) - price
    a, b = lo, hi; fa, fb = f(a), f(b)
    if fa*fb > 0: return None
    for _ in range(max_iter):
        m = 0.5*(a+b); fm = f(m)
        if abs(fm) < tol or (b-a)/2 < tol: return max(m, lo)
        if fa*fm <= 0: b, fb = m, fm
        else: a, fa = m, fm
    return None

# ---------- Max Pain ----------
OptionType = Literal['call','put']

@dataclass(frozen=True)
class OptionRow:
    strike: float
    type: OptionType
    open_interest: int

@dataclass(frozen=True)
class MaxPainResult:
    max_pain: float
    min_total_pain: float
    curve: List[Tuple[float, float]]
    contract_multiplier: int

def compute_max_pain(options: Iterable[OptionRow], contract_multiplier: int=100) -> MaxPainResult:
    calls, puts = {}, {}
    for r in options:
        s = float(r.strike); oi = int(max(0, r.open_interest))
        (calls if r.type=='call' else puts)[s] = (calls if r.type=='call' else puts).get(s,0)+oi
    strikes = sorted(set(calls.keys())|set(puts.keys()))
    if not strikes: raise ValueError('No strikes')
    curve=[]
    for K in strikes:
        call_payout = sum((K-s)*oi for s,oi in calls.items() if s<K)
        put_payout  = sum((s-K)*oi for s,oi in puts.items()  if s>K)
        curve.append((K, float((call_payout+put_payout)*contract_multiplier)))
    K_star, min_pain = min(curve, key=lambda x:x[1])
    return MaxPainResult(max_pain=K_star, min_total_pain=min_pain, curve=curve, contract_multiplier=contract_multiplier)

# ---------- GEX ----------
@dataclass(frozen=True)
class OptionGreeksRow:
    strike: float
    type: Literal['call','put']
    open_interest: int
    iv: Optional[float]
    T: float

@dataclass(frozen=True)
class GEXResult:
    share_gamma: float
    dollar_gamma_1pct: float

def compute_gex(rows: Iterable[OptionGreeksRow], spot: float, r: float, q: float, contract_multiplier: int=100) -> GEXResult:
    g_shares = 0.0
    for r0 in rows:
        if r0.iv is None or r0.iv <= 0 or r0.T <= 0: continue
        gamma = bs_gamma(spot, r0.strike, r, q, r0.iv, r0.T)
        g_shares += gamma * r0.open_interest * contract_multiplier
    g_dollar_1pct = g_shares * 0.01 * spot * spot
    return GEXResult(share_gamma=g_shares, dollar_gamma_1pct=g_dollar_1pct)

# ---------- Gamma 支撐/阻力（實用 heuristics） ----------
def compute_gamma_levels(rows: Iterable[OptionGreeksRow], spot: float, r: float, q: float, contract_multiplier: int=100):
    """把 call gamma 視為 +、put gamma 視為 -，聚合到各 strike。
       找到最靠近現價的符號翻轉點，作為支撐/阻力；若沒有就取最接近的上下 strike。"""
    by_strike: Dict[float, float] = {}
    for r0 in rows:
        if r0.iv is None or r0.iv <= 0 or r0.T <= 0: continue
        g = bs_gamma(spot, r0.strike, r, q, r0.iv, r0.T) * r0.open_interest * contract_multiplier
        by_strike[r0.strike] = by_strike.get(r0.strike, 0.0) + (g if r0.type=='call' else -g)
    if not by_strike: return None, None
    strikes = sorted(by_strike.keys())
    below = [k for k in strikes if k <= spot]
    above = [k for k in strikes if k >= spot]
    support = None
    for i in range(len(below)-1, 0, -1):
        if by_strike[below[i]]*by_strike[below[i-1]] <= 0: support = below[i]; break
    resistance = None
    for i in range(0, len(above)-1):
        if by_strike[above[i]]*by_strike[above[i+1]] <= 0: resistance = above[i]; break
    if support is None and below: support = below[-1]
    if resistance is None and above: resistance = above[0]
    return support, resistance

def magnet_strength(spot: float, max_pain: float) -> str:
    d = abs(spot - max_pain)
    return "🟢 強磁吸" if d < 3 else ("🟡 中等磁吸" if d < 10 else "⚪ 弱磁吸")
