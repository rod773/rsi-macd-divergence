import argparse
import sys
import pandas as pd

from rsi_macd_divergence import detect_divergences, plot_divergences
from backtest import run_backtest, print_report, plot_equity


def fetch_data(symbol, timeframe, start, end, tick=False):
    if tick:
        from mt5_data import fetch_ticks_ohlc
        return fetch_ticks_ohlc(symbol, timeframe, start, end)
    try:
        from mt5_data import fetch_ohlc
        return fetch_ohlc(symbol, timeframe, start, end)
    except Exception:
        import yfinance as yf
        df = yf.download(symbol, start=start, end=end, auto_adjust=True)
        if df.empty:
            raise ValueError(f"No data for {symbol} from {start} to {end}")
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0].lower() for c in df.columns]
        else:
            df.columns = [c.lower() for c in df.columns]
        df.index = pd.to_datetime(df.index)
        return df


def cmd_plot(args):
    df = fetch_data(args.symbol, args.timeframe, args.start, args.end, args.tick)
    result = detect_divergences(df, args.fast, args.slow, args.smooth)
    plot_divergences(result)


def cmd_backtest(args):
    df = fetch_data(args.symbol, args.timeframe, args.start, args.end, args.tick)

    result = run_backtest(
        df,
        fast=args.fast,
        slow=args.slow,
        smooth=args.smooth,
        use_hidden=args.hidden,
        tp_pct=args.tp,
        sl_pct=args.sl,
        size=args.size,
    )
    print_report(result, args.symbol)

    if args.plot_equity:
        import matplotlib
        matplotlib.use("Agg")
        plot_equity(result, path=f"backtest_{args.symbol}_{args.timeframe}.png")


def main():
    parser = argparse.ArgumentParser(description="RSI MACD Divergence")
    sub = parser.add_subparsers(dest="command", required=True)

    # shared args
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--symbol", default="EURUSD")
    common.add_argument("--timeframe", default="H1", help="M1, M5, M15, M30, H1, H4, D1, W1, MN1")
    common.add_argument("--start", default="2024-01-01")
    common.add_argument("--end", default=None)
    common.add_argument("--fast", type=int, default=12)
    common.add_argument("--slow", type=int, default=26)
    common.add_argument("--smooth", type=int, default=9)

    common.add_argument("--tick", action="store_true", help="Build OHLC from MT5 tick data")

    # plot
    p = sub.add_parser("plot", parents=[common], help="Plot divergences")
    p.set_defaults(func=cmd_plot)

    # backtest
    b = sub.add_parser("backtest", parents=[common], help="Run backtest")
    b.add_argument("--hidden", action="store_true", help="Include hidden divergences")
    b.add_argument("--tp", type=float, default=None, help="Take profit (e.g. 0.02 = 2 pct)")
    b.add_argument("--sl", type=float, default=None, help="Stop loss (e.g. 0.01 = 1 pct)")
    b.add_argument("--size", type=float, default=1.0, help="Position size")
    b.add_argument("--plot-equity", action="store_true", help="Plot equity curve")
    b.set_defaults(func=cmd_backtest)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
