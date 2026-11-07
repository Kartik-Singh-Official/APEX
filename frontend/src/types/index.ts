export interface Candle {
  symbol: string;
  timeframe: string;
  open_time: number;
  close_time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  amount: number;
  trades_count?: number;
  is_closed: boolean;
  provider: string;
  received_at: number;
  quality_status: 'VALID' | 'PROVISIONAL' | 'GAP_FILLED' | 'ANOMALY';
}

export interface PredictedCandle {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ForecastResult {
  id: string;
  symbol: string;
  timeframe: string;
  horizon_label: string;
  current_price: number;
  median_target_price: number;
  expected_return_pct: number;
  range_95_low: number;
  range_95_high: number;
  range_80_low: number;
  range_80_high: number;
  var_95_pct: number;
  calibrated_prob: number | null;
  is_confidence_available: boolean;
  confidence_message: string;
  confidence_interval: [number, number] | null;
  predicted_candles: PredictedCandle[];
  model_metadata: {
    model_name: string;
    model_id: string;
    model_revision: string;
    device: string;
    latency_ms: number;
    memory_resident_mb: number;
    memory_mps_mb: number;
    sample_count: number;
  };
}

export interface IndicatorLatest {
  open_time: number;
  close: number;
  ema_20?: number;
  ema_50?: number;
  ema_200?: number;
  rsi_14?: number;
  macd?: number;
  macd_signal?: number;
  macd_hist?: number;
  atr_14?: number;
  adx_14?: number;
  plus_di?: number;
  minus_di?: number;
  bb_middle?: number;
  bb_upper?: number;
  bb_lower?: number;
  bb_bandwidth?: number;
  rvol?: number;
  obv?: number;
}

export interface IndicatorSeriesItem {
  open_time: number;
  ema_20: number | null;
  ema_50: number | null;
  ema_200: number | null;
  bb_upper: number | null;
  bb_middle: number | null;
  bb_lower: number | null;
  rsi_14: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_hist: number | null;
  atr_14: number | null;
  rvol: number | null;
}

export interface SwingPivot {
  index: number;
  open_time: number;
  confirmation_time: number;
  type: 'HIGH' | 'LOW';
  price: number;
  classification?: string;
}

export interface SRZone {
  level: number;
  zone_low: number;
  zone_high: number;
  type: 'SUPPORT' | 'RESISTANCE';
  touch_count: number;
  strength: number;
}

export interface MarketStructure {
  regime: string;
  trend: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  swing_pivots: SwingPivot[];
  support_resistance: SRZone[];
  volatility_state: string;
  atr_percentile: number;
  range_high: number;
  range_low: number;
}

export interface DetectedPattern {
  id: string;
  pattern_name: string;
  pattern_category: 'CANDLESTICK' | 'CHART_FORMATION';
  stance: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  timeframe: string;
  formation_start: number;
  confirmation_time: number;
  price_levels: Record<string, number>;
  detection_conditions: Record<string, any>;
  quality_score: number;
  is_confirmed: boolean;
}

export interface AnalysisThesis {
  symbol: string;
  timeframe: string;
  horizon_label: string;
  expiry_time: number;
  research_stance: string;
  market_regime: string;
  forecasted_direction: string;
  expected_return_pct: number;
  expected_price_target: number;
  expected_range_low: number;
  expected_range_high: number;
  var_95_pct: number;
  calibrated_prob: number | null;
  sample_count: number;
  confidence_interval_str: string;
  detected_patterns: string[];
  supporting_factors: string[];
  conflicting_factors: string[];
  invalidation_conditions: string;
  data_quality_status: string;
  explanation_narrative: string;
}

export interface DataHealth {
  provider: string;
  status: 'ONLINE' | 'DEGRADED' | 'OFFLINE';
  connected: boolean;
  ws_connected?: boolean;
  last_update_ms: number;
  freshness_ms: number;
  last_closed_candle_time: number | null;
  missing_candles_count: number;
  stored_candles_count: number;
  last_error: string | null;
  active_symbols: string[];
  active_timeframes: string[];
}

export interface ModelHealth {
  active_model: string | null;
  device: string;
  is_mps_available: boolean;
  is_mps_built: boolean;
  last_load_time_s: number;
  last_latency_ms: number;
  inference_count: number;
  last_forecast_timestamp: number | null;
  memory_resident_mb: number;
  memory_mps_mb: number;
  available_models: string[];
}

export interface BacktestSummary {
  model_name: string;
  horizon_label: string;
  evaluated_samples: number;
  mae: number;
  rmse: number;
  directional_accuracy: number;
  balanced_accuracy: number;
  brier_score: number;
  coverage_80: number;
  coverage_95: number;
  baseline_no_change_mae: number;
  baseline_drift_mae: number;
  baseline_sma_mae: number;
  outperforms_no_change: boolean;
  evaluation_time_s: number;
}

export interface PaperRecord {
  id: string;
  forecast_id?: string;
  symbol: string;
  timeframe: string;
  stance: string;
  entry_time: number;
  entry_price: number;
  target_price: number;
  stop_loss: number;
  horizon_hours: number;
  expiry_time: number;
  exit_time?: number;
  exit_price?: number;
  fee_pct: number;
  slippage_pct: number;
  gross_pnl_pct?: number;
  net_pnl_pct?: number;
  status: 'OPEN' | 'WIN' | 'LOSS' | 'EXPIRED';
  notes?: string;
  created_at: number;
}
