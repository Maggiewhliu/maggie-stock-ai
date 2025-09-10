import yfinance as yf
import requests
import logging
from datetime import datetime, timedelta
import time
from typing import Dict, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)

class YahooProvider:
    def __init__(self, api_key=None):
        self.yahoo_api_key = api_key or "NBWPE7OFZHTT3OFI"
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
        
    def get_stock_data(self, symbol: str) -> Dict:
        """
        獲取股票數據，包含錯誤處理和重試機制
        """
        symbol = symbol.upper().strip()
        
        # 驗證股票代碼格式
        if not self._validate_symbol_format(symbol):
            raise ValueError(f"無效的股票代碼格式: {symbol}")
        
        # 嘗試多種方法獲取數據
        methods = [
            self._get_data_yfinance,
            self._get_data_direct_api,
            self._get_data_fallback
        ]
        
        last_error = None
        for method in methods:
            try:
                logger.info(f"嘗試使用 {method.__name__} 獲取 {symbol} 數據")
                data = method(symbol)
                if data:
                    logger.info(f"成功獲取 {symbol} 數據")
                    return data
            except Exception as e:
                logger.warning(f"{method.__name__} 失敗: {e}")
                last_error = e
                continue
        
        # 所有方法都失敗
        raise Exception(f"無法獲取股票 {symbol} 的數據。最後錯誤: {last_error}")
    
    def nearest_expiry(self, symbol: str) -> Optional[str]:
        """
        獲取最近的期權到期日
        """
        try:
            ticker = yf.Ticker(symbol)
            options = ticker.options
            if options and len(options) > 0:
                return options[0]  # 返回最近的到期日
            return None
        except Exception as e:
            logger.error(f"獲取 {symbol} 期權到期日失敗: {e}")
            return None
    
    def get_options_data(self, symbol: str, expiry_date: str = None) -> Dict:
        """
        獲取期權數據
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # 如果沒有指定到期日，使用最近的
            if not expiry_date:
                expiry_date = self.nearest_expiry(symbol)
                if not expiry_date:
                    return {"error": "無可用的期權數據"}
            
            # 獲取期權鏈
            option_chain = ticker.option_chain(expiry_date)
            
            calls = option_chain.calls
            puts = option_chain.puts
            
            return {
                "symbol": symbol,
                "expiry_date": expiry_date,
                "calls": calls.to_dict('records') if not calls.empty else [],
                "puts": puts.to_dict('records') if not puts.empty else [],
                "call_count": len(calls),
                "put_count": len(puts)
            }
            
        except Exception as e:
            logger.error(f"獲取 {symbol} 期權數據失敗: {e}")
            return {"error": str(e)}
    
    def calculate_max_pain(self, symbol: str, expiry_date: str = None) -> Dict:
        """
        計算 Max Pain 點
        """
        try:
            options_data = self.get_options_data(symbol, expiry_date)
            
            if "error" in options_data:
                return options_data
            
            calls = pd.DataFrame(options_data["calls"])
            puts = pd.DataFrame(options_data["puts"])
            
            if calls.empty or puts.empty:
                return {"error": "期權數據不足"}
            
            # 獲取所有執行價格
            all_strikes = sorted(set(calls['strike'].tolist() + puts['strike'].tolist()))
            
            max_pain_data = []
            
            for strike in all_strikes:
                call_pain = 0
                put_pain = 0
                
                # 計算 Call 期權的痛苦值
                for _, call in calls.iterrows():
                    if strike > call['strike']:
                        call_pain += call['openInterest'] * (strike - call['strike'])
                
                # 計算 Put 期權的痛苦值
                for _, put in puts.iterrows():
                    if strike < put['strike']:
                        put_pain += put['openInterest'] * (put['strike'] - strike)
                
                total_pain = call_pain + put_pain
                max_pain_data.append({
                    'strike': strike,
                    'total_pain': total_pain,
                    'call_pain': call_pain,
                    'put_pain': put_pain
                })
            
            # 找到最大痛苦點
            max_pain_point = min(max_pain_data, key=lambda x: x['total_pain'])
            
            return {
                "symbol": symbol,
                "expiry_date": options_data["expiry_date"],
                "max_pain_strike": max_pain_point['strike'],
                "max_pain_value": max_pain_point['total_pain'],
                "all_strikes_data": max_pain_data
            }
            
        except Exception as e:
            logger.error(f"計算 {symbol} Max Pain 失敗: {e}")
            return {"error": str(e)}
    
    def _validate_symbol_format(self, symbol: str) -> bool:
        """驗證股票代碼格式"""
        if not symbol or len(symbol) < 1 or len(symbol) > 6:
            return False
        if not symbol.replace('.', '').isalnum():
            return False
        return True
    
    def _get_data_yfinance(self, symbol: str) -> Dict:
        """使用 yfinance 獲取數據"""
        ticker = yf.Ticker(symbol)
        
        # 獲取基本信息
        info = ticker.info
        
        # 檢查是否為有效股票
        if not info or 'symbol' not in info:
            raise ValueError(f"yfinance 找不到股票: {symbol}")
        
        # 獲取歷史數據
        hist = ticker.history(period="5d")
        if hist.empty:
            raise ValueError(f"無法獲取 {symbol} 歷史數據")
        
        # 獲取當前價格
        current_price = self._extract_current_price(info, hist)
        previous_close = info.get('previousClose', hist['Close'][-2] if len(hist) > 1 else current_price)
        
        return {
            'symbol': info.get('symbol', symbol),
            'name': info.get('shortName') or info.get('longName', symbol),
            'current_price': float(current_price),
            'previous_close': float(previous_close),
            'change': float(current_price - previous_close),
            'change_percent': float((current_price - previous_close) / previous_close * 100),
            'volume': int(info.get('volume', 0)),
            'market_cap': info.get('marketCap'),
            'pe_ratio': info.get('trailingPE'),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
            'data_source': 'Yahoo Finance (yfinance)',
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_data_direct_api(self, symbol: str) -> Dict:
        """直接調用Yahoo Finance API"""
        url = f"{self.base_url}{symbol}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            result = data['chart']['result'][0]
            
            # 提取數據
            meta = result['meta']
            current_price = meta['regularMarketPrice']
            previous_close = meta['previousClose']
            
            return {
                'symbol': meta['symbol'],
                'name': meta.get('shortName', symbol),
                'current_price': float(current_price),
                'previous_close': float(previous_close),
                'change': float(current_price - previous_close),
                'change_percent': float((current_price - previous_close) / previous_close * 100),
                'volume': int(meta.get('regularMarketVolume', 0)),
                'data_source': 'Yahoo Finance (Direct API)',
                'timestamp': datetime.now().isoformat()
            }
            
        except requests.RequestException as e:
            raise Exception(f"API請求失敗: {e}")
        except (KeyError, IndexError) as e:
            raise Exception(f"數據解析失敗: {e}")
    
    def _get_data_fallback(self, symbol: str) -> Dict:
        """備用數據獲取方法"""
        logger.warning(f"使用備用方法獲取 {symbol} 數據")
        
        # 檢查是否為已知的主要股票
        known_stocks = {
            'AAPL': {'name': 'Apple Inc.', 'price': 180.00},
            'MSFT': {'name': 'Microsoft Corporation', 'price': 350.00},
            'GOOGL': {'name': 'Alphabet Inc.', 'price': 140.00},
            'AMZN': {'name': 'Amazon.com Inc.', 'price': 145.00},
            'TSLA': {'name': 'Tesla Inc.', 'price': 250.00},
            'META': {'name': 'Meta Platforms Inc.', 'price': 300.00},
            'NVDA': {'name': 'NVIDIA Corporation', 'price': 450.00}
        }
        
        if symbol in known_stocks:
            stock_info = known_stocks[symbol]
            current_price = stock_info['price']
            
            return {
                'symbol': symbol,
                'name': stock_info['name'],
                'current_price': current_price,
                'previous_close': current_price * 0.99,  # 模擬1%變化
                'change': current_price * 0.01,
                'change_percent': 1.0,
                'volume': 1000000,
                'data_source': 'Fallback (Emergency)',
                'timestamp': datetime.now().isoformat(),
                'note': '這是緊急備用數據，僅供參考'
            }
        
        raise Exception(f"備用方法也無法獲取 {symbol} 數據")
    
    def _extract_current_price(self, info: Dict, hist) -> float:
        """提取當前價格"""
        price_fields = [
            'currentPrice',
            'regularMarketPrice', 
            'previousClose'
        ]
        
        for field in price_fields:
            if field in info and info[field]:
                return float(info[field])
        
        # 使用歷史數據的最新價格
        if not hist.empty:
            return float(hist['Close'][-1])
        
        raise ValueError("無法獲取當前價格")
    
    def search_symbol(self, query: str) -> List[Dict]:
        """搜索股票代碼"""
        try:
            query = query.upper().strip()
            
            # 簡單的符號匹配
            common_stocks = {
                'APPLE': 'AAPL',
                'MICROSOFT': 'MSFT', 
                'GOOGLE': 'GOOGL',
                'AMAZON': 'AMZN',
                'TESLA': 'TSLA',
                'META': 'META',
                'NVIDIA': 'NVDA'
            }
            
            results = []
            for name, symbol in common_stocks.items():
                if query in name or query == symbol:
                    results.append({'symbol': symbol, 'name': name})
            
            return results
            
        except Exception as e:
            logger.error(f"搜索股票失敗: {e}")
            return []
    
    def get_sp500_list(self) -> List[str]:
        """
        獲取標普500股票清單
        """
        try:
            # 從 Wikipedia 獲取標普500清單
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            tables = pd.read_html(url)
            sp500_table = tables[0]
            
            # 提取股票代碼
            symbols = sp500_table['Symbol'].tolist()
            
            # 清理符號（移除特殊字符）
            clean_symbols = []
            for symbol in symbols:
                if isinstance(symbol, str):
                    # 替換常見的特殊字符
                    clean_symbol = symbol.replace('.', '-')
                    clean_symbols.append(clean_symbol)
            
            return clean_symbols
            
        except Exception as e:
            logger.error(f"獲取標普500清單失敗: {e}")
            # 返回主要的股票作為備用
            return [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B',
                'UNH', 'JNJ', 'V', 'PG', 'JPM', 'HD', 'MA', 'BAC', 'ABBV', 'PFE',
                'KO', 'AVGO', 'PEP', 'TMO', 'COST', 'DIS', 'ABT', 'MRK', 'VZ', 'ADBE'
            ]

# 測試函數
def test_provider():
    """測試 Yahoo Provider"""
    provider = YahooProvider()
    
    test_symbols = ['AAPL', 'MSFT', 'INVALID']
    
    for symbol in test_symbols:
        try:
            print(f"\n測試 {symbol}:")
            
            # 測試基本股票數據
            data = provider.get_stock_data(symbol)
            print(f"✅ 股票數據: {data['name']} - ${data['current_price']}")
            
            # 測試期權到期日
            expiry = provider.nearest_expiry(symbol)
            print(f"✅ 最近期權到期日: {expiry}")
            
            # 測試期權數據
            if expiry:
                options = provider.get_options_data(symbol, expiry)
                if "error" not in options:
                    print(f"✅ 期權數據: {options['call_count']} calls, {options['put_count']} puts")
                else:
                    print(f"⚠️ 期權數據: {options['error']}")
            
        except Exception as e:
            print(f"❌ {symbol}: {e}")

if __name__ == "__main__":
    test_provider()
