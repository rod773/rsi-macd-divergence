# RSI MACD Divergence

A TradingView Pine Script indicator that detects **regular and hidden divergences** between price and the MACD histogram.

## How it works

### MACD Calculation

Computes MACD using **SMA** (not EMA) for fast/slow lines, then an EMA signal line. Histogram = MACD - signal.

### Fractal Detection

Identifies 5-bar pivot highs/lows on the MACD histogram. A top fractal is when bar `[2]` is higher than its 2 neighbors on each side (and vice versa for bottoms). These become divergence anchor points.

### Divergence Logic

Compares consecutive fractals to detect four divergence types:

| Divergence | Price | Histogram | Signal |
|---|---|---|---|
| **Regular Bearish** | higher high | lower high | Bearish reversal |
| **Hidden Bearish** | lower high | higher high | Bearish continuation |
| **Regular Bullish** | lower low | higher low | Bullish reversal |
| **Hidden Bullish** | higher low | lower low | Bullish continuation |

### Visuals

- MACD line (gray), signal line (silver), histogram (black)
- Fractal points marked as black shapes
- Divergences shown as maroon (bearish) or green (bullish) circles
- "Regular" / "hidden" labels on detected divergences

## Python version

`rsi_macd_divergence.py` replicates the indicator logic with pandas/numpy.

### Plot divergences

```python
from rsi_macd_divergence import detect_divergences, plot_divergences
import yfinance as yf

data = yf.download("AAPL", start="2024-01-01", end="2024-12-31")
data.columns = [c.lower() for c in data.columns]

result = detect_divergences(data)
plot_divergences(result)
```

### CLI

```bash
# Plot divergences
python main.py plot --symbol EURUSD --timeframe H1 --start 2024-01-01

# Run backtest
python main.py backtest --symbol GBPUSD --timeframe H1 --start 2024-01-01 --sl 0.01 --tp 0.02 --plot-equity

# With hidden divergences
python main.py backtest --symbol BTCUSD --timeframe H4 --start 2024-01-01 --hidden --plot-equity
```

If MetaTrader5 is not installed, it falls back to yfinance for data.

### Backtest strategy

- **Long entry** on Regular Bullish Divergence (or hidden with `--hidden`)
- **Short entry** on Regular Bearish Divergence (or hidden with `--hidden`)
- Position is closed on the opposite signal, TP/SL, or at end of data

### Output columns

`detect_divergences()` returns a DataFrame with added columns: `macd`, `signal`, `hist`, `fractal_top`, `fractal_bot`, `regular_bearish`, `hidden_bearish`, `regular_bullish`, `hidden_bullish`.

### Dependencies

- `pandas`, `numpy`, `matplotlib`
- `MetaTrader5` (optional, for MT5 data)
- `yfinance` (optional, fallback data source)
