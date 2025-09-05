# src/service.py
"""
核心業務邏輯層
提供 Max Pain、GEX 等分析功能的高級接口
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from .provider_yahoo import YahooProvider
from .analyzers import (
    OptionRow, OptionGreeksRow, 
    compute_max_pain, compute_gex, compute_gamma_levels,
    magnet_strength
)

logger = logging.getLogger(__name__)

class StockService:
    """股票分析服務類"""
    
    def __init__(self):
        self.yahoo_provider = YahooProvider()
        self.risk_free_rate = 0.045  # 4.5% 無風險利率
        self.dividend_yield = 0.0    # 預設無股息
    
    async def get_full_analysis(self, symbol: str, expiry: Optional[str] = None) -> Dict[str, Any]:
        """獲取完整的股票分析"""
        try:
            # 獲取基礎股票數據
            stock_data = await self.yahoo_provider.get_stock_data(symbol)
            if not stock_data:
                raise ValueError(f"無法獲取 {symbol} 的股票數據")
            
            spot_price = stock_data['current_price']
            
            # 獲取期權數據
            if not expiry:
                expiry = self.yahoo_provider.nearest_expiry(symbol)
            
            # Max Pain 分析
            max_pain_result = maxpain_handler(symbol, expiry)
            
            # GEX 分析
            gex_result, support, resistance = gex_handler(symbol, expiry, spot=spot_price)
            
            return {
                'symbol': symbol.upper(),
                'spot_price': spot_price,
                'expiry': expiry,
                'max_pain': max_pain_result,
                'gex': gex_result,
                'gamma_levels': {
                    'support': support,
                    'resistance': resistance
                },
                'magnet_strength': magnet_strength(spot_price, max_pain_result['max_pain']),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"完整分析失敗 ({symbol}): {str(e)}")
            raise

def maxpain_handler(symbol: str, expiry: str) -> Dict[str, Any]:
    """
    Max Pain 分析處理器
    
    Args:
        symbol: 股票代碼
        expiry: 到期日 (YYYY-MM-DD)
        
    Returns:
        Max Pain 分析結果
    """
    try:
        logger.info(f"計算 {symbol} Max Pain，到期日: {expiry}")
        
        # 獲取期權鏈數據
        yahoo_provider = YahooProvider()
        options_chain = yahoo_provider.get_options_chain(symbol, expiry)
        
        # 準備期權數據
        option_rows = []
        
        # 處理 calls
        for call in options_chain['calls']:
            option_rows.append(OptionRow(
                strike=call['strike'],
                type='call',
                open_interest=call['openInterest']
            ))
        
        # 處理 puts
        for put in options_chain['puts']:
            option_rows.append(OptionRow(
                strike=put['strike'],
                type='put',
                open_interest=put['openInterest']
            ))
        
        if not option_rows:
            raise ValueError(f"沒有找到 {symbol} 的期權數據")
        
        # 計算 Max Pain
        max_pain_result = compute_max_pain(option_rows, contract_multiplier=100)
        
        # 格式化結果
        result = {
            'symbol': symbol.upper(),
            'expiry': expiry,
            'max_pain': max_pain_result.max_pain,
            'min_total_pain': max_pain_result.min_total_pain,
            'pain_curve': max_pain_result.curve,
            'total_strikes': len(max_pain_result.curve),
            'total_call_oi': sum(row.open_interest for row in option_rows if row.type == 'call'),
            'total_put_oi': sum(row.open_interest for row in option_rows if row.type == 'put'),
            'contract_multiplier': max_pain_result.contract_multiplier
        }
        
        logger.info(f"Max Pain 計算完成: {symbol} = ${max_pain_result.max_pain}")
        return result
        
    except Exception as e:
        logger.error(f"Max Pain 計算失敗 ({symbol}, {expiry}): {str(e)}")
        raise

def gex_handler(symbol: str, expiry: str, spot: Optional[float] = None) -> Tuple[Dict[str, Any], Optional[float], Optional[float]]:
    """
    GEX (Gamma Exposure) 分析處理器
    
    Args:
        symbol: 股票代碼
        expiry: 到期日 (YYYY-MM-DD)
        spot: 現貨價格，如果不提供會自動獲取
        
    Returns:
        (GEX結果, 支撐位, 阻力位)
    """
    try:
        logger.info(f"計算 {symbol} GEX，到期日: {expiry}")
        
        # 獲取現貨價格
        yahoo_provider = YahooProvider()
        if spot is None:
            spot_data = yahoo_provider.get_spot(symbol)
            spot = spot_data['price']
        
        # 獲取期權鏈數據
        options_chain = yahoo_provider.get_options_chain(symbol, expiry)
        
        # 準備希臘字母數據
        greeks_rows = []
        
        # 處理 calls
        for call in options_chain['calls']:
            if call['impliedVolatility'] is not None and call['impliedVolatility'] > 0:
                greeks_rows.append(OptionGreeksRow(
                    strike=call['strike'],
                    type='call',
                    open_interest=call['openInterest'],
                    iv=call['impliedVolatility'],
                    T=call['T']
                ))
        
        # 處理 puts
        for put in options_chain['puts']:
            if put['impliedVolatility'] is not None and put['impliedVolatility'] > 0:
                greeks_rows.append(OptionGreeksRow(
                    strike=put['strike'],
                    type='put',
                    open_interest=put['openInterest'],
                    iv=put['impliedVolatility'],
                    T=put['T']
                ))
        
        if not greeks_rows:
            logger.warning(f"沒有找到 {symbol} 的有效 IV 數據，使用零值")
            gex_result = type('GEXResult', (), {
                'share_gamma': 0.0,
                'dollar_gamma_1pct': 0.0
            })()
            support, resistance = None, None
        else:
            # 計算 GEX
            risk_free_rate = 0.045
            dividend_yield = 0.0
            
            gex_result = compute_gex(greeks_rows, spot, risk_free_rate, dividend_yield, contract_multiplier=100)
            
            # 計算 Gamma 支撐/阻力位
            support, resistance = compute_gamma_levels(greeks_rows, spot, risk_free_rate, dividend_yield, contract_multiplier=100)
        
        # 格式化 GEX 結果
        gex_dict = {
            'symbol': symbol.upper(),
            'expiry': expiry,
            'spot_price': spot,
            'share_gamma': gex_result.share_gamma,
            'dollar_gamma_1pct': gex_result.dollar_gamma_1pct,
            'total_options': len(greeks_rows)
        }
        
        logger.info(f"GEX 計算完成: {symbol} ShareGamma={gex_result.share_gamma:.2f}")
        return gex_dict, support, resistance
        
    except Exception as e:
        logger.error(f"GEX 計算失敗 ({symbol}, {expiry}): {str(e)}")
        raise

def options_summary(symbol: str, expiry: Optional[str] = None) -> Dict[str, Any]:
    """
    期權數據摘要
    
    Args:
        symbol: 股票代碼
        expiry: 到期日，如果不提供會使用最近的到期日
        
    Returns:
        期權摘要數據
    """
    try:
        yahoo_provider = YahooProvider()
        
        # 獲取到期日
        if not expiry:
            expiry = yahoo_provider.nearest_expiry(symbol)
        
        # 獲取現貨價格
        spot_data = yahoo_provider.get_spot(symbol)
        spot_price = spot_data['price']
        
        # 獲取期權鏈
        options_chain = yahoo_provider.get_options_chain(symbol, expiry)
        
        # 統計期權數據
        calls = options_chain['calls']
        puts = options_chain['puts']
        
        total_call_oi = sum(call['openInterest'] for call in calls)
        total_put_oi = sum(put['openInterest'] for put in puts)
        
        # 找到 ATM 期權
        atm_strike = min(calls + puts, key=lambda x: abs(x['strike'] - spot_price))['strike']
        
        # Put/Call 比率
        pc_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else 0
        
        return {
            'symbol': symbol.upper(),
            'expiry': expiry,
            'spot_price': spot_price,
            'atm_strike': atm_strike,
            'total_call_oi': total_call_oi,
            'total_put_oi': total_put_oi,
            'put_call_ratio': pc_ratio,
            'total_contracts': len(calls) + len(puts),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"期權摘要失敗 ({symbol}): {str(e)}")
        raise

def market_sentiment_analysis(symbol: str) -> Dict[str, Any]:
    """
    基於期權數據的市場情緒分析
    
    Args:
        symbol: 股票代碼
        
    Returns:
        市場情緒分析結果
    """
    try:
        # 獲取期權摘要
        summary = options_summary(symbol)
        
        # 分析情緒指標
        pc_ratio = summary['put_call_ratio']
        
        # Put/Call 比率解讀
        if pc_ratio > 1.2:
            sentiment = "極度看空"
            sentiment_score = 20
        elif pc_ratio > 0.8:
            sentiment = "看空"
            sentiment_score = 35
        elif pc_ratio > 0.6:
            sentiment = "略微看空"
            sentiment_score = 45
        elif pc_ratio > 0.4:
            sentiment = "中性"
            sentiment_score = 50
        elif pc_ratio > 0.3:
            sentiment = "略微看多"
            sentiment_score = 60
        else:
            sentiment = "看多"
            sentiment_score = 75
        
        # 獲取 Max Pain 數據進行綜合分析
        try:
            max_pain_data = maxpain_handler(symbol, summary['expiry'])
            spot_price = summary['spot_price']
            max_pain = max_pain_data['max_pain']
            
            # Max Pain 距離分析
            distance_pct = (spot_price - max_pain) / max_pain * 100
            
            if abs(distance_pct) < 2:
                max_pain_sentiment = "中性（接近Max Pain）"
            elif distance_pct > 5:
                max_pain_sentiment = "看空（遠高於Max Pain）"
            elif distance_pct < -5:
                max_pain_sentiment = "看多（遠低於Max Pain）"
            else:
                max_pain_sentiment = "中性"
                
        except Exception:
            max_pain_sentiment = "無法計算"
            distance_pct = 0
        
        return {
            'symbol': symbol.upper(),
            'overall_sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'put_call_ratio': pc_ratio,
            'pc_interpretation': f"Put/Call比率 {pc_ratio:.2f}",
            'max_pain_sentiment': max_pain_sentiment,
            'max_pain_distance_pct': distance_pct,
            'analysis_time': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"市場情緒分析失敗 ({symbol}): {str(e)}")
        raise

# 向後兼容的函數別名
def get_maxpain(symbol: str, expiry: str) -> Dict[str, Any]:
    """向後兼容的 Max Pain 函數"""
    return maxpain_handler(symbol, expiry)

def get_gex(symbol: str, expiry: str, spot: Optional[float] = None) -> Tuple[Dict[str, Any], Optional[float], Optional[float]]:
    """向後兼容的 GEX 函數"""
    return gex_handler(symbol, expiry, spot)
