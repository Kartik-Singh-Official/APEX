"""Database Schema for APEX Market Intelligence & Quantitative Forecasting.
Stores historical candles with strict data provenance, generated forecasts,
detected patterns, market structure pivots, paper journal records, and validation metrics.
"""

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS candles (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    open_time INTEGER NOT NULL,
    close_time INTEGER NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,
    amount REAL NOT NULL,
    trades_count INTEGER DEFAULT 0,
    is_closed INTEGER NOT NULL DEFAULT 1,
    provider TEXT NOT NULL DEFAULT 'binance_spot',
    received_at INTEGER NOT NULL,
    quality_status TEXT NOT NULL DEFAULT 'VALID',
    PRIMARY KEY (symbol, timeframe, open_time)
);

CREATE INDEX IF NOT EXISTS idx_candles_lookup 
ON candles (symbol, timeframe, open_time DESC);

CREATE TABLE IF NOT EXISTS forecasts (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    horizon_label TEXT NOT NULL,
    horizon_candles INTEGER NOT NULL,
    model_id TEXT NOT NULL,
    model_revision TEXT NOT NULL,
    inference_device TEXT NOT NULL,
    generated_at INTEGER NOT NULL,
    expiry_at INTEGER NOT NULL,
    start_price REAL NOT NULL,
    median_pred_price REAL NOT NULL,
    median_pred_return REAL NOT NULL,
    range_low REAL NOT NULL,
    range_high REAL NOT NULL,
    var_95 REAL NOT NULL,
    sample_count INTEGER NOT NULL,
    calibrated_prob REAL,
    confidence_interval_low REAL,
    confidence_interval_high REAL,
    validation_sample_count INTEGER,
    predicted_candles_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    realized_price REAL,
    realized_return REAL,
    brier_score REAL,
    directional_hit INTEGER
);

CREATE INDEX IF NOT EXISTS idx_forecasts_lookup 
ON forecasts (symbol, timeframe, generated_at DESC);

CREATE TABLE IF NOT EXISTS detected_patterns (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    pattern_name TEXT NOT NULL,
    pattern_category TEXT NOT NULL, -- 'CANDLESTICK' or 'CHART_FORMATION'
    stance TEXT NOT NULL,           -- 'BULLISH', 'BEARISH', 'NEUTRAL'
    formation_start INTEGER NOT NULL,
    confirmation_time INTEGER NOT NULL,
    price_levels_json TEXT NOT NULL,
    quality_score REAL NOT NULL,
    is_confirmed INTEGER NOT NULL DEFAULT 1,
    detection_conditions_json TEXT NOT NULL,
    created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_patterns_lookup 
ON detected_patterns (symbol, timeframe, confirmation_time DESC);

CREATE TABLE IF NOT EXISTS paper_journal (
    id TEXT PRIMARY KEY,
    forecast_id TEXT,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    stance TEXT NOT NULL,
    entry_time INTEGER NOT NULL,
    entry_price REAL NOT NULL,
    target_price REAL NOT NULL,
    stop_loss REAL NOT NULL,
    horizon_hours INTEGER NOT NULL,
    expiry_time INTEGER NOT NULL,
    exit_time INTEGER,
    exit_price REAL,
    fee_pct REAL NOT NULL DEFAULT 0.05,
    slippage_pct REAL NOT NULL DEFAULT 0.05,
    gross_pnl_pct REAL,
    net_pnl_pct REAL,
    status TEXT NOT NULL DEFAULT 'OPEN', -- 'OPEN', 'WIN', 'LOSS', 'EXPIRED'
    notes TEXT,
    created_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_paper_journal_lookup 
ON paper_journal (symbol, entry_time DESC);

CREATE TABLE IF NOT EXISTS model_evaluations (
    id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    horizon_label TEXT NOT NULL,
    mae REAL NOT NULL,
    rmse REAL NOT NULL,
    directional_accuracy REAL NOT NULL,
    balanced_accuracy REAL NOT NULL,
    brier_score REAL NOT NULL,
    coverage_80 REAL NOT NULL,
    coverage_95 REAL NOT NULL,
    baseline_no_change_mae REAL NOT NULL,
    baseline_drift_mae REAL NOT NULL,
    evaluated_samples INTEGER NOT NULL,
    eval_period_start INTEGER NOT NULL,
    eval_period_end INTEGER NOT NULL,
    evaluated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS data_health_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    last_candle_time INTEGER,
    data_freshness_ms INTEGER,
    missing_candles_count INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    message TEXT,
    timestamp INTEGER NOT NULL
);
"""
