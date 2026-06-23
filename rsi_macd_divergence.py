import numpy as np
import pandas as pd


def sma(data: pd.Series, period: int) -> pd.Series:
    return data.rolling(window=period).mean()


def ema(data: pd.Series, period: int) -> pd.Series:
    return data.ewm(span=period, adjust=False).mean()


def detect_divergences(
    df: pd.DataFrame,
    fast: int = 12,
    slow: int = 26,
    smooth: int = 9,
) -> pd.DataFrame:
    src = df["close"]

    fast_ma = sma(src, fast)
    slow_ma = sma(src, slow)
    macd = fast_ma - slow_ma
    signal = ema(macd, smooth)
    hist = macd - signal

    fractal_top = np.full(len(df), np.nan)
    fractal_bot = np.full(len(df), np.nan)

    for j in range(2, len(df) - 2):
        if (
            hist.iloc[j - 2] < hist.iloc[j]
            and hist.iloc[j - 1] < hist.iloc[j]
            and hist.iloc[j] > hist.iloc[j + 1]
            and hist.iloc[j] > hist.iloc[j + 2]
        ):
            fractal_top[j] = hist.iloc[j]

        if (
            hist.iloc[j - 2] > hist.iloc[j]
            and hist.iloc[j - 1] > hist.iloc[j]
            and hist.iloc[j] < hist.iloc[j + 1]
            and hist.iloc[j] < hist.iloc[j + 2]
        ):
            fractal_bot[j] = hist.iloc[j]

    regular_bearish = np.full(len(df), np.nan)
    hidden_bearish = np.full(len(df), np.nan)
    regular_bullish = np.full(len(df), np.nan)
    hidden_bullish = np.full(len(df), np.nan)

    last_top_hist = None
    last_top_high = None

    last_bot_hist = None
    last_bot_low = None

    for j in range(2, len(df) - 2):
        if not np.isnan(fractal_top[j]):
            if last_top_hist is not None:
                curr_high = df["high"].iloc[j]
                curr_hist = hist.iloc[j]
                if curr_high > last_top_high and curr_hist < last_top_hist:
                    regular_bearish[j] = curr_hist
                elif curr_high < last_top_high and curr_hist > last_top_hist:
                    hidden_bearish[j] = curr_hist
            last_top_hist = hist.iloc[j]
            last_top_high = df["high"].iloc[j]

        if not np.isnan(fractal_bot[j]):
            if last_bot_hist is not None:
                curr_low = df["low"].iloc[j]
                curr_hist = hist.iloc[j]
                if curr_low < last_bot_low and curr_hist > last_bot_hist:
                    regular_bullish[j] = curr_hist
                elif curr_low > last_bot_low and curr_hist < last_bot_hist:
                    hidden_bullish[j] = curr_hist
            last_bot_hist = hist.iloc[j]
            last_bot_low = df["low"].iloc[j]

    result = df.copy()
    result["macd"] = macd
    result["signal"] = signal
    result["hist"] = hist
    result["fractal_top"] = fractal_top
    result["fractal_bot"] = fractal_bot
    result["regular_bearish"] = regular_bearish
    result["hidden_bearish"] = hidden_bearish
    result["regular_bullish"] = regular_bullish
    result["hidden_bullish"] = hidden_bullish
    return result


def plot_divergences(result: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    ax1.plot(result.index, result["close"], color="black", linewidth=1.2, label="Close")
    ax1.set_ylabel("Price")
    ax1.legend(loc="upper left")
    ax1.grid(True, alpha=0.3)

    ax2.plot(result.index, result["macd"], color="gray", linewidth=1, label="MACD")
    ax2.plot(result.index, result["signal"], color="silver", linewidth=1, label="Signal")
    ax2.bar(result.index, result["hist"], color="black", width=0.8, label="Hist")
    ax2.axhline(0, color="black", linewidth=0.5)

    top_idx = ~np.isnan(result["fractal_top"])
    ax2.scatter(
        result.index[top_idx],
        result["fractal_top"][top_idx],
        color="black",
        s=40,
        marker="v",
        zorder=5,
    )

    bot_idx = ~np.isnan(result["fractal_bot"])
    ax2.scatter(
        result.index[bot_idx],
        result["fractal_bot"][bot_idx],
        color="black",
        s=40,
        marker="^",
        zorder=5,
    )

    for div_type, color, label in [
        ("regular_bearish", "maroon", "Regular Bearish"),
        ("hidden_bearish", "maroon", "Hidden Bearish"),
        ("regular_bullish", "green", "Regular Bullish"),
        ("hidden_bullish", "green", "Hidden Bullish"),
    ]:
        idx = ~np.isnan(result[div_type])
        ax2.scatter(
            result.index[idx],
            result[div_type][idx],
            color=color,
            s=100,
            marker="o",
            zorder=6,
            label=label,
        )

    ax2.set_ylabel("MACD")
    ax2.legend(loc="upper left")
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_locator(ticker.MaxNLocator(10))

    fig.tight_layout()
    plt.show()



