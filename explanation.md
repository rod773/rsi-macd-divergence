# RSI‑MACD Divergence Indicator & Strategy

## Indicator Overview

The indicator identifies **regular** and **hidden** divergences between price and the MACD histogram, using:

- **Fast MA**   – SMA of period *fast* (default 12)
- **Slow MA**   – SMA of period *slow* (default 26)
- **Signal**    – EMA of the MACD line with *smooth* periods (default 9)
- **Histogram** – MACD – Signal

### Fractal Detection
Five‑bar pivot highs/lows on the histogram are used as anchor points for divergences.

- **Top fractal** – bar 2 is higher than bars 0, 1, 3, 4
- **Bottom fractal** – bar 2 is lower than bars 0, 1, 3, 4

### Divergence Logic
When a new top or bottom fractal appears, the indicator compares price highs/lows against the previous fractal’s high/low and the histogram values:

| Divergence Type | Price Trend | Histogram Trend | Interpretation |
|---------------|-------------|-----------------|--------------|
| Regular Bearish | Higher high | Lower high | Bearish reversal |
| Hidden Bearish | Lower high  | Higher high | Bearish continuation |
| Regular Bullish | Lower low | Higher low | Bullish reversal |
| Hidden Bullish | Higher low | Lower low | Bullish continuation |

### Output Columns
The DataFrame returned by `detect_divergences()` contains:

- `macd`, `signal`, `hist`
- `fractal_top`, `fractal_bot`
- `regular_bearish`, `hidden_bearish`, `regular_bullish`, `hidden_bullish`

## Trading Strategy
The corresponding backtesting strategy trades on the divergence signals:

1. **Long entry** – Regular Bullish (or, if `--hidden` flag is set, Hidden Bullish) divergence.
2. **Short entry** – Regular Bearish (or, if `--hidden` flag is set, Hidden Bearish) divergence.
3. **Exit conditions** –
   - Opposite signal appears.
   - Take‑Profit (TP) hit (`--tp`).
   - Stop‑Loss (SL) hit (`--sl`).
   - Or at the end of the data period.

### Parameters
```
--symbol     Currency pair or ticker (default: EURUSD)
--timeframe  Chart timeframe (e.g., H1, H4, D1)
--start      Start date (YYYY‑MM‑DD)
--end        End date (YYYY‑MM‑DD, optional)
--fast       Fast MA period (default 12)
--slow       Slow MA period (default 26)
--smooth     Signal EMA period (default 9)
--hidden     Include hidden divergences (long/short)
--tp         Take‑Profit percentage (e.g., 0.02 = 2%)
--sl         Stop‑Loss percentage (e.g., 0.01 = 1%)
--size       Position size multiplier
--plot-equity Plot equity curve after backtest
```

### Usage
```bash
# Plot divergences
python main.py plot --symbol EURUSD --timeframe H1 --start 2024-01-01

# Run backtest with hidden divergences and TP/SL
python main.py backtest --symbol GBPUSD --timeframe H1 \
    --start 2024-01-01 --tp 0.02 --sl 0.01 --hidden --plot-equity
```

## Statistics
The backtest prints:
- Total return, max drawdown, Sharpe ratio, profit factor, win rate, number of trades, gross profit/loss.
- Detailed trade list.
- Optional equity curve plot.

## Dependencies
- `pandas`, `numpy`, `matplotlib`
- Optional `MetaTrader5` provider; falls back to `yfinance`.

---

For further details refer to the repository README and source code.
