import argparse
import sys
import pandas as pd
from src.provider_yahoo import YahooProvider

def main():
    ap = argparse.ArgumentParser(description="Maggie's Stock AI - 命令行工具")
    sub = ap.add_subparsers(dest='cmd', help='可用命令')
    
    # Max Pain 命令
    mp = sub.add_parser('maxpain', help='計算 Max Pain')
    mp.add_argument('symbol', nargs='?', help='股票代碼 (例如: TSLA)')
    mp.add_argument('expiry', nargs='?', help='到期日 (YYYY-MM-DD)')
    mp.add_argument('--from-csv', help='從 CSV 文件讀取期權數據')
    
    # GEX 命令
    gx = sub.add_parser('gex', help='計算 Gamma Exposure')
    gx.add_argument('symbol', nargs='?', help='股票代碼 (例如: TSLA)')
    gx.add_argument('expiry', nargs='?', help='到期日 (YYYY-MM-DD)')
    
    # 測試命令
    test = sub.add_parser('test', help='測試系統功能')
    test.add_argument('--yahoo', action='store_true', help='測試 Yahoo Finance')
    test.add_argument('--cache', action='store_true', help='測試快取系統')
    test.add_argument('--all', action='store_true', help='測試所有功能')
    
    args = ap.parse_args()
    
    if args.cmd == 'maxpain':
        handle_maxpain_command(args)
    elif args.cmd == 'gex':
        handle_gex_command(args)
    elif args.cmd == 'test':
        handle_test_command(args)
    else:
        ap.print_help()

def handle_maxpain_command(args):
    """處理 Max Pain 命令"""
    try:
        if args.from_csv:
            # 從 CSV 文件計算
            from src.analyzers import OptionRow, compute_max_pain
            
            if not os.path.exists(args.from_csv):
                print(f"錯誤: 找不到文件 {args.from_csv}")
                sys.exit(1)
            
            df = pd.read_csv(args.from_csv)
            required_columns = ['strike', 'type', 'openInterest']
            
            if not all(col in df.columns for col in required_columns):
                print(f"錯誤: CSV 文件必須包含列: {required_columns}")
                sys.exit(1)
            
            rows = [
                OptionRow(
                    strike=float(r['strike']), 
                    type=str(r['type']).lower(), 
                    open_interest=int(r['openInterest'])
                ) 
                for _, r in df.iterrows()
            ]
            
            res = compute_max_pain(rows, contract_multiplier=100)
            print(f'CSV MaxPain={res.max_pain} MinTotalPain={int(res.min_total_pain)}; strikes={len(res.curve)}')
            return
        
        if not args.symbol:
            print('使用方法: python -m src.cli maxpain <SYMBOL> [YYYY-MM-DD] 或 --from-csv <路徑>')
            sys.exit(2)
        
        # 從 Yahoo Finance 計算
        yp = YahooProvider()
        
        try:
            expiry = args.expiry or yp.nearest_expiry(args.symbol)
        except Exception as e:
            print(f"錯誤: 無法獲取 {args.symbol} 的期權到期日: {str(e)}")
            sys.exit(1)
        
        # 使用 service.py 的函數，如果不存在則直接計算
        try:
            from src.service import maxpain_handler
            res = maxpain_handler(args.symbol, expiry)
            print(f"{res['symbol']} {res['expiry']} MaxPain={res['max_pain']} MinTotalPain={int(res['min_total_pain'])}")
        except ImportError:
            # 如果 service.py 不存在，直接計算
            res = calculate_maxpain_direct(args.symbol, expiry, yp)
            print(f"{args.symbol.upper()} {expiry} MaxPain={res['max_pain']} MinTotalPain={int(res['min_total_pain'])}")
            
    except Exception as e:
        print(f"計算 Max Pain 時發生錯誤: {str(e)}")
        sys.exit(1)

def handle_gex_command(args):
    """處理 GEX 命令"""
    try:
        if not args.symbol:
            print('使用方法: python -m src.cli gex <SYMBOL> [YYYY-MM-DD]')
            sys.exit(2)
        
        yp = YahooProvider()
        
        try:
            expiry = args.expiry or yp.nearest_expiry(args.symbol)
            spot = yp.get_spot(args.symbol)['price']
        except Exception as e:
            print(f"錯誤: 無法獲取 {args.symbol} 的數據: {str(e)}")
            sys.exit(1)
        
        # 使用 service.py 的函數，如果不存在則直接計算
        try:
            from src.service import gex_handler
            g, sup, res = gex_handler(args.symbol, expiry, spot=spot)
            print(f"{args.symbol.upper()} {expiry} ShareGamma={g.share_gamma:.2f} DollarGamma(1%)={g.dollar_gamma_1pct:,.0f} Support={sup} Resistance={res}")
        except ImportError:
            # 如果 service.py 不存在，直接計算
            gex_result = calculate_gex_direct(args.symbol, expiry, spot, yp)
            print(f"{args.symbol.upper()} {expiry} ShareGamma={gex_result['share_gamma']:.2f} DollarGamma(1%)={gex_result['dollar_gamma_1pct']:,.0f}")
            
    except Exception as e:
        print(f"計算 GEX 時發生錯誤: {str(e)}")
        sys.exit(1)

def handle_test_command(args):
    """處理測試命令"""
    try:
        if args.yahoo or args.all:
            print("測試 Yahoo Finance 連接...")
            yp = YahooProvider()
            if yp.test_connection():
                print("✅ Yahoo Finance 連接成功")
                # 測試獲取數據
                data = yp.get_quote("AAPL")
                if data and data.get('price'):
                    print(f"   AAPL 價格: ${data['price']}")
                else:
                    print("⚠️ 無法獲取價格數據")
            else:
                print("❌ Yahoo Finance 連接失敗")
        
        if args.cache or args.all:
            print("\n測試快取系統...")
            try:
                from src.cache import CacheManager
                cache = CacheManager()
                if cache.health_check():
                    print("✅ 快取系統正常")
                    stats = cache.get_cache_stats()
                    print(f"   快取類型: {stats.get('type', 'Unknown')}")
                else:
                    print("❌ 快取系統異常")
            except ImportError:
                print("⚠️ 快取模組未找到")
        
        if args.all:
            print("\n測試分析器...")
            try:
                from src.analyzers import compute_max_pain, OptionRow
                # 簡單測試
                test_rows = [
                    OptionRow(strike=100.0, type='call', open_interest=1000),
                    OptionRow(strike=105.0, type='put', open_interest=1500)
                ]
                result = compute_max_pain(test_rows)
                print(f"✅ 分析器正常 (測試 Max Pain: {result.max_pain})")
            except ImportError:
                print("⚠️ 分析器模組未找到")
        
        if not (args.yahoo or args.cache or args.all):
            print("請指定要測試的功能: --yahoo, --cache, 或 --all")
            
    except Exception as e:
        print(f"測試過程中發生錯誤: {str(e)}")

def calculate_maxpain_direct(symbol, expiry, yahoo_provider):
    """直接計算 Max Pain（不依賴 service.py）"""
    from src.analyzers import OptionRow, compute_max_pain
    
    # 獲取期權鏈
    options_chain = yahoo_provider.get_options_chain(symbol, expiry)
    
    # 準備期權數據
    option_rows = []
    
    for call in options_chain['calls']:
        option_rows.append(OptionRow(
            strike=call['strike'],
            type='call',
            open_interest=call['openInterest']
        ))
    
    for put in options_chain['puts']:
        option_rows.append(OptionRow(
            strike=put['strike'],
            type='put',
            open_interest=put['openInterest']
        ))
    
    # 計算 Max Pain
    result = compute_max_pain(option_rows)
    
    return {
        'symbol': symbol.upper(),
        'expiry': expiry,
        'max_pain': result.max_pain,
        'min_total_pain': result.min_total_pain
    }

def calculate_gex_direct(symbol, expiry, spot, yahoo_provider):
    """直接計算 GEX（不依賴 service.py）"""
    from src.analyzers import OptionGreeksRow, compute_gex
    
    # 獲取期權鏈
    options_chain = yahoo_provider.get_options_chain(symbol, expiry)
    
    # 準備希臘字母數據
    greeks_rows = []
    
    for call in options_chain['calls']:
        if call['impliedVolatility'] is not None:
            greeks_rows.append(OptionGreeksRow(
                strike=call['strike'],
                type='call',
                open_interest=call['openInterest'],
                iv=call['impliedVolatility'],
                T=call['T']
            ))
    
    for put in options_chain['puts']:
        if put['impliedVolatility'] is not None:
            greeks_rows.append(OptionGreeksRow(
                strike=put['strike'],
                type='put',
                open_interest=put['openInterest'],
                iv=put['impliedVolatility'],
                T=put['T']
            ))
    
    # 計算 GEX
    gex_result = compute_gex(greeks_rows, spot, r=0.045, q=0.0)
    
    return {
        'share_gamma': gex_result.share_gamma,
        'dollar_gamma_1pct': gex_result.dollar_gamma_1pct
    }

if __name__ == '__main__':
    main()
