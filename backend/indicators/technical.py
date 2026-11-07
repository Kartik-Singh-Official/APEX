"""Technical Indicators Engine for APEX.
Pure vector implementations of:
- EMA (20, 50, 200)
- RSI (14)
- MACD (12, 26, 9)
- ATR (14)
- ADX (14) with +DI, -DI
- Bollinger Bands (20, 2)
- Volume MA (20)
- On-Balance Volume (OBV)
- Relative Volume (RVOL)
"""
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    """Compute Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Compute Relative Strength Index."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    # Wilder's smoothing (alpha = 1 / period)
    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def compute_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
    """Compute MACD, Signal Line, and Histogram."""
    ema_fast = compute_ema(close, fast)
    ema_slow = compute_ema(close, slow)
    macd_line = ema_fast - ema_slow
    signal_line = compute_ema(macd_line, signal)
    hist = macd_line - signal_line
    return {
        "macd": macd_line,
        "signal": signal_line,
        "hist": hist,
    }


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Compute Average True Range."""
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    return atr.fillna(0.0)


def compute_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
    """Compute Average Directional Index (ADX) along with +DI and -DI."""
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

    atr = compute_atr(high, low, close, period=period)

    plus_di = 100.0 * (pd.Series(plus_dm, index=high.index).ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean() / (atr + 1e-9))
    minus_di = 100.0 * (pd.Series(minus_dm, index=low.index).ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean() / (atr + 1e-9))

    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    adx = dx.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    return {
        "adx": adx.fillna(0.0),
        "plus_di": plus_di.fillna(0.0),
        "minus_di": minus_di.fillna(0.0),
    }


def compute_bollinger_bands(close: pd.Series, period: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
    """Compute Bollinger Bands (Middle, Upper, Lower, Bandwidth, %B)."""
    middle = close.rolling(window=period).mean()
    std = close.rolling(window=period).std()
    upper = middle + (std_dev * std)
    lower = middle - (std_dev * std)
    bandwidth = (upper - lower) / (middle + 1e-9)
    pct_b = (close - lower) / (upper - lower + 1e-9)
    return {
        "middle": middle,
        "upper": upper,
        "lower": lower,
        "bandwidth": bandwidth,
        "pct_b": pct_b,
    }


def compute_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """Compute On-Balance Volume."""
    diff = close.diff()
    direction = np.where(diff > 0, 1, np.where(diff < 0, -1, 0))
    obv = (direction * volume).cumsum()
    return pd.Series(obv, index=close.index)


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Compute full indicator suite and append to dataframe."""
    if len(df) < 5:
        return df.copy()

    res = df.copy()
    c = res["close"]
    h = res["high"]
    l = res["low"]
    v = res["volume"]

    # Moving Averages
    res["ema_20"] = compute_ema(c, 20)
    res["ema_50"] = compute_ema(c, 50)
    res["ema_200"] = compute_ema(c, 200)

    # Momentum
    res["rsi_14"] = compute_rsi(c, 14)
    macd = compute_macd(c, 12, 26, 9)
    res["macd"] = macd["macd"]
    res["macd_signal"] = macd["signal"]
    res["macd_hist"] = macd["hist"]

    # Volatility
    res["atr_14"] = compute_atr(h, l, c, 14)
    bb = compute_bollinger_bands(c, 20, 2.0)
    res["bb_middle"] = bb["middle"]
    res["bb_upper"] = bb["upper"]
    res["bb_lower"] = bb["lower"]
    res["bb_bandwidth"] = bb["bandwidth"]
    res["bb_pct_b"] = bb["pct_b"]

    # Trend Strength
    adx_res = compute_adx(h, l, c, 14)
    res["adx_14"] = adx_res["adx"]
    res["plus_di"] = adx_res["plus_di"]
    res["minus_di"] = adx_res["minus_di"]

    # Volume Analytics
    res["vol_ma_20"] = v.rolling(window=20).mean()
    res["rvol"] = v / (res["vol_ma_20"] + 1e-9)
    res["obv"] = compute_obv(c, v)

    return res

