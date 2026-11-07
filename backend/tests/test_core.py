"""Unit and Integration Tests for APEX Core Modules."""
import pytest
import pandas as pd
import numpy as np

from backend.indicators.technical import (
    compute_ema,
    compute_rsi,
    compute_macd,
    compute_atr,
    compute_bollinger_bands,
    compute_adx,
    compute_indicators,
)
from backend.market_structure.structure import (
    detect_pivots,
    derive_sr_zones,
    analyze_market_structure,
)
from backend.patterns.detector import (
    detect_candlestick_patterns,
    detect_all_patterns,
)
from backend.calibration.calibrator import (
    calibrate_forecast,
    compute_wilson_score_interval,
)


@pytest.fixture
def sample_ohlcv_df():
    """Generates synthetic trending OHLCV dataframe."""
    np.random.seed(42)
    n = 100
    base = 60000.0
    drift = np.cumsum(np.random.randn(n) * 150 + 20)
    closes = base + drift
    opens = closes - np.random.randn(n) * 50
    highs = np.maximum(opens, closes) + np.random.rand(n) * 80
    lows = np.minimum(opens, closes) - np.random.rand(n) * 80
    volumes = np.random.rand(n) * 500 + 50
    amounts = volumes * closes
    times = [1700000000000 + i * 4 * 3600 * 1000 for i in range(n)]

    df = pd.DataFrame({
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
        "amount": amounts,
        "open_time": times,
        "close_time": [t + 4 * 3600 * 1000 - 1 for t in times],
        "is_closed": [1] * n,
    })
    df["timestamps"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    return df


def test_technical_indicators(sample_ohlcv_df):
    df_ind = compute_indicators(sample_ohlcv_df)
    assert "ema_20" in df_ind.columns
    assert "ema_50" in df_ind.columns
    assert "ema_200" in df_ind.columns
    assert "rsi_14" in df_ind.columns
    assert "macd" in df_ind.columns
    assert "bb_upper" in df_ind.columns
    assert "adx_14" in df_ind.columns
    assert "rvol" in df_ind.columns

    # RSI must strictly be between 0 and 100
    valid_rsi = df_ind["rsi_14"].dropna()
    assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()

    # Bollinger Bands check: upper >= middle >= lower
    valid_bb = df_ind.dropna(subset=["bb_upper", "bb_middle", "bb_lower"])
    assert (valid_bb["bb_upper"] >= valid_bb["bb_middle"]).all()
    assert (valid_bb["bb_middle"] >= valid_bb["bb_lower"]).all()


def test_market_structure_no_future_leakage(sample_ohlcv_df):
    pivots = detect_pivots(sample_ohlcv_df, window=3)
    assert len(pivots) > 0

    # Ensure pivot confirmation time is strictly after the pivot open time
    for p in pivots:
        assert p.confirmation_time > p.open_time

    analysis = analyze_market_structure(compute_indicators(sample_ohlcv_df))
    assert analysis.regime in ["TRENDING_BULL", "TRENDING_BEAR", "CONSOLIDATION", "VOLATILITY_SQUEEZE"]
    assert analysis.trend in ["BULLISH", "BEARISH", "NEUTRAL"]


def test_pattern_detection(sample_ohlcv_df):
    patterns = detect_all_patterns(sample_ohlcv_df, timeframe="4h")
    assert isinstance(patterns, list)
    for p in patterns:
        assert p.stance in ["BULLISH", "BEARISH", "NEUTRAL"]
        assert p.quality_score >= 0.0 and p.quality_score <= 1.0
        assert p.confirmation_time >= p.formation_start


def test_calibrated_confidence_threshold():
    # Test insufficient data threshold
    res_empty = calibrate_forecast(65000, 64000, [], min_samples=20)
    assert not res_empty.is_available
    assert res_empty.directional_probability is None
    assert "Insufficient validation data" in res_empty.diagnostic_message

    # Test sufficient synthetic validation records
    records = []
    for _ in range(30):
        records.append({
            "pred_return": 0.03,
            "realized_return": 0.02,
            "residual": -0.01
        })
    res_cal = calibrate_forecast(65000, 64000, records, min_samples=20)
    assert res_cal.is_available
    assert res_cal.directional_probability == 1.0  # All predicted positive and realized positive
    assert res_cal.sample_count == 30


def test_wilson_interval():
    low, high = compute_wilson_score_interval(0.6, 100)
    assert 0.0 < low < 0.6 < high < 1.0

