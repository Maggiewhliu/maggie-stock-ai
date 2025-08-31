import argparse, sys
import pandas as pd
from src.provider_yahoo import YahooProvider
from src.service import maxpain_handler, gex_handler

def main():
    ap=argparse.ArgumentParser()
    sub=ap.add_subparsers(dest='cmd')
    mp=sub.add_parser('maxpain'); mp.add_argument('symbol', nargs='?'); mp.add_argument('expiry', nargs='?'); mp.add_argument('--from-csv')
    gx=sub.add_parser('gex'); gx.add_argument('symbol', nargs='?'); gx.add_argument('expiry', nargs='?')
    args=ap.parse_args()

    if args.cmd=='maxpain':
        if args.from_csv:
            from src.analyzers import OptionRow, compute_max_pain
            df=pd.read_csv(args.from_csv)
            rows=[OptionRow(float(r['strike']), str(r['type']).lower(), int(r['openInterest'])) for _,r in df.iterrows()]
            res=compute_max_pain(rows, contract_multiplier=100)
            print(f'CSV MaxPain={res.max_pain} MinTotalPain={int(res.min_total_pain)}; strikes={len(res.curve)}'); return
        if not args.symbol:
            print('Usage: python -m src.cli maxpain <SYMBOL> [YYYY-MM-DD] or --from-csv path'); sys.exit(2)
        yp=YahooProvider()
        expiry=args.expiry or yp.nearest_expiry(args.symbol)
        res=maxpain_handler(args.symbol, expiry)
        print(f"{res['symbol']} {res['expiry']} MaxPain={res['max_pain']} MinTotalPain={int(res['min_total_pain'])}")
    elif args.cmd=='gex':
        if not args.symbol:
            print('Usage: python -m src.cli gex <SYMBOL> [YYYY-MM-DD]'); sys.exit(2)
        yp=YahooProvider()
        expiry=args.expiry or yp.nearest_expiry(args.symbol)
        spot=yp.get_spot(args.symbol)['price']
        g,sup,res=gex_handler(args.symbol, expiry, spot=spot)
        print(f"{args.symbol.upper()} {expiry} ShareGamma={g.share_gamma:.2f} DollarGamma(1%)={g.dollar_gamma_1pct:,.0f} Support={sup} Resistance={res}")
    else:
        ap.print_help()

if __name__=='__main__':
    main()
