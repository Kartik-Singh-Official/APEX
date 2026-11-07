"""Market Intelligence & Evidence-Based Synthesis Engine for APEX.
Synthesizes Kronos forecasts, technical indicators, pattern detections, and market structure
into a transparent, auditable research thesis.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.calibration.calibrator import CalibratedConfidence
from backend.market_structure.structure import MarketStructureAnalysis
from backend.patterns.detector import PatternDetection


class SynthesisResult(BaseModel):
    symbol: str
    timeframe: str
    horizon_label: str
    expiry_time: int
    research_stance: str  # 'STRONG_BULLISH', 'BULLISH', 'NEUTRAL', 'BEARISH', 'STRONG_BEARISH', 'NO_SIGNAL'
    market_regime: str
    forecasted_direction: str  # 'UP', 'DOWN', 'FLAT'
    expected_return_pct: float
    expected_price_target: float
    expected_range_low: float
    expected_range_high: float
    var_95_pct: float
    calibrated_prob: Optional[float]
    sample_count: int
    confidence_interval_str: str
    detected_patterns: List[str]
    supporting_factors: List[str]
    conflicting_factors: List[str]
    invalidation_conditions: str
    data_quality_status: str
    explanation_narrative: str


def synthesize_market_intelligence(
    symbol: str,
    timeframe: str,
    horizon_label: str,
    current_price: float,
    pred_final_price: float,
    pred_expiry_time: int,
    structure: MarketStructureAnalysis,
    patterns: List[PatternDetection],
    indicators: Dict[str, Any],
    confidence: CalibratedConfidence,
    data_quality: str = "VALID"
) -> SynthesisResult:
    """Combine computed quantitative telemetry into structured stance and narrative."""
    expected_return = (pred_final_price - current_price) / current_price
    expected_return_pct = round(expected_return * 100.0, 2)

    if expected_return > 0.005:
        forecast_dir = "UP"
    elif expected_return < -0.005:
        forecast_dir = "DOWN"
    else:
        forecast_dir = "FLAT"

    # Evaluate factors
    supporting = []
    conflicting = []

    # 1. Moving average alignment
    ema20 = indicators.get("ema_20")
    ema50 = indicators.get("ema_50")
    ema200 = indicators.get("ema_200")
    rsi14 = indicators.get("rsi_14", 50.0)
    adx14 = indicators.get("adx_14", 20.0)
    rvol = indicators.get("rvol", 1.0)

    # Bullish criteria
    bullish_score = 0
    bearish_score = 0

    if forecast_dir == "UP":
        bullish_score += 2
        supporting.append(f"Kronos predicts positive return (+{expected_return_pct}%) over {horizon_label} horizon")
    elif forecast_dir == "DOWN":
        bearish_score += 2
        supporting.append(f"Kronos predicts negative return ({expected_return_pct}%) over {horizon_label} horizon")
    else:
        conflicting.append("Kronos forecast path indicates minimal price displacement (range-bound)")

    # Structure
    if structure.trend == "BULLISH":
        bullish_score += 2
        supporting.append(f"{timeframe} market structure confirms higher highs and higher lows")
    elif structure.trend == "BEARISH":
        bearish_score += 2
        supporting.append(f"{timeframe} market structure confirms lower highs and lower lows")

    # Moving averages
    if ema20 and ema50:
        if current_price > ema20 > ema50:
            bullish_score += 1
            supporting.append("Price is trading above ascending EMA 20 and EMA 50")
        elif current_price < ema20 < ema50:
            bearish_score += 1
            supporting.append("Price is trading below descending EMA 20 and EMA 50")
        else:
            conflicting.append("Moving average alignment shows compression/cross-traffic")

    # Momentum (RSI)
    if rsi14 > 55.0 and rsi14 < 75.0:
        bullish_score += 1
        supporting.append(f"RSI(14) is {rsi14:.1f}, indicating positive momentum without overextension")
    elif rsi14 < 45.0 and rsi14 > 25.0:
        bearish_score += 1
        supporting.append(f"RSI(14) is {rsi14:.1f}, indicating negative momentum without oversold exhaustion")
    elif rsi14 >= 75.0:
        conflicting.append(f"RSI(14) at {rsi14:.1f} shows overbought reading, elevating mean-reversion risk")
    elif rsi14 <= 25.0:
        conflicting.append(f"RSI(14) at {rsi14:.1f} shows oversold reading, elevating bounce risk")

    # Patterns
    confirmed_bull_patterns = [p for p in patterns if p.stance == "BULLISH" and p.is_confirmed]
    confirmed_bear_patterns = [p for p in patterns if p.stance == "BEARISH" and p.is_confirmed]

    for p in confirmed_bull_patterns[:2]:
        bullish_score += 1
        supporting.append(f"Confirmed pattern: {p.pattern_name} (quality {p.quality_score:.2f})")

    for p in confirmed_bear_patterns[:2]:
        bearish_score += 1
        if forecast_dir == "UP":
            conflicting.append(f"Contradictory pattern detected: {p.pattern_name} (quality {p.quality_score:.2f})")
        else:
            supporting.append(f"Confirmed pattern: {p.pattern_name} (quality {p.quality_score:.2f})")

    # Support / Resistance proximity
    nearest_res = next((z for z in structure.support_resistance if z.type == "RESISTANCE"), None)
    nearest_sup = next((z for z in structure.support_resistance if z.type == "SUPPORT"), None)

    if forecast_dir == "UP" and nearest_res:
        dist_res = (nearest_res.level - current_price) / current_price
        if dist_res < 0.015:
            conflicting.append(f"Price is within {dist_res*100:.1f}% of key overhead resistance at ${nearest_res.level:,.2f}")

    if forecast_dir == "DOWN" and nearest_sup:
        dist_sup = (current_price - nearest_sup.level) / current_price
        if dist_sup < 0.015:
            conflicting.append(f"Price is within {dist_sup*100:.1f}% of major support zone at ${nearest_sup.level:,.2f}")

    # Resolve stance
    diff = bullish_score - bearish_score
    if diff >= 4:
        stance = "STRONG_BULLISH"
    elif diff >= 2:
        stance = "BULLISH"
    elif diff <= -4:
        stance = "STRONG_BEARISH"
    elif diff <= -2:
        stance = "BEARISH"
    else:
        stance = "NEUTRAL"

    # Invalidation condition
    if stance in ["STRONG_BULLISH", "BULLISH"]:
        inv_level = nearest_sup.zone_low if nearest_sup else current_price * 0.98
        invalidation = f"Thesis invalidated on 4-hour close below confirmed swing support at ${inv_level:,.2f}."
    elif stance in ["STRONG_BEARISH", "BEARISH"]:
        inv_level = nearest_res.zone_high if nearest_res else current_price * 1.02
        invalidation = f"Thesis invalidated on 4-hour close above confirmed swing resistance at ${inv_level:,.2f}."
    else:
        invalidation = "Neutral research stance — wait for breakout confirmation outside consolidation range."

    # Formatted CI string
    if confidence.is_available and confidence.confidence_interval_low is not None:
        ci_str = f"[{confidence.confidence_interval_low * 100:.1f}%, {confidence.confidence_interval_high * 100:.1f}%]"
    else:
        ci_str = "N/A (Insufficient validation data)"

    # Formatted narrative
    pattern_names = [p.pattern_name for p in patterns[:3]]
    narrative = (
        f"{symbol} — {stance.replace('_', ' ').title()} research bias\n\n"
        f"The {timeframe} market structure is in a {structure.regime.replace('_', ' ').lower()} regime with {structure.trend.lower()} bias. "
        f"Price is currently trading at ${current_price:,.2f}.\n\n"
        f"Kronos forecasts a median path of ${pred_final_price:,.2f} ({expected_return_pct:+0.2f}%) over the {horizon_label} horizon. "
        f"Volatility is currently {structure.volatility_state.lower()} (ATR percentile {structure.atr_percentile:.0f}%).\n\n"
        f"Directional reliability: {f'{confidence.directional_probability * 100:.1f}% (N={confidence.sample_count})' if confidence.is_available else 'Confidence unavailable — insufficient historical evaluation samples'}.\n"
        f"Invalidation: {invalidation}"
    )

    return SynthesisResult(
        symbol=symbol,
        timeframe=timeframe,
        horizon_label=horizon_label,
        expiry_time=pred_expiry_time,
        research_stance=stance,
        market_regime=structure.regime,
        forecasted_direction=forecast_dir,
        expected_return_pct=expected_return_pct,
        expected_price_target=round(pred_final_price, 2),
        expected_range_low=confidence.empirical_range_95_low,
        expected_range_high=confidence.empirical_range_95_high,
        var_95_pct=confidence.var_95_pct,
        calibrated_prob=confidence.directional_probability,
        sample_count=confidence.sample_count,
        confidence_interval_str=ci_str,
        detected_patterns=pattern_names,
        supporting_factors=supporting,
        conflicting_factors=conflicting,
        invalidation_conditions=invalidation,
        data_quality_status=data_quality,
        explanation_narrative=narrative,
    )
