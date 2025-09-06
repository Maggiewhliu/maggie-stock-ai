# yahoo_finance.py
import requests
import json
import time
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class YahooFinanceProvider:
    """完整的 Yahoo Finance 數據提供者"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.base_url = "https://query1.finance.yahoo.com"
        self.retry_count = 3
        self.retry_delay = 1
    
    def _make_request(self, url, params=None):
        """發送HTTP請求，包含重試機制"""
        for attempt in range(self.retry_count):
            try:
                response = self.session.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    logger.warning(f"股票代碼不存在: {url}")
                    return None
                else:
                    logger.warning(f"API 請求失敗，狀態碼: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"請求超時，嘗試 {attempt + 1}/{self.retry_count}")
            except requests.exceptions.RequestException as e:
                logger.error(f"請求錯誤: {str(e)}")
            except json.JSONDecodeError:
                logger.error(f"JSON 解析錯誤")
            
            if attempt < self.retry_count - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        return None
    
    def get_basic_info(self, symbol):
        """獲取股票基本資訊"""
        try:
            url = f"{self.base_url}/v8/finance/chart/{symbol}"
            params = {
                'interval': '1d',
                'range': '5d',
                'includePrePost': 'true'
            }
            
            data = self._make_request(url, params)
            
            if not data or 'chart' not in data:
                return None
                
            chart_data = data['chart']
            if not chart_data['result']:
                return None
                
            result = chart_data['result'][0]
            meta = result['meta']
            
            # 基本資訊
            basic_info = {
                'symbol': meta.get('symbol', symbol).upper(),
                'longName': meta.get('longName', symbol),
                'currency': meta.get('currency', 'USD'),
                'exchangeName': meta.get('exchangeName', 'Unknown'),
                'instrumentType': meta.get('instrumentType', 'EQUITY'),
                'firstTradeDate': meta.get('firstTradeDate'),
                'regularMarketTime': meta.get('regularMarketTime'),
                'timezone': meta.get('timezone', 'America/New_York'),
                'exchangeTimezoneName': meta.get('exchangeTimezoneName')
            }
            
            return basic_info
            
        except Exception as e:
            logger.error(f"獲取基本資訊失敗 ({symbol}): {str(e)}")
            return None
    
    def get_price_data(self, symbol, period='5d', interval='1d'):
        """獲取價格數據"""
        try:
            url = f"{self.base_url}/v8/finance/chart/{symbol}"
            params = {
                'interval': interval,
                'range': period,
                'includePrePost': 'true'
            }
            
            data = self._make_request(url, params)
            
            if not data or 'chart' not in data:
                return None
                
            chart_data = data['chart']
            if not chart_data['result']:
                return None
                
            result = chart_data['result'][0]
            meta = result['meta']
            
            # 價格相關數據
            timestamps = result.get('timestamp', [])
            indicators = result.get('indicators', {})
            quote = indicators.get('quote', [{}])[0] if indicators.get('quote') else {}
            
            # 基本價格資訊
            current_price = meta.get('regularMarketPrice')
            previous_close = meta.get('previousClose')
            
            if current_price and previous_close:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100
            else:
                change = None
                change_percent = None
            
            price_data = {
                'symbol': meta.get('symbol', symbol).upper(),
                'current_price': current_price,
                'previous_close': previous_close,
                'change': change,
                'change_percent': change_percent,
                'day_high': meta.get('regularMarketDayHigh'),
                'day_low': meta.get('regularMarketDayLow'),
                'day_volume': meta.get('regularMarketVolume'),
                'fifty_two_week_high': meta.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': meta.get('fiftyTwoWeekLow'),
                'market_cap': meta.get('marketCap'),
                'shares_outstanding': meta.get('sharesOutstanding'),
                'forward_pe': meta.get('forwardPE'),
                'trailing_pe': meta.get('trailingPE'),
                'price_to_book': meta.get('priceToBook'),
                'eps_ttm': meta.get('epsTrailingTwelveMonths'),
                'dividend_yield': meta.get('dividendYield'),
                'ex_dividend_date': meta.get('exDividendDate'),
                'beta': meta.get('beta'),
                'timestamps': timestamps,
                'ohlcv': {
                    'open': quote.get('open', []),
                    'high': quote.get('high', []),
                    'low': quote.get('low', []),
                    'close': quote.get('close', []),
                    'volume': quote.get('volume', [])
                }
            }
            
            return price_data
            
        except Exception as e:
            logger.error(f"獲取價格數據失敗 ({symbol}): {str(e)}")
            return None
    
    def calculate_technical_indicators(self, price_data):
        """計算技術指標"""
        try:
            if not price_data or 'ohlcv' not in price_data:
                return {}
            
            closes = [price for price in price_data['ohlcv']['close'] if price is not None]
            highs = [price for price in price_data['ohlcv']['high'] if price is not None]
            lows = [price for price in price_data['ohlcv']['low'] if price is not None]
            volumes = [vol for vol in price_data['ohlcv']['volume'] if vol is not None]
            
            if len(closes) < 2:
                return {}
            
            indicators = {}
            
            # 移動平均線
            if len(closes) >= 5:
                indicators['sma_5'] = sum(closes[-5:]) / 5
            if len(closes) >= 10:
                indicators['sma_10'] = sum(closes[-10:]) / 10
            if len(closes) >= 20:
                indicators['sma_20'] = sum(closes[-20:]) / 20
            if len(closes) >= 50:
                indicators['sma_50'] = sum(closes[-50:]) / 50
            
            # RSI
            if len(closes) >= 15:
                indicators['rsi'] = self._calculate_rsi(closes)
            
            # MACD
            if len(closes) >= 26:
                macd_data = self._calculate_macd(closes)
                indicators.update(macd_data)
            
            # 支撐阻力位
            if len(highs) >= 5 and len(lows) >= 5:
                indicators['resistance'] = max(highs[-20:]) if len(highs) >= 20 else max(highs)
                indicators['support'] = min(lows[-20:]) if len(lows) >= 20 else min(lows)
            
            # 布林帶
            if len(closes) >= 20:
                bollinger = self._calculate_bollinger_bands(closes)
                indicators.update(bollinger)
            
            # 成交量分析
            if len(volumes) >= 20:
                indicators['avg_volume_20'] = sum(volumes[-20:]) / 20
                if volumes:
                    indicators['volume_ratio'] = volumes[-1] / indicators['avg_volume_20']
            
            return indicators
            
        except Exception as e:
            logger.error(f"計算技術指標失敗: {str(e)}")
            return {}
    
    def _calculate_rsi(self, prices, period=14):
        """計算 RSI"""
        try:
            if len(prices) < period + 1:
                return None
            
            gains = []
            losses = []
            
            for i in range(1, len(prices)):
                change = prices[i] - prices[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            if len(gains) < period:
                return None
            
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
            
            if avg_loss == 0:
                return 100
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return round(rsi, 2)
            
        except Exception:
            return None
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """計算 MACD"""
        try:
            if len(prices) < slow:
                return {}
            
            # 計算 EMA
            def ema(data, period):
                multiplier = 2 / (period + 1)
                ema_values = [data[0]]
                for i in range(1, len(data)):
                    ema_values.append((data[i] * multiplier) + (ema_values[-1] * (1 - multiplier)))
                return ema_values
            
            ema_fast = ema(prices, fast)
            ema_slow = ema(prices, slow)
            
            # MACD 線
            macd_line = []
            for i in range(len(ema_slow)):
                if i < len(ema_fast):
                    macd_line.append(ema_fast[i] - ema_slow[i])
            
            # Signal 線
            if len(macd_line) >= signal:
                signal_line = ema(macd_line, signal)
            else:
                signal_line = []
            
            # Histogram
            histogram = []
            for i in range(min(len(macd_line), len(signal_line))):
                histogram.append(macd_line[i] - signal_line[i])
            
            return {
                'macd': macd_line[-1] if macd_line else None,
                'signal': signal_line[-1] if signal_line else None,
                'histogram': histogram[-1] if histogram else None
            }
            
        except Exception:
            return {}
    
    def _calculate_bollinger_bands(self, prices, period=20, std_dev=2):
        """計算布林帶"""
        try:
            if len(prices) < period:
                return {}
            
            recent_prices = prices[-period:]
            sma = sum(recent_prices) / period
            
            # 計算標準差
            variance = sum([(price - sma) ** 2 for price in recent_prices]) / period
            std = variance ** 0.5
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            return {
                'bb_upper': round(upper_band, 2),
                'bb_middle': round(sma, 2),
                'bb_lower': round(lower_band, 2)
            }
            
        except Exception:
            return {}
    
    def get_options_chain(self, symbol):
        """獲取期權鏈數據"""
        try:
            # 先獲取可用的到期日
            url = f"{self.base_url}/v7/finance/options/{symbol}"
            data = self._make_request(url)
            
            if not data or 'optionChain' not in data:
                return None
            
            option_chain = data['optionChain']
            if not option_chain['result']:
                return None
            
            result = option_chain['result'][0]
            
            # 獲取到期日列表
            expiration_dates = result.get('expirationDates', [])
            if not expiration_dates:
                return None
            
            # 使用最近的到期日
            nearest_expiry = expiration_dates[0]
            
            # 獲取該到期日的期權數據
            url_with_date = f"{url}?date={nearest_expiry}"
            data = self._make_request(url_with_date)
            
            if not data or 'optionChain' not in data:
                return None
            
            result = data['optionChain']['result'][0]
            options_data = result.get('options', [])
            
            if not options_data:
                return None
            
            calls = options_data[0].get('calls', [])
            puts = options_data[0].get('puts', [])
            
            # 期權到期日轉換
            expiry_date = datetime.fromtimestamp(nearest_expiry).strftime('%Y-%m-%d')
            
            options_info = {
                'symbol': symbol.upper(),
                'expiry_date': expiry_date,
                'expiry_timestamp': nearest_expiry,
                'calls': calls,
                'puts': puts,
                'total_call_volume': sum([opt.get('volume', 0) for opt in calls]),
                'total_put_volume': sum([opt.get('volume', 0) for opt in puts]),
                'total_call_oi': sum([opt.get('openInterest', 0) for opt in calls]),
                'total_put_oi': sum([opt.get('openInterest', 0) for opt in puts])
            }
            
            return options_info
            
        except Exception as e:
            logger.error(f"獲取期權鏈失敗 ({symbol}): {str(e)}")
            return None
    
    def calculate_max_pain(self, options_data):
        """計算 Max Pain"""
        try:
            if not options_data:
                return None
            
            calls = options_data.get('calls', [])
            puts = options_data.get('puts', [])
            
            if not calls and not puts:
                return None
            
            # 收集所有執行價
            strikes = set()
            for call in calls:
                if call.get('strike'):
                    strikes.add(call['strike'])
            for put in puts:
                if put.get('strike'):
                    strikes.add(put['strike'])
            
            if not strikes:
                return None
            
            strikes = sorted(strikes)
            min_pain = float('inf')
            max_pain_strike = None
            pain_data = []
            
            for strike in strikes:
                total_pain = 0
                
                # Call 方損失
                for call in calls:
                    if call.get('strike', 0) < strike:
                        pain = (strike - call['strike']) * call.get('openInterest', 0) * 100
                        total_pain += pain
                
                # Put 方損失
                for put in puts:
                    if put.get('strike', 0) > strike:
                        pain = (put['strike'] - strike) * put.get('openInterest', 0) * 100
                        total_pain += pain
                
                pain_data.append({'strike': strike, 'pain': total_pain})
                
                if total_pain < min_pain:
                    min_pain = total_pain
                    max_pain_strike = strike
            
            return {
                'max_pain_strike': max_pain_strike,
                'min_total_pain': min_pain,
                'pain_curve': pain_data
            }
            
        except Exception as e:
            logger.error(f"Max Pain 計算失敗: {str(e)}")
            return None
    
    def get_comprehensive_data(self, symbol):
        """獲取綜合股票數據"""
        try:
            # 基本資訊
            basic_info = self.get_basic_info(symbol)
            if not basic_info:
                return None
            
            # 價格數據
            price_data = self.get_price_data(symbol)
            if not price_data:
                return None
            
            # 技術指標
            technical_indicators = self.calculate_technical_indicators(price_data)
            
            # 期權數據（可選）
            options_data = self.get_options_chain(symbol)
            max_pain_data = None
            if options_data:
                max_pain_data = self.calculate_max_pain(options_data)
            
            # 整合所有數據
            comprehensive_data = {
                'basic_info': basic_info,
                'price_data': price_data,
                'technical_indicators': technical_indicators,
                'options_data': options_data,
                'max_pain_data': max_pain_data,
                'timestamp': datetime.now().isoformat(),
                'data_source': 'Yahoo Finance'
            }
            
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"獲取綜合數據失敗 ({symbol}): {str(e)}")
            return None
    
    def test_connection(self):
        """測試 Yahoo Finance 連接"""
        try:
            test_data = self.get_basic_info("AAPL")
            return test_data is not None
        except Exception:
            return False

# 使用範例
if __name__ == "__main__":
    # 創建提供者實例
    yahoo = YahooFinanceProvider()
    
    # 測試連接
    if yahoo.test_connection():
        print("✅ Yahoo Finance 連接成功")
        
        # 獲取 AAPL 綜合數據
        data = yahoo.get_comprehensive_data("AAPL")
        if data:
            print("✅ 成功獲取 AAPL 數據")
            print(f"當前價格: ${data['price_data']['current_price']}")
            print(f"技術指標數量: {len(data['technical_indicators'])}")
            if data['max_pain_data']:
                print(f"Max Pain: ${data['max_pain_data']['max_pain_strike']}")
        else:
            print("❌ 無法獲取股票數據")
    else:
        print("❌ Yahoo Finance 連接失敗")
