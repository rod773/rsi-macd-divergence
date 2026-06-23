import numpy as np
import pandas as pd
from typing import Optional


def fetch_ticks_ohlc(
    symbol: str,
    timeframe: str = "H1",
    start: str = "2024-01-01",
    end: Optional[str] = None,
) -> pd.DataFrame:
    try:
        import MetaTrader5 as mt5
    except ImportError:
        raise ImportError("MetaTrader5 not installed. Run: pip install MetaTrader5")

    if not mt5.initialize():
        raise ConnectionError(f"MT5 init failed: {mt5.last_error()}")

    end_dt = pd.Timestamp(end) if end else pd.Timestamp.today()
    ticks = mt5.copy_ticks_range(symbol, pd.Timestamp(start), end_dt, mt5.COPY_TICKS_ALL)
    mt5.shutdown()

    if ticks is None or len(ticks) == 0:
        raise ValueError(f"No tick data for {symbol} from {start} to {end}")

    df = pd.DataFrame(ticks)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.set_index("time").sort_index()

    price = df[["bid", "ask"]].mean(axis=1) if "bid" in df.columns else df["last"]
    price.name = "price"

    tf_upper = timeframe.upper()
    rule_map = {"M1": "1min", "M5": "5min", "M15": "15min", "M30": "30min",
                "H1": "1h", "H4": "4h",
                "D1": "1D", "W1": "1W", "MN1": "1ME"}
    rule = rule_map.get(tf_upper)
    if rule is None:
        raise ValueError(f"Invalid timeframe: {timeframe}")
    ohlc = price.resample(rule).agg(["first", "max", "min", "last"]).dropna()
    ohlc.columns = ["open", "high", "low", "close"]

    ohlc["volume"] = price.resample(rule).count()
    ohlc.index.name = "time"
    return ohlc


def fetch_ohlc(
    symbol: str,
    timeframe: str = "H1",
    start: str = "2024-01-01",
    end: Optional[str] = None,
) -> pd.DataFrame:
    try:
        import MetaTrader5 as mt5
    except ImportError:
        raise ImportError("MetaTrader5 not installed. Run: pip install MetaTrader5")

    timeframe_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
        "MN1": mt5.TIMEFRAME_MN1,
    }

    tf = timeframe_map.get(timeframe.upper())
    if tf is None:
        raise ValueError(f"Invalid timeframe: {timeframe}")

    if not mt5.initialize():
        raise ConnectionError(f"MT5 init failed: {mt5.last_error()}")

    rates = mt5.copy_rates_range(symbol, tf, pd.Timestamp(start), pd.Timestamp(end) if end else pd.Timestamp.today())
    mt5.shutdown()

    if rates is None or len(rates) == 0:
        raise ValueError(f"No data for {symbol} {timeframe} from {start} to {end}")

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    df = df.rename(columns={
        "open": "open",
        "high": "high",
        "low": "low",
        "close": "close",
        "tick_volume": "volume",
    })
    df = df.set_index("time")
    return df


def list_symbols() -> list:
    try:
        import MetaTrader5 as mt5
    except ImportError:
        raise ImportError("MetaTrader5 not installed. Run: pip install MetaTrader5")

    if not mt5.initialize():
        raise ConnectionError(f"MT5 init failed: {mt5.last_error()}")

    symbols = [s.name for s in mt5.symbols_get()]
    mt5.shutdown()
    return symbols
