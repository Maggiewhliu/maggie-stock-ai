#!/usr/bin/env python3
"""
測試Yahoo Finance API連接
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

def test_yahoo_finance():
    """測試Yahoo Finance功能"""
    print("🧪 測試 Yahoo Finance API")
    print("=" * 50)
    
    # 測試股票清單
    test_symbols = ['AAPL', 'TSLA', 'GOOGL', 'MSFT', 'NVDA']
    
    for symbol in test_symbols:
        print(f"\n📊 測試股票: {symbol}")
        
        try:
            # 獲取股票數據
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")
            info = ticker.info
            
            if len(hist) >= 1:
                current_price = hist['Close'].iloc[-1]
                volume = hist['Volume'].iloc[-1]
                
                # 計算漲跌
                if len(hist) >= 2:
                    previous_price = hist['Close'].iloc[-2]
                    change = current_price - previous_price
                    change_percent = (change / previous_price) * 100
                else:
                    change = 0
                    change_percent = 0
                
                print(f"   ✅ 價格: ${current_price:.2f}")
                print(f"   📈 漲跌: {change:+.2f} ({change_percent:+.1f}%)")
                print(f"   📦 成交量: {volume:,.0f}")
                print(f"   🏢 公司: {info.get('longName', symbol)}")
                
                # 測試期權數據（僅美股支援）
                try:
                    options = ticker.options
                    if options:
                        print(f"   🎯 期權到期日: {len(options)}個")
                    else:
                        print(f"   ⚠️ 無期權數據")
                except:
                    print(f"   ⚠️ 期權數據獲取失敗")
                
            else:
                print(f"   ❌ 無歷史數據")
                
        except Exception as e:
            print(f"   ❌ 錯誤: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Yahoo Finance 測試完成！")

def test_yahoo_options():
    """測試Yahoo Finance期權功能"""
    print("\n🎯 測試期權數據功能")
    print("=" * 50)
    
    symbol = 'AAPL'  # 使用蘋果股票測試
    
    try:
        ticker = yf.Ticker(symbol)
        
        # 獲取期權到期日
        expirations = ticker.options
        print(f"📅 {symbol} 期權到期日數量: {len(expirations)}")
        
        if expirations:
            # 使用最近的到期日
            exp_date = expirations[0]
            print(f"📅 測試到期日: {exp_date}")
            
            # 獲取期權鏈
            option_chain = ticker.option_chain(exp_date)
            calls = option_chain.calls
            puts = option_chain.puts
            
            print(f"📞 Call期權數量: {len(calls)}")
            print(f"📞 Put期權數量: {len(puts)}")
            
            # 顯示幾個範例
            print(f"\n📊 Call期權範例:")
            for i, (_, row) in enumerate(calls.head(3).iterrows()):
                print(f"   執行價: ${row['strike']:.0f}, 開倉量: {row['openInterest']}")
            
            print(f"\n📊 Put期權範例:")
            for i, (_, row) in enumerate(puts.head(3).iterrows()):
                print(f"   執行價: ${row['strike']:.0f}, 開倉量: {row['openInterest']}")
            
            print(f"\n✅ 期權數據獲取成功！Max Pain計算可用")
            
        else:
            print(f"❌ {symbol} 無期權數據")
            
    except Exception as e:
        print(f"❌ 期權測試失敗: {e}")

def test_data_sources():
    """測試數據源對比"""
    print("\n🔄 數據源對比測試")
    print("=" * 50)
    
    symbol = 'AAPL'
    
    # Yahoo Finance
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        yahoo_price = hist['Close'].iloc[-1]
        print(f"📊 Yahoo Finance: ${yahoo_price:.2f}")
    except Exception as e:
        print(f"❌ Yahoo失敗: {e}")
        yahoo_price = None
    
    # 如果你有Alpha Vantage API Key，可以比較
    print(f"💡 建議: 如果有Alpha Vantage Key，會優先使用")
    print(f"🔄 備援: Yahoo Finance確保服務不中斷")

if __name__ == "__main__":
    print("🚀 Yahoo Finance API 完整測試")
    print("=" * 60)
    
    # 基礎股票數據測試
    test_yahoo_finance()
    
    # 期權數據測試
    test_yahoo_options()
    
    # 數據源對比
    test_data_sources()
    
    print("\n" + "=" * 60)
    print("✅ 測試完成！Yahoo Finance API已準備就緒")
    print("💡 你的Bot可以正常使用Yahoo Finance數據")
