"""Pattern Detection Engine for APEX.
Algorithmic detection of candlestick patterns and chart formations.
Every pattern contains:
- pattern_name
- stance: BULLISH, BEARISH, NEUTRAL
- timeframe
- formation_start (timestamp)
- confirmation_time (timestamp)
- price_levels: dict
- detection_conditions: dict
- quality_score: 0.0 to 1.0
- is_confirmed: bool
"""
import uuid
import time
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel


class PatternDetection(BaseModel):
    id: str
    pattern_name: str
    pattern_category: str  # 'CANDLESTICK' or 'CHART_FORMATION'
    stance: str            # 'BULLISH', 'BEARISH', 'NEUTRAL'
    timeframe: str
    formation_start: int
    confirmation_time: int
    price_levels: Dict[str, float]
    detection_conditions: Dict[str, Any]
    quality_score: float
    is_confirmed: bool


def detect_candlestick_patterns(df: pd.DataFrame, timeframe: str) -> List[PatternDetection]:
    """Detect single and multi-bar candlestick patterns on closed candles."""
    patterns: List[PatternDetection] = []
    n = len(df)
    if n < 4:
        return patterns

    opens = df["open"].values
    highs = df["high"].values
    lows = df["low"].values
    closes = df["close"].values
    times = df["open_time"].values

    for i in range(2, n):
        o1, h1, l1, c1, t1 = opens[i - 1], highs[i - 1], lows[i - 1], closes[i - 1], int(times[i - 1])
        o2, h2, l2, c2, t2 = opens[i], highs[i], lows[i], closes[i], int(times[i])

        body1 = abs(c1 - o1)
        body2 = abs(c2 - o2)
        range1 = h1 - l1 + 1e-9
        range2 = h2 - l2 + 1e-9

        # 1. Bullish Engulfing
        # Condition: Prior bar red, current bar green, current body engulfs prior body
        if (c1 < o1) and (c2 > o2) and (o2 <= c1) and (c2 >= o1) and (body2 > body1 * 1.05):
            score = min(1.0, 0.6 + 0.4 * (body2 / range2))
            patterns.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Bullish Engulfing",
                pattern_category="CANDLESTICK",
                stance="BULLISH",
                timeframe=timeframe,
                formation_start=t1,
                confirmation_time=t2,
                price_levels={"breakout_trigger": round(h2, 2), "invalidation": round(l2, 2)},
                detection_conditions={"prior_candle_red": True, "engulfing_ratio": round(body2 / (body1 + 1e-9), 2)},
                quality_score=round(score, 2),
                is_confirmed=True,
            ))

        # 2. Bearish Engulfing
        # Condition: Prior bar green, current bar red, current body engulfs prior body
        if (c1 > o1) and (c2 < o2) and (o2 >= c1) and (c2 <= o1) and (body2 > body1 * 1.05):
            score = min(1.0, 0.6 + 0.4 * (body2 / range2))
            patterns.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Bearish Engulfing",
                pattern_category="CANDLESTICK",
                stance="BEARISH",
                timeframe=timeframe,
                formation_start=t1,
                confirmation_time=t2,
                price_levels={"breakdown_trigger": round(l2, 2), "invalidation": round(h2, 2)},
                detection_conditions={"prior_candle_green": True, "engulfing_ratio": round(body2 / (body1 + 1e-9), 2)},
                quality_score=round(score, 2),
                is_confirmed=True,
            ))

        # 3. Hammer (Bullish Reversal)
        # Condition: Small body at upper end of candle, lower shadow >= 2x body, upper shadow <= 0.1x range
        lower_shadow2 = min(o2, c2) - l2
        upper_shadow2 = h2 - max(o2, c2)
        if lower_shadow2 >= 2.0 * body2 and upper_shadow2 <= 0.15 * range2 and body2 > 0:
            score = min(1.0, 0.5 + 0.5 * (lower_shadow2 / range2))
            patterns.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Hammer",
                pattern_category="CANDLESTICK",
                stance="BULLISH",
                timeframe=timeframe,
                formation_start=t2,
                confirmation_time=t2,
                price_levels={"rejection_low": round(l2, 2), "trigger_high": round(h2, 2)},
                detection_conditions={"lower_shadow_ratio": round(lower_shadow2 / range2, 2)},
                quality_score=round(score, 2),
                is_confirmed=True,
            ))

        # 4. Shooting Star (Bearish Reversal)
        # Condition: Small body at lower end of candle, upper shadow >= 2x body, lower shadow <= 0.1x range
        if upper_shadow2 >= 2.0 * body2 and lower_shadow2 <= 0.15 * range2 and body2 > 0:
            score = min(1.0, 0.5 + 0.5 * (upper_shadow2 / range2))
            patterns.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Shooting Star",
                pattern_category="CANDLESTICK",
                stance="BEARISH",
                timeframe=timeframe,
                formation_start=t2,
                confirmation_time=t2,
                price_levels={"rejection_high": round(h2, 2), "trigger_low": round(l2, 2)},
                detection_conditions={"upper_shadow_ratio": round(upper_shadow2 / range2, 2)},
                quality_score=round(score, 2),
                is_confirmed=True,
            ))

        # 5. Doji (Indecision)
        # Condition: Body is <= 10% of total candle range
        if body2 <= 0.10 * range2:
            score = round(1.0 - (body2 / range2), 2)
            patterns.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Doji",
                pattern_category="CANDLESTICK",
                stance="NEUTRAL",
                timeframe=timeframe,
                formation_start=t2,
                confirmation_time=t2,
                price_levels={"doji_level": round((o2 + c2) / 2.0, 2), "range_high": round(h2, 2), "range_low": round(l2, 2)},
                detection_conditions={"body_to_range_ratio": round(body2 / range2, 3)},
                quality_score=round(score, 2),
                is_confirmed=True,
            ))

        # 6. Inside Bar
        # Condition: Bar 2's range is entirely within Bar 1's range
        if (h2 <= h1) and (l2 >= l1):
            score = round(1.0 - (range2 / range1), 2)
            patterns.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Inside Bar",
                pattern_category="CANDLESTICK",
                stance="NEUTRAL",
                timeframe=timeframe,
                formation_start=t1,
                confirmation_time=t2,
                price_levels={"mother_high": round(h1, 2), "mother_low": round(l1, 2)},
                detection_conditions={"compression_ratio": round(range2 / range1, 2)},
                quality_score=round(max(0.5, score), 2),
                is_confirmed=True,
            ))

        # 7. Outside Bar
        # Condition: Bar 2 completely engulfs both the high and low of Bar 1
        if (h2 > h1) and (l2 < l1):
            stance = "BULLISH" if c2 > o2 else "BEARISH"
            patterns.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Outside Bar",
                pattern_category="CANDLESTICK",
                stance=stance,
                timeframe=timeframe,
                formation_start=t1,
                confirmation_time=t2,
                price_levels={"range_high": round(h2, 2), "range_low": round(l2, 2)},
                detection_conditions={"expansion_ratio": round(range2 / range1, 2)},
                quality_score=0.75,
                is_confirmed=True,
            ))

        # 8. Morning Star (3-candle bullish reversal)
        if i >= 2:
            o0, h0, l0, c0, t0 = opens[i - 2], highs[i - 2], lows[i - 2], closes[i - 2], int(times[i - 2])
            body0 = abs(c0 - o0)
            # Candle 0 is long red
            # Candle 1 has small body gapping below candle 0
            # Candle 2 is long green closing above midpoint of candle 0
            if (c0 < o0) and (body1 <= 0.35 * body0) and (c2 > o2) and (c2 >= o0 - 0.5 * body0):
                patterns.append(PatternDetection(
                    id=str(uuid.uuid4())[:12],
                    pattern_name="Morning Star",
                    pattern_category="CANDLESTICK",
                    stance="BULLISH",
                    timeframe=timeframe,
                    formation_start=t0,
                    confirmation_time=t2,
                    price_levels={"star_low": round(min(l0, l1, l2), 2), "target": round(h0, 2)},
                    detection_conditions={"midpoint_penetration": True},
                    quality_score=0.85,
                    is_confirmed=True,
                ))

            # 9. Evening Star (3-candle bearish reversal)
            if (c0 > o0) and (body1 <= 0.35 * body0) and (c2 < o2) and (c2 <= o0 + 0.5 * body0):
                patterns.append(PatternDetection(
                    id=str(uuid.uuid4())[:12],
                    pattern_name="Evening Star",
                    pattern_category="CANDLESTICK",
                    stance="BEARISH",
                    timeframe=timeframe,
                    formation_start=t0,
                    confirmation_time=t2,
                    price_levels={"star_high": round(max(h0, h1, h2), 2), "target": round(l0, 2)},
                    detection_conditions={"midpoint_penetration": True},
                    quality_score=0.85,
                    is_confirmed=True,
                ))

    return patterns


def detect_chart_formations(df: pd.DataFrame, timeframe: str) -> List[PatternDetection]:
    """Detect classical chart formations (Double Top/Bottom, Triangles, Flags) from confirmed pivots."""
    formations: List[PatternDetection] = []
    if len(df) < 30:
        return formations

    from backend.market_structure.structure import detect_pivots
    pivots = detect_pivots(df, window=3)
    if len(pivots) < 4:
        return formations

    high_pivots = [p for p in pivots if p.type == "HIGH"]
    low_pivots = [p for p in pivots if p.type == "LOW"]

    # 1. Double Top
    if len(high_pivots) >= 2:
        p1, p2 = high_pivots[-2], high_pivots[-1]
        price_diff = abs(p1.price - p2.price) / p1.price
        # Between the two highs there must be an intermediate low
        inter_lows = [p for p in low_pivots if p1.open_time < p.open_time < p2.open_time]
        if price_diff <= 0.015 and inter_lows:
            neckline = inter_lows[0].price
            curr_close = float(df["close"].iloc[-1])
            is_confirmed = curr_close < neckline
            formations.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Double Top",
                pattern_category="CHART_FORMATION",
                stance="BEARISH",
                timeframe=timeframe,
                formation_start=p1.open_time,
                confirmation_time=p2.confirmation_time,
                price_levels={"peak_1": p1.price, "peak_2": p2.price, "neckline": neckline},
                detection_conditions={"peak_symmetry_pct": round(price_diff * 100, 2), "inter_low_found": True},
                quality_score=0.80 if is_confirmed else 0.60,
                is_confirmed=is_confirmed,
            ))

    # 2. Double Bottom
    if len(low_pivots) >= 2:
        p1, p2 = low_pivots[-2], low_pivots[-1]
        price_diff = abs(p1.price - p2.price) / p1.price
        inter_highs = [p for p in high_pivots if p1.open_time < p.open_time < p2.open_time]
        if price_diff <= 0.015 and inter_highs:
            neckline = inter_highs[0].price
            curr_close = float(df["close"].iloc[-1])
            is_confirmed = curr_close > neckline
            formations.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Double Bottom",
                pattern_category="CHART_FORMATION",
                stance="BULLISH",
                timeframe=timeframe,
                formation_start=p1.open_time,
                confirmation_time=p2.confirmation_time,
                price_levels={"trough_1": p1.price, "trough_2": p2.price, "neckline": neckline},
                detection_conditions={"trough_symmetry_pct": round(price_diff * 100, 2), "inter_high_found": True},
                quality_score=0.80 if is_confirmed else 0.60,
                is_confirmed=is_confirmed,
            ))

    # 3. Ascending Triangle (Flat resistance, higher lows)
    if len(high_pivots) >= 2 and len(low_pivots) >= 2:
        h1, h2 = high_pivots[-2], high_pivots[-1]
        l1, l2 = low_pivots[-2], low_pivots[-1]
        high_diff = abs(h1.price - h2.price) / h1.price
        if high_diff <= 0.015 and l2.price > l1.price:
            formations.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Ascending Triangle",
                pattern_category="CHART_FORMATION",
                stance="BULLISH",
                timeframe=timeframe,
                formation_start=min(h1.open_time, l1.open_time),
                confirmation_time=max(h2.confirmation_time, l2.confirmation_time),
                price_levels={"horizontal_resistance": round((h1.price + h2.price) / 2, 2), "ascending_low": l2.price},
                detection_conditions={"higher_lows": True, "flat_ceiling": True},
                quality_score=0.75,
                is_confirmed=float(df["close"].iloc[-1]) > max(h1.price, h2.price),
            ))

    # 4. Descending Triangle (Flat support floor, lower highs)
    if len(high_pivots) >= 2 and len(low_pivots) >= 2:
        h1, h2 = high_pivots[-2], high_pivots[-1]
        l1, l2 = low_pivots[-2], low_pivots[-1]
        low_diff = abs(l1.price - l2.price) / l1.price
        if low_diff <= 0.015 and h2.price < h1.price:
            formations.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Descending Triangle",
                pattern_category="CHART_FORMATION",
                stance="BEARISH",
                timeframe=timeframe,
                formation_start=min(h1.open_time, l1.open_time),
                confirmation_time=max(h2.confirmation_time, l2.confirmation_time),
                price_levels={"horizontal_support": round((l1.price + l2.price) / 2, 2), "descending_high": h2.price},
                detection_conditions={"lower_highs": True, "flat_floor": True},
                quality_score=0.75,
                is_confirmed=float(df["close"].iloc[-1]) < min(l1.price, l2.price),
            ))

    # 5. Symmetrical Triangle (Lower highs and higher lows converging)
    if len(high_pivots) >= 2 and len(low_pivots) >= 2:
        h1, h2 = high_pivots[-2], high_pivots[-1]
        l1, l2 = low_pivots[-2], low_pivots[-1]
        if h2.price < h1.price and l2.price > l1.price:
            # Check converging range
            range_start = h1.price - l1.price
            range_end = h2.price - l2.price
            if 0 < range_end < range_start:
                curr_close = float(df["close"].iloc[-1])
                is_breakout_up = curr_close > h2.price
                is_breakdown_dn = curr_close < l2.price
                stance = "BULLISH" if is_breakout_up else ("BEARISH" if is_breakdown_dn else "NEUTRAL")
                formations.append(PatternDetection(
                    id=str(uuid.uuid4())[:12],
                    pattern_name="Symmetrical Triangle",
                    pattern_category="CHART_FORMATION",
                    stance=stance,
                    timeframe=timeframe,
                    formation_start=min(h1.open_time, l1.open_time),
                    confirmation_time=max(h2.confirmation_time, l2.confirmation_time),
                    price_levels={"upper_trendline": h2.price, "lower_trendline": l2.price},
                    detection_conditions={"compression_ratio": round(range_end / range_start, 2)},
                    quality_score=0.70,
                    is_confirmed=is_breakout_up or is_breakdown_dn,
                ))

    # 6. Head and Shoulders (Left Shoulder, Head, Right Shoulder)
    if len(high_pivots) >= 3:
        ls, head, rs = high_pivots[-3], high_pivots[-2], high_pivots[-1]
        if head.price > ls.price and head.price > rs.price:
            shoulder_symmetry = abs(ls.price - rs.price) / ls.price
            if shoulder_symmetry <= 0.04:
                # Find neckline lows
                troughs = [p for p in low_pivots if ls.open_time < p.open_time < rs.open_time]
                if len(troughs) >= 2:
                    nl = round((troughs[0].price + troughs[1].price) / 2.0, 2)
                    curr_close = float(df["close"].iloc[-1])
                    is_confirmed = curr_close < nl
                    formations.append(PatternDetection(
                        id=str(uuid.uuid4())[:12],
                        pattern_name="Head and Shoulders",
                        pattern_category="CHART_FORMATION",
                        stance="BEARISH",
                        timeframe=timeframe,
                        formation_start=ls.open_time,
                        confirmation_time=rs.confirmation_time,
                        price_levels={"left_shoulder": ls.price, "head": head.price, "right_shoulder": rs.price, "neckline": nl},
                        detection_conditions={"shoulder_symmetry_pct": round(shoulder_symmetry * 100, 2), "troughs_count": len(troughs)},
                        quality_score=0.85 if is_confirmed else 0.65,
                        is_confirmed=is_confirmed,
                    ))

    # 7. Inverse Head and Shoulders
    if len(low_pivots) >= 3:
        ls, head, rs = low_pivots[-3], low_pivots[-2], low_pivots[-1]
        if head.price < ls.price and head.price < rs.price:
            shoulder_symmetry = abs(ls.price - rs.price) / ls.price
            if shoulder_symmetry <= 0.04:
                peaks = [p for p in high_pivots if ls.open_time < p.open_time < rs.open_time]
                if len(peaks) >= 2:
                    nl = round((peaks[0].price + peaks[1].price) / 2.0, 2)
                    curr_close = float(df["close"].iloc[-1])
                    is_confirmed = curr_close > nl
                    formations.append(PatternDetection(
                        id=str(uuid.uuid4())[:12],
                        pattern_name="Inverse Head and Shoulders",
                        pattern_category="CHART_FORMATION",
                        stance="BULLISH",
                        timeframe=timeframe,
                        formation_start=ls.open_time,
                        confirmation_time=rs.confirmation_time,
                        price_levels={"left_shoulder": ls.price, "head": head.price, "right_shoulder": rs.price, "neckline": nl},
                        detection_conditions={"shoulder_symmetry_pct": round(shoulder_symmetry * 100, 2), "peaks_count": len(peaks)},
                        quality_score=0.85 if is_confirmed else 0.65,
                        is_confirmed=is_confirmed,
                    ))

    # 8. Rising Wedge (Higher highs & higher lows converging upward, bearish reversal/continuation)
    if len(high_pivots) >= 2 and len(low_pivots) >= 2:
        h1, h2 = high_pivots[-2], high_pivots[-1]
        l1, l2 = low_pivots[-2], low_pivots[-1]
        if h2.price > h1.price and l2.price > l1.price:
            high_slope = (h2.price - h1.price) / h1.price
            low_slope = (l2.price - l1.price) / l1.price
            if low_slope > high_slope:  # Lows rising faster than highs = converging upward
                curr_close = float(df["close"].iloc[-1])
                is_confirmed = curr_close < l2.price
                formations.append(PatternDetection(
                    id=str(uuid.uuid4())[:12],
                    pattern_name="Rising Wedge",
                    pattern_category="CHART_FORMATION",
                    stance="BEARISH",
                    timeframe=timeframe,
                    formation_start=min(h1.open_time, l1.open_time),
                    confirmation_time=max(h2.confirmation_time, l2.confirmation_time),
                    price_levels={"wedge_upper": h2.price, "wedge_lower": l2.price},
                    detection_conditions={"converging_up": True, "high_slope": round(high_slope, 4), "low_slope": round(low_slope, 4)},
                    quality_score=0.76 if is_confirmed else 0.60,
                    is_confirmed=is_confirmed,
                ))

    # 9. Falling Wedge (Lower highs & lower lows converging downward, bullish reversal/continuation)
    if len(high_pivots) >= 2 and len(low_pivots) >= 2:
        h1, h2 = high_pivots[-2], high_pivots[-1]
        l1, l2 = low_pivots[-2], low_pivots[-1]
        if h2.price < h1.price and l2.price < l1.price:
            high_drop = (h1.price - h2.price) / h1.price
            low_drop = (l1.price - l2.price) / l1.price
            if high_drop > low_drop:  # Highs falling faster than lows = converging downward
                curr_close = float(df["close"].iloc[-1])
                is_confirmed = curr_close > h2.price
                formations.append(PatternDetection(
                    id=str(uuid.uuid4())[:12],
                    pattern_name="Falling Wedge",
                    pattern_category="CHART_FORMATION",
                    stance="BULLISH",
                    timeframe=timeframe,
                    formation_start=min(h1.open_time, l1.open_time),
                    confirmation_time=max(h2.confirmation_time, l2.confirmation_time),
                    price_levels={"wedge_upper": h2.price, "wedge_lower": l2.price},
                    detection_conditions={"converging_down": True, "high_drop": round(high_drop, 4), "low_drop": round(low_drop, 4)},
                    quality_score=0.76 if is_confirmed else 0.60,
                    is_confirmed=is_confirmed,
                ))

    # 10. Bullish Flag
    # Strong prior impulse up followed by tight downward consolidation
    if len(df) >= 20:
        impulse_return = (df["close"].iloc[-10] - df["close"].iloc[-20]) / df["close"].iloc[-20]
        recent_consolidation_return = (df["close"].iloc[-1] - df["close"].iloc[-10]) / df["close"].iloc[-10]
        if impulse_return >= 0.04 and -0.03 <= recent_consolidation_return <= 0.005:
            formations.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Bullish Flag",
                pattern_category="CHART_FORMATION",
                stance="BULLISH",
                timeframe=timeframe,
                formation_start=int(df["open_time"].iloc[-20]),
                confirmation_time=int(df["open_time"].iloc[-1]),
                price_levels={"pole_base": float(df["close"].iloc[-20]), "flag_high": float(df["high"].iloc[-10]), "flag_low": float(df["low"].iloc[-5:].min())},
                detection_conditions={"impulse_pct": round(impulse_return * 100, 2), "consolidation_pct": round(recent_consolidation_return * 100, 2)},
                quality_score=0.78,
                is_confirmed=float(df["close"].iloc[-1]) > float(df["high"].iloc[-5]),
            ))

    # 11. Bearish Flag
    # Strong prior impulse down followed by tight upward consolidation
    if len(df) >= 20:
        impulse_return = (df["close"].iloc[-10] - df["close"].iloc[-20]) / df["close"].iloc[-20]
        recent_consolidation_return = (df["close"].iloc[-1] - df["close"].iloc[-10]) / df["close"].iloc[-10]
        if impulse_return <= -0.04 and -0.005 <= recent_consolidation_return <= 0.03:
            formations.append(PatternDetection(
                id=str(uuid.uuid4())[:12],
                pattern_name="Bearish Flag",
                pattern_category="CHART_FORMATION",
                stance="BEARISH",
                timeframe=timeframe,
                formation_start=int(df["open_time"].iloc[-20]),
                confirmation_time=int(df["open_time"].iloc[-1]),
                price_levels={"pole_base": float(df["close"].iloc[-20]), "flag_low": float(df["low"].iloc[-10]), "flag_high": float(df["high"].iloc[-5:].max())},
                detection_conditions={"impulse_pct": round(impulse_return * 100, 2), "consolidation_pct": round(recent_consolidation_return * 100, 2)},
                quality_score=0.78,
                is_confirmed=float(df["close"].iloc[-1]) < float(df["low"].iloc[-5]),
            ))

    return formations


def detect_all_patterns(df: pd.DataFrame, timeframe: str) -> List[PatternDetection]:
    """Detect and aggregate both candlestick patterns and chart formations."""
    candlesticks = detect_candlestick_patterns(df, timeframe)
    formations = detect_chart_formations(df, timeframe)
    combined = candlesticks + formations
    # Sort chronologically by confirmation time descending (newest first)
    combined.sort(key=lambda p: p.confirmation_time, reverse=True)
    return combined

