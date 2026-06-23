from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from rsi_macd_divergence import detect_divergences


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    side: str  # LONG / SHORT
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_pct: float
    exit_reason: str


@dataclass
class BacktestResult:
    trades: list[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    total_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    profit_factor: float = 0.0


def run_backtest(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    smooth: int = 9,
    use_hidden: bool = False,
    tp_pct: Optional[float] = None,
    sl_pct: Optional[float] = None,
    size: float = 1.0,
) -> BacktestResult:
    data = detect_divergences(df, fast, slow, smooth)

    if use_hidden:
        long_signal = (~np.isnan(data["regular_bullish"])) | (~np.isnan(data["hidden_bullish"]))
        short_signal = (~np.isnan(data["regular_bearish"])) | (~np.isnan(data["hidden_bearish"]))
    else:
        long_signal = ~np.isnan(data["regular_bullish"])
        short_signal = ~np.isnan(data["regular_bearish"])

    position = 0.0  # +1 long, -1 short, 0 flat
    entry_price = 0.0
    entry_time = None

    trades: list[Trade] = []
    equity = [100_000.0]
    balance = 100_000.0

    for i in range(1, len(data)):
        idx = data.index[i]
        close = data["close"].iloc[i]
        high = data["high"].iloc[i]
        low = data["low"].iloc[i]

        # check TP/SL for open position
        exit_reason = None
        if position != 0 and tp_pct is not None:
            if position == 1 and high >= entry_price * (1 + tp_pct):
                exit_price = entry_price * (1 + tp_pct)
                exit_reason = "TP"
            elif position == -1 and low <= entry_price * (1 - tp_pct):
                exit_price = entry_price * (1 - tp_pct)
                exit_reason = "TP"

        if position != 0 and sl_pct is not None and exit_reason is None:
            if position == 1 and low <= entry_price * (1 - sl_pct):
                exit_price = entry_price * (1 - sl_pct)
                exit_reason = "SL"
            elif position == -1 and high >= entry_price * (1 + sl_pct):
                exit_price = entry_price * (1 + sl_pct)
                exit_reason = "SL"

        # close on opposite signal or TP/SL
        if position != 0:
            close_signal = False
            if position == 1 and short_signal.iloc[i]:
                close_signal = True
                exit_reason = exit_reason or "Signal"
                exit_price = close
            elif position == -1 and long_signal.iloc[i]:
                close_signal = True
                exit_reason = exit_reason or "Signal"
                exit_price = close

            if exit_reason is not None:
                pnl = (exit_price - entry_price) * size * position
                pnl_pct = (exit_price / entry_price - 1) * position
                balance += pnl
                trades.append(Trade(
                    entry_time=entry_time,
                    exit_time=idx,
                    side="LONG" if position == 1 else "SHORT",
                    entry_price=entry_price,
                    exit_price=exit_price,
                    size=size,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    exit_reason=exit_reason,
                ))
                position = 0.0
                entry_price = 0.0
                entry_time = None

        # enter new position
        if position == 0:
            if long_signal.iloc[i]:
                position = 1.0
                entry_price = close
                entry_time = idx
            elif short_signal.iloc[i]:
                position = -1.0
                entry_price = close
                entry_time = idx

        equity.append(balance)

    # close any open position at end
    if position != 0:
        exit_price = data["close"].iloc[-1]
        pnl = (exit_price - entry_price) * size * position
        pnl_pct = (exit_price / entry_price - 1) * position
        balance += pnl
        trades.append(Trade(
            entry_time=entry_time,
            exit_time=data.index[-1],
            side="LONG" if position == 1 else "SHORT",
            entry_price=entry_price,
            exit_price=exit_price,
            size=size,
            pnl=pnl,
            pnl_pct=pnl_pct,
            exit_reason="End",
        ))

    equity_series = pd.Series(equity, index=data.index[:len(equity)])

    # stats
    total_return = (balance / 100_000.0 - 1) * 100
    peak = equity_series.expanding().max()
    dd = (equity_series - peak) / peak * 100
    max_dd = dd.min()

    returns = equity_series.pct_change().dropna()
    sharpe = float(returns.mean() / returns.std() * np.sqrt(252)) if len(returns) > 1 else 0.0

    n_wins = sum(1 for t in trades if t.pnl > 0)
    total = len(trades)
    win_rate = (n_wins / total * 100) if total > 0 else 0.0
    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    return BacktestResult(
        trades=trades,
        equity_curve=equity_series,
        total_return=total_return,
        max_drawdown=max_dd,
        sharpe=sharpe,
        win_rate=win_rate,
        total_trades=total,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
        profit_factor=profit_factor,
    )


def print_report(result: BacktestResult, symbol: str = "") -> None:
    header = f" Backtest Report {symbol}".rstrip()
    print("=" * 60)
    print(f"  {header}")
    print("=" * 60)
    print(f"  Total Return:      {result.total_return:>8.2f}%")
    print(f"  Max Drawdown:      {result.max_drawdown:>8.2f}%")
    print(f"  Sharpe Ratio:      {result.sharpe:>8.2f}")
    print(f"  Profit Factor:     {result.profit_factor:>8.2f}")
    print(f"  Total Trades:      {result.total_trades:>8}")
    print(f"  Win Rate:          {result.win_rate:>8.2f}%")
    print(f"  Gross Profit:      ${result.gross_profit:>8.2f}")
    print(f"  Gross Loss:        ${result.gross_loss:>8.2f}")
    print("-" * 60)
    print(f"  {'#':>3} {'Date':>20} {'Side':>6} {'Entry':>10} {'Exit':>10} {'PnL':>10} {'Reason':>8}")
    print("-" * 60)
    for i, t in enumerate(result.trades, 1):
        print(f"  {i:>3} {t.entry_time.strftime('%Y-%m-%d %H:%M'):>20} {t.side:>6} {t.entry_price:>10.2f} {t.exit_price:>10.2f} {t.pnl:>+10.2f} {t.exit_reason:>8}")
    print("=" * 60)


def plot_equity(result: BacktestResult, path: Optional[str] = None) -> None:
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    ax1.plot(result.equity_curve.index, result.equity_curve, color="blue", linewidth=1)
    ax1.set_ylabel("Equity ($)")
    ax1.grid(True, alpha=0.3)
    ax1.axhline(100_000, color="gray", linestyle="--", linewidth=0.5)

    peak = result.equity_curve.expanding().max()
    dd = (result.equity_curve - peak) / peak * 100
    ax2.fill_between(dd.index, dd, 0, color="red", alpha=0.3)
    ax2.plot(dd.index, dd, color="red", linewidth=0.8)
    ax2.set_ylabel("Drawdown (%)")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    if path:
        plt.savefig(path, dpi=150, bbox_inches="tight")
        print(f"  Saved: {path}")
    else:
        plt.show()
    plt.close(fig)
