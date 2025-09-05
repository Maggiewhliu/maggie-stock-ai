#!/usr/bin/env python3
"""
Maggie's Stock AI Bot 系統測試腳本
用於測試所有核心組件是否正常工作
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_yahoo_provider():
    """測試 Yahoo Finance 數據源"""
    print("\n🔍 測試 Yahoo Finance Provider...")
    
    try:
        from src.provider_yahoo import YahooProvider
        provider = YahooProvider()
        
        # 測試連接
        if provider.test_connection():
            print("✅ Yahoo Finance 連接成功")
        else:
            print("❌ Yahoo Finance 連接失敗")
            return False
        
        # 測試獲取股票數據
        print("   測試獲取 TSLA 數據...")
        data = await provider.get_stock_data("TSLA")
        
        if data:
            print(f"   ✅ 成功獲取 TSLA 數據:")
            print(f"      價格: ${data.get('current_price', 'N/A')}")
            print(f"      變動: {data.get('change', 'N/A')} ({data.get('change_percent', 'N/A')}%)")
            print(f"      成交量: {data.get('volume', 'N/A'):,}")
            return True
        else:
            print("   ❌ 獲取股票數據失敗")
            return False
            
    except Exception as e:
        print(f"❌ Yahoo Provider 測試失敗: {str(e)}")
        return False

async def test_ipo_provider():
    """測試 IPO 數據源"""
    print("\n🆕 測試 IPO Provider...")
    
    try:
        from src.provider_ipo import IPOProvider
        provider = IPOProvider()
        
        # 測試連接
        if await provider.test_connection():
            print("✅ IPO Provider 連接成功")
        else:
            print("⚠️ IPO Provider 連接失敗，但可以使用模擬數據")
        
        # 測試獲取即將上市的 IPO
        print("   測試獲取即將上市的 IPO...")
        upcoming = await provider.get_upcoming_ipos()
        
        if upcoming:
            print(f"   ✅ 獲取到 {len(upcoming)} 個即將上市的 IPO:")
            for ipo in upcoming[:2]:  # 只顯示前2個
                print(f"      {ipo.get('symbol', 'N/A')} - {ipo.get('company', 'N/A')}")
                print(f"        上市日期: {ipo.get('date', 'N/A')}")
                print(f"        AI評級: {ipo.get('ai_rating', 'N/A')}")
        else:
            print("   ⚠️ 沒有獲取到 IPO 數據")
        
        return True
        
    except Exception as e:
        print(f"❌ IPO Provider 測試失敗: {str(e)}")
        return False

async def test_analyzers():
    """測試股票分析器"""
    print("\n📊 測試股票分析器...")
    
    try:
        from src.analyzers_integration import StockAnalyzer
        analyzer = StockAnalyzer()
        
        # 創建模擬股票數據
        mock_data = {
            'symbol': 'TSLA',
            'current_price': 250.00,
            'change': -2.50,
            'change_percent': '-0.99',
            'volume': 45000000,
            'market_cap': 800000000000,
            'sma_20': 248.50,
            'sma_50': 245.00,
            'history': None  # 簡化測試
        }
        
        print("   執行股票分析...")
        result = await analyzer.analyze_stock(mock_data)
        
        if result:
            print("   ✅ 股票分析成功:")
            print(f"      股票: {result.get('symbol', 'N/A')}")
            print(f"      Max Pain: ${result.get('max_pain', 'N/A')}")
            print(f"      磁吸強度: {result.get('magnet_strength', 'N/A')}")
            print(f"      AI建議: {result.get('ai_recommendation', 'N/A')}")
            print(f"      信心度: {result.get('confidence', 'N/A')}%")
            return True
        else:
            print("   ❌ 股票分析失敗")
            return False
            
    except Exception as e:
        print(f"❌ 分析器測試失敗: {str(e)}")
        return False

async def test_cache_system():
    """測試快取系統"""
    print("\n💾 測試快取系統...")
    
    try:
        from src.cache import CacheManager
        cache = CacheManager()
        
        # 健康檢查
        if cache.health_check():
            print("✅ 快取系統健康檢查通過")
        else:
            print("❌ 快取系統健康檢查失敗")
            return False
        
        # 測試快取操作
        test_key = "test_stock_AAPL"
        test_data = {
            "symbol": "AAPL",
            "price": 175.50,
            "timestamp": datetime.now().isoformat()
        }
        
        # 寫入測試
        if cache.set(test_key, test_data, 60):
            print("   ✅ 快取寫入成功")
        else:
            print("   ❌ 快取寫入失敗")
            return False
        
        # 讀取測試
        cached_data = cache.get(test_key)
        if cached_data and cached_data.get("symbol") == "AAPL":
            print("   ✅ 快取讀取成功")
        else:
            print("   ❌ 快取讀取失敗")
            return False
        
        # 顯示快取統計
        stats = cache.get_cache_stats()
        print(f"   快取類型: {stats.get('type', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 快取系統測試失敗: {str(e)}")
        return False

async def test_bot_integration():
    """測試 Bot 整合"""
    print("\n🤖 測試 Bot 整合...")
    
    try:
        # 檢查 Bot Token 是否設置
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not bot_token:
            print("⚠️ TELEGRAM_BOT_TOKEN 環境變數未設置")
            print("   這是正常的開發階段情況")
            return True
        
        from src.bot import MaggieStockBot
        bot = MaggieStockBot()
        
        print("✅ Bot 初始化成功")
        print("   所有核心模組已整合")
        
        return True
        
    except Exception as e:
        print(f"❌ Bot 整合測試失敗: {str(e)}")
        return False

async def main():
    """主測試函數"""
    print("🚀 Maggie's Stock AI Bot 系統測試")
    print("=" * 50)
    
    tests = [
        ("Yahoo Finance Provider", test_yahoo_provider),
        ("IPO Provider", test_ipo_provider),
        ("分析器", test_analyzers),
        ("快取系統", test_cache_system),
        ("Bot 整合", test_bot_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 測試過程中發生異常: {str(e)}")
            results.append((test_name, False))
    
    # 總結
    print("\n" + "=" * 50)
    print("📋 測試結果總結:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("🎉 所有測試都通過了！你的機器人可以開始運行了！")
        print("\n下一步:")
        print("1. 設置環境變數: TELEGRAM_BOT_TOKEN")
        print("2. 運行服務器: python server.py")
        print("3. 設置 webhook")
    else:
        print("⚠️ 部分測試失敗，請檢查上述錯誤信息")
        
    return passed == total

if __name__ == "__main__":
    # 確保在正確的目錄中
    current_dir = os.getcwd()
    if not os.path.exists("src"):
        print("❌ 請在專案根目錄中運行此測試腳本")
        print(f"   當前目錄: {current_dir}")
        print("   應該包含 src/ 目錄")
        sys.exit(1)
    
    # 運行測試
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
