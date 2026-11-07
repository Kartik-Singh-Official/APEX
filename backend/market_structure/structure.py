"""Market Structure Analysis Engine for APEX.
Algorithmically detects:
- Confirmed Swing Highs & Lows (zero lookahead bias)
- Higher Highs (HH), Higher Lows (HL), Lower Highs (LH), Lower Lows (LL)
- Break of Structure (BOS) and Change of Character (CHoCH)
- Support & Resistance Zones derived from confirmed pivot clusters
- Volatility Expansion & Contraction
- Overall Market Regime
"""
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel


class SwingPivot(BaseModel):
    index: int
    open_time: int
    confirmation_time: int
    type: str  # 'HIGH' or 'LOW'
    price: float
    classification: Optional[str] = None  # 'HH', 'LH', 'HL', 'LL'


class SRZone(BaseModel):
    level: float
    zone_low: float
    zone_high: float
    type: str  # 'SUPPORT' or 'RESISTANCE'
    touch_count: int
    strength: float  # 0.0 to 1.0


class MarketStructureAnalysis(BaseModel):
    regime: str  # 'TRENDING_BULL', 'TRENDING_BEAR', 'CONSOLIDATION', 'VOLATILITY_SQUEEZE'
    trend: str   # 'BULLISH', 'BEARISH', 'NEUTRAL'
    swing_pivots: List[SwingPivot]
    support_resistance: List[SRZone]
    last_bos: Optional[Dict[str, Any]] = None
    last_choch: Optional[Dict[str, Any]] = None
    volatility_state: str  # 'EXPANSION', 'CONTRACTION', 'NORMAL'
    atr_percentile: float
    range_high: float
    range_low: float


def detect_pivots(df: pd.DataFrame, window: int = 3) -> List[SwingPivot]:
    """Detect confirmed swing pivots strictly without future leakage.
    Pivot at bar i is confirmed only after window subsequent bars have closed.
    """
    pivots: List[SwingPivot] = []
    n = len(df)
    if n < window * 2 + 1:
        return pivots

    highs = df["high"].values
    lows = df["low"].values
    times = df["open_time"].values

    for i in range(window, n - window):
        # Swing High
        is_high = True
        curr_high = highs[i]
        for w in range(1, window + 1):
            if highs[i - w] >= curr_high or highs[i + w] >= curr_high:
                is_high = False
                break
        if is_high:
            # Confirmation time is the close time of bar i + window
            conf_time = int(times[i + window])
            pivots.append(SwingPivot(
                index=i,
                open_time=int(times[i]),
                confirmation_time=conf_time,
                type="HIGH",
                price=float(curr_high),
            ))

        # Swing Low
        is_low = True
        curr_low = lows[i]
        for w in range(1, window + 1):
            if lows[i - w] <= curr_low or lows[i + w] <= curr_low:
                is_low = False
                break
        if is_low:
            conf_time = int(times[i + window])
            pivots.append(SwingPivot(
                index=i,
                open_time=int(times[i]),
                confirmation_time=conf_time,
                type="LOW",
                price=float(curr_low),
            ))

    # Sort chronologically by bar index
    pivots.sort(key=lambda p: p.index)

    # Classify HH, LH, HL, LL
    last_high: Optional[float] = None
    last_low: Optional[float] = None

    for p in pivots:
        if p.type == "HIGH":
            if last_high is not None:
                p.classification = "HH" if p.price > last_high else "LH"
            else:
                p.classification = "HIGH"
            last_high = p.price
        elif p.type == "LOW":
            if last_low is not None:
                p.classification = "HL" if p.price > last_low else "LL"
            else:
                p.classification = "LOW"
            last_low = p.price

    return pivots


def derive_sr_zones(df: pd.DataFrame, pivots: List[SwingPivot], tolerance_pct: float = 0.015) -> List[SRZone]:
    """Cluster confirmed pivot prices into Support and Resistance zones."""
    if not pivots:
        return []

    current_price = float(df["close"].iloc[-1])
    high_prices = [p.price for p in pivots if p.type == "HIGH"]
    low_prices = [p.price for p in pivots if p.type == "LOW"]

    zones: List[SRZone] = []

    def cluster_prices(prices: List[float], sr_type: str):
        if not prices:
            return
        sorted_p = sorted(prices)
        clusters = []
        current_cluster = [sorted_p[0]]

        for price in sorted_p[1:]:
            cluster_mean = sum(current_cluster) / len(current_cluster)
            if abs(price - cluster_mean) / cluster_mean <= tolerance_pct:
                current_cluster.append(price)
            else:
                clusters.append(current_cluster)
                current_cluster = [price]
        clusters.append(current_cluster)

        for c in clusters:
            touch_count = len(c)
            avg_price = sum(c) / touch_count
            min_p = min(c) * (1 - 0.002)
            max_p = max(c) * (1 + 0.002)
            # Strength score: scaled by touches and proximity to current price
            strength = min(1.0, 0.4 + 0.15 * touch_count)
            zones.append(SRZone(
                level=round(avg_price, 2),
                zone_low=round(min_p, 2),
                zone_high=round(max_p, 2),
                type=sr_type,
                touch_count=touch_count,
                strength=round(strength, 2)
            ))

    cluster_prices([p for p in high_prices if p >= current_price], "RESISTANCE")
    cluster_prices([p for p in low_prices if p <= current_price], "SUPPORT")

    # Sort resistances ascending from price, supports descending from price
    resistances = sorted([z for z in zones if z.type == "RESISTANCE"], key=lambda z: z.level)
    supports = sorted([z for z in zones if z.type == "SUPPORT"], key=lambda z: -z.level)

    return (resistances[:3] + supports[:3])


def analyze_market_structure(df: pd.DataFrame) -> MarketStructureAnalysis:
    """Analyze complete market structure, BOS, CHoCH, volatility, and regime."""
    if len(df) < 20:
        return MarketStructureAnalysis(
            regime="CONSOLIDATION",
            trend="NEUTRAL",
            swing_pivots=[],
            support_resistance=[],
            volatility_state="NORMAL",
            atr_percentile=50.0,
            range_high=float(df["high"].max() if len(df) else 0),
            range_low=float(df["low"].min() if len(df) else 0)
        )

    pivots = detect_pivots(df, window=3)
    sr_zones = derive_sr_zones(df, pivots)

    # Trend determination from last 4 pivots
    recent_pivots = pivots[-4:] if len(pivots) >= 4 else pivots
    hh_count = sum(1 for p in recent_pivots if p.classification == "HH")
    hl_count = sum(1 for p in recent_pivots if p.classification == "HL")
    lh_count = sum(1 for p in recent_pivots if p.classification == "LH")
    ll_count = sum(1 for p in recent_pivots if p.classification == "LL")

    trend = "NEUTRAL"
    if (hh_count + hl_count) > (lh_count + ll_count):
        trend = "BULLISH"
    elif (lh_count + ll_count) > (hh_count + hl_count):
        trend = "BEARISH"

    # Detect BOS and CHoCH
    last_bos = None
    last_choch = None
    current_close = float(df["close"].iloc[-1])
    recent_highs = [p for p in pivots if p.type == "HIGH"]
    recent_lows = [p for p in pivots if p.type == "LOW"]

    if recent_highs:
        prev_swing_high = recent_highs[-1]
        if current_close > prev_swing_high.price:
            if trend == "BULLISH":
                last_bos = {
                    "type": "BULLISH_BOS",
                    "breakout_level": prev_swing_high.price,
                    "pivot_time": prev_swing_high.open_time,
                }
            elif trend == "BEARISH":
                last_choch = {
                    "type": "BULLISH_CHOCH",
                    "breakout_level": prev_swing_high.price,
                    "pivot_time": prev_swing_high.open_time,
                }

    if recent_lows:
        prev_swing_low = recent_lows[-1]
        if current_close < prev_swing_low.price:
            if trend == "BEARISH":
                last_bos = {
                    "type": "BEARISH_BOS",
                    "breakdown_level": prev_swing_low.price,
                    "pivot_time": prev_swing_low.open_time,
                }
            elif trend == "BULLISH":
                last_choch = {
                    "type": "BEARISH_CHOCH",
                    "breakdown_level": prev_swing_low.price,
                    "pivot_time": prev_swing_low.open_time,
                }

    # Volatility analysis
    if "atr_14" in df.columns:
        atr_series = df["atr_14"].dropna()
        if len(atr_series) > 10:
            current_atr = atr_series.iloc[-1]
            atr_percentile = float((atr_series < current_atr).mean() * 100.0)
        else:
            atr_percentile = 50.0
    else:
        atr_percentile = 50.0

    vol_state = "NORMAL"
    if atr_percentile >= 75.0:
        vol_state = "EXPANSION"
    elif atr_percentile <= 25.0:
        vol_state = "CONTRACTION"

    # Regime synthesis
    if vol_state == "CONTRACTION":
        regime = "VOLATILITY_SQUEEZE"
    elif trend == "BULLISH":
        regime = "TRENDING_BULL"
    elif trend == "BEARISH":
        regime = "TRENDING_BEAR"
    else:
        regime = "CONSOLIDATION"

    range_high = float(df["high"].tail(50).max())
    range_low = float(df["low"].tail(50).min())

    return MarketStructureAnalysis(
        regime=regime,
        trend=trend,
        swing_pivots=pivots,
        support_resistance=sr_zones,
        last_bos=last_bos,
        last_choch=last_choch,
        volatility_state=vol_state,
        atr_percentile=round(atr_percentile, 1),
        range_high=range_high,
        range_low=range_low,
    )
