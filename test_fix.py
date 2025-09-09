#!/usr/bin/env python3
"""
股票機器人修復測試腳本
使用方法: python test_fix.py
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from provider_yahoo import YahooProvider
import logging

# 設定 logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_yahoo_provider():
    """測試 Yahoo Finance Provider"""
    print("🔍 開始測試 Yahoo Finance Provider...")
    print("-" * 50)
    
    provider = YahooProvider()
    
    # 測試股票清單
    test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'INVALID']
    
    success_count = 0
    total_tests = len(test_stocks)
    
    for symbol in test_stocks:
        try:
            print(f"\n📊 測試股票: {symbol}")
            data = provider.get_stock_data(symbol)
            
            print(f"✅ 成功獲取 {symbol} 數據:")
            print(f"   名稱: {data['name']}")
            print(f"   價格: ${data['current_price']:.2f}")
            print(f"   漲跌: {data['change']:+.2f} ({data['change_percent']:+.2f}%)")
            print(f"   數據源: {data['data_source']}")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ {symbol} 測試失敗: {e}")
    
    print(f"\n📈 測試結果: {success_count}/{total_tests} 成功")
    
    if success_count >= 3:  # AAPL, MSFT, GOOGL, TSLA 中至少3個成功
        print("🎉 Provider 測試通過！")
        return True
    else:
        print("⚠️ Provider 測試部分失敗，需要檢查網路連接或API")
        return False

def test_symbol_validation():
    """測試股票代碼驗證"""
    print("\n🔍 開始測試股票代碼驗證...")
    print("-" * 50)
    
    provider = YahooProvider()
    
    test_cases = [
        ('AAPL', True),      # 正常股票
        ('MSFT', True),      # 正常股票
        ('', False),         # 空字符串
        ('TOOLONG', False),  # 太長
        ('12345', False),    # 純數字
        ('AAPL!', False),    # 特殊字符
    ]
    
    for symbol, expected in test_cases:
        result = provider._validate_symbol_format(symbol)
        status = "✅" if result == expected else "❌"
        print(f"{status} {symbol or '(empty)'}: {result} (期望: {expected})")

def test_data_structure():
    """測試數據結構完整性"""
    print("\n🔍 開始測試數據結構...")
    print("-" * 50)
    
    provider = YahooProvider()
    
    try:
        data = provider.get_stock_data('AAPL')
        
        required_fields = [
            'symbol', 'name', 'current_price', 'previous_close',
            'change', 'change_percent', 'volume', 'data_source', 'timestamp'
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
        
        if not missing_fields:
            print("✅ 數據結構完整")
            print("📋 返回的字段:")
            for key, value in data.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ 缺少字段: {missing_fields}")
            
    except Exception as e:
        print(f"❌ 數據結構測試失敗: {e}")

def main():
    """主測試函數"""
    print("🚀 Maggie Stock AI Bot - 修復測試")
    print("=" * 50)
    
    # 檢查模組導入
    try:
        from provider_yahoo import YahooProvider
        print("✅ provider_yahoo 模組導入成功")
    except ImportError as e:
        print(f"❌ provider_yahoo 模組導入失敗: {e}")
        print("請確保文件結構正確且已安裝依賴")
        return False
    
    # 執行測試
    tests = [
        test_symbol_validation,
        test_yahoo_provider,
        test_data_structure
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ 測試 {test_func.__name__} 時發生錯誤: {e}")
    
    print("\n🎯 測試完成!")
    print("如果大部分測試通過，可以部署到 Render")
    print("如果測試失敗，請檢查網路連接和依賴安裝")

if __name__ == "__main__":
    main()
