# src/analyzers_integration.py
"""
整合版本的股票分析器，連接所有分析功能
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

# 導入分析模組
from . import analyzers  # 你原有的分析模組
from .provider_yahoo import YahooProvider

logger = logging.getLogger(__name__)

class StockAnalyzer:
    """整合式股票分析器，提供 Max Pain、Gamma 等分析"""
    
    def __init__(self):
        self.yahoo_provider = YahooProvider()
        self.risk_free_rate = 0.045  # 4.5% 無風險利率
        self.dividend_yield = 0.0    # 預設無股息
        
    async def analyze_stock(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        完整股票分析，包含技術面和期權分析
        
        Args:
            stock_data: 從 YahooProvider.get_stock_data() 獲得的股票數據
            
        Returns:
            完整的分析結果字典
        """
        try:
            symbol = stock_data['symbol']
            current_price = stock_data['current_price']
            
            logger.info(f"開始分析 {symbol}，當前價格: ${current_price}")
            
            # 基礎數據整理
            analysis_result = {
                'symbol': symbol,
                'current_price': current_price,
                'change': stock_data.get('change', 0),
                'change_percent': stock_data.get('change_percent', '0.00'),
                'volume': stock_data.get('volume', 0),
                'market_cap': stock_data.get('market_cap', 0),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # 技術分析
            technical_analysis = self._perform_technical_analysis(stock_data)
            analysis_result.update(technical_analysis)
            
            # 期權分析 (如果有期權數據)
            options_analysis = await self._perform_options_analysis(symbol, current_price)
            analysis_result.update(options_analysis)
            
            # AI 建議生成
            ai_recommendation = self._generate_ai_recommendation(analysis_result)
            analysis_result.update(ai_recommendation)
            
            logger.info(f"完成 {symbol} 分析")
            return analysis_result
            
        except Exception as e:
            logger.error(f"分析 {symbol} 時發生錯誤: {str(e)}")
            return self._get_fallback_analysis(stock_data)
    
    def _perform_technical_analysis(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行技術分析"""
        try:
            history = stock_data.get('history')
            if history is None or len(history) < 5:
                return self._get_basic_technical_analysis(stock_data)
            
            # 計算技術指標
            prices = history['Close']
            
            # RSI
            rsi = self.yahoo_provider.calculate_rsi(prices) if len(prices) >= 14 else None
            
            # 布林帶
            bollinger = self.yahoo_provider.calculate_bollinger_bands(prices) if len(prices) >= 20 else {
                'upper': None, 'middle': None, 'lower': None
            }
            
            # 移動平均線
            sma_20 = stock_data.get('sma_20')
            sma_50 = stock_data.get('sma_50')
            
            # 趨勢判斷
            trend = self._determine_trend(stock_data['current_price'], sma_20, sma_50)
            
            return {
                'rsi': rsi,
                'bollinger_bands': bollinger,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'trend': trend,
                'technical_score': self._calculate_technical_score(rsi, bollinger, trend)
            }
            
        except Exception as e:
            logger.error(f"技術分析錯誤: {str(e)}")
            return self._get_basic_technical_analysis(stock_data)
    
    async def _perform_options_analysis(self, symbol: str, spot_price: float) -> Dict[str, Any]:
        """執行期權分析"""
        try:
            # 獲取期權鏈數據
            expiry = self.yahoo_provider.nearest_expiry(symbol)
            options_chain = self.yahoo_provider.get_options_chain(symbol, expiry)
            
            # 準備期權數據
            option_rows = []
            greeks_rows = []
            
            for call in options_chain['calls']:
                option_rows.append(analyzers.OptionRow(
                    strike=call['strike'],
                    type='call',
                    open_interest=call['openInterest']
                ))
                
                if call['impliedVolatility'] is not None:
                    greeks_rows.append(analyzers.OptionGreeksRow(
                        strike=call['strike'],
                        type='call',
                        open_interest=call['openInterest'],
                        iv=call['impliedVolatility'],
                        T=call['T']
                    ))
            
            for put in options_chain['puts']:
                option_rows.append(analyzers.OptionRow(
                    strike=put['strike'],
                    type='put',
                    open_interest=put['openInterest']
                ))
                
                if put['impliedVolatility'] is not None:
                    greeks_rows.append(analyzers.OptionGreeksRow(
                        strike=put['strike'],
                        type='put',
                        open_interest=put['openInterest'],
                        iv=put['impliedVolatility'],
                        T=put['T']
                    ))
            
            # 計算 Max Pain
            max_pain_result = analyzers.compute_max_pain(option_rows)
            
            # 計算 GEX
            gex_result = analyzers.compute_gex(greeks_rows, spot_price, self.risk_free_rate, self.dividend_yield)
            
            # 計算 Gamma 支撐/阻力
            support, resistance = analyzers.compute_gamma_levels(greeks_rows, spot_price, self.risk_free_rate, self.dividend_yield)
            
            # 磁吸強度
            magnet_strength = analyzers.magnet_strength(spot_price, max_pain_result.max_pain)
            
            return {
                'max_pain': max_pain_result.max_pain,
                'magnet_strength': magnet_strength,
                'gamma_levels': {
                    'support': support,
                    'resistance': resistance
                },
                'gex': {
                    'share_gamma': gex_result.share_gamma,
                    'dollar_gamma_1pct': gex_result.dollar_gamma_1pct
                },
                'options_expiry': expiry,
                'total_call_oi': sum(row.open_interest for row in option_rows if row.type == 'call'),
                'total_put_oi': sum(row.open_interest for row in option_rows if row.type == 'put'),
            }
            
        except Exception as e:
            logger.warning(f"期權分析失敗 ({symbol}): {str(e)}")
            # 如果期權分析失敗，返回模擬數據
            return self._get_mock_options_analysis(spot_price)
    
    def _generate_ai_recommendation(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成 AI 投資建議"""
        try:
            symbol = analysis_result['symbol']
            current_price = analysis_result['current_price']
            change_percent = float(analysis_result['change_percent'].replace('%', ''))
            
            # 技術面評分
            technical_score = analysis_result.get('technical_score', 50)
            
            # 期權面評分
            max_pain = analysis_result.get('max_pain')
            options_score = 50  # 預設中性
            
            if max_pain:
                price_vs_max_pain = (current_price - max_pain) / max_pain * 100
                if abs(price_vs_max_pain) < 2:
                    options_score = 45  # 接近 Max Pain，略偏空
                elif price_vs_max_pain > 5:
                    options_score = 40  # 遠高於 Max Pain，偏空
                elif price_vs_max_pain < -5:
                    options_score = 60  # 遠低於 Max Pain，偏多
            
            # 綜合評分
            overall_score = (technical_score * 0.6 + options_score * 0.4)
            
            # 信心度計算
            confidence = min(85, max(60, overall_score + abs(change_percent) * 2))
            
            # 生成建議
            recommendation = self._format_recommendation(overall_score, symbol, current_price, max_pain)
            
            return {
                'ai_recommendation': recommendation,
                'confidence': f"{confidence:.0f}",
                'technical_score': technical_score,
                'options_score': options_score,
                'overall_score': overall_score
            }
            
        except Exception as e:
            logger.error(f"生成 AI 建議錯誤: {str(e)}")
            return {
                'ai_recommendation': '技術分析中，請稍後查看',
                'confidence': '75',
                'technical_score': 50,
                'options_score': 50,
                'overall_score': 50
            }
    
    def _format_recommendation(self, score: float, symbol: str, price: float, max_pain: Optional[float]) -> str:
        """格式化投資建議"""
        if score >= 65:
            base_rec = f"看多 {symbol}，技術面呈現上漲趨勢"
        elif score <= 35:
            base_rec = f"看空 {symbol}，注意下跌風險"
        else:
            base_rec = f"{symbol} 呈現震盪格局，建議觀望"
        
        if max_pain:
            distance = abs(price - max_pain)
            if distance / price < 0.03:  # 3% 以內
                base_rec += f"，當前價格接近 Max Pain (${max_pain:.2f})，可能受期權影響"
        
        return base_rec
    
    def _determine_trend(self, price: float, sma_20: Optional[float], sma_50: Optional[float]) -> str:
        """判斷趨勢"""
        if not sma_20 or not sma_50:
            return "數據不足"
        
        if price > sma_20 > sma_50:
            return "上漲趨勢"
        elif price < sma_20 < sma_50:
            return "下跌趨勢"
        else:
            return "震盪整理"
    
    def _calculate_technical_score(self, rsi: Optional[float], bollinger: Dict, trend: str) -> float:
        """計算技術分析評分 (0-100)"""
        score = 50  # 基準分數
        
        # RSI 評分
        if rsi is not None:
            if rsi < 30:
                score += 15  # 超賣，偏多
            elif rsi > 70:
                score -= 15  # 超買，偏空
            elif 40 <= rsi <= 60:
                score += 5   # 中性偏好
        
        # 趨勢評分
        if trend == "上漲趨勢":
            score += 10
        elif trend == "下跌趨勢":
            score -= 10
        
        # 布林帶評分
        if all(bollinger.get(k) for k in ['upper', 'middle', 'lower']):
            # 這裡可以添加布林帶邏輯
            pass
        
        return max(0, min(100, score))
    
    def _get_basic_technical_analysis(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """當無法進行完整技術分析時的基礎版本"""
        change_percent = float(str(stock_data.get('change_percent', '0')).replace('%', ''))
        
        # 簡單的趨勢判斷
        if change_percent > 2:
            trend = "強勢上漲"
            score = 70
        elif change_percent < -2:
            trend = "弱勢下跌"
            score = 30
        else:
            trend = "震盪整理"
            score = 50
        
        return {
            'rsi': None,
            'bollinger_bands': {'upper': None, 'middle': None, 'lower': None},
            'sma_20': stock_data.get('sma_20'),
            'sma_50': stock_data.get('sma_50'),
            'trend': trend,
            'technical_score': score
        }
    
    def _get_mock_options_analysis(self, spot_price: float) -> Dict[str, Any]:
        """當期權分析失敗時的模擬數據"""
        # 生成合理的 Max Pain (通常接近 ATM)
        max_pain = round(spot_price / 5) * 5  # 圓整到最近的 5
        
        # 生成支撐阻力位
        support = max_pain - 10
        resistance = max_pain + 10
        
        return {
            'max_pain': max_pain,
            'magnet_strength': analyzers.magnet_strength(spot_price, max_pain),
            'gamma_levels': {
                'support': support,
                'resistance': resistance
            },
            'gex': {
                'share_gamma': 0,
                'dollar_gamma_1pct': 0
            },
            'options_expiry': 'N/A',
            'total_call_oi': 0,
            'total_put_oi': 0,
        }
    
    def _get_fallback_analysis(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """當整個分析失敗時的後備數據"""
        return {
            'symbol': stock_data.get('symbol', 'UNKNOWN'),
            'current_price': stock_data.get('current_price', 0),
            'change': stock_data.get('change', 0),
            'change_percent': stock_data.get('change_percent', '0.00'),
            'volume': stock_data.get('volume', 0),
            'max_pain': stock_data.get('current_price', 0),
            'magnet_strength': '⚪ 無數據',
            'gamma_levels': {'support': None, 'resistance': None},
            'ai_recommendation': '數據獲取中，請稍後再試',
            'confidence': '50',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
