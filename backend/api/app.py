"""FastAPI Application for APEX Quantitative Market Intelligence Terminal."""
import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core.config import settings, detect_optimal_device
from backend.database.db import init_db, get_sync_db
from backend.data.models import CandleData, DataHealthInfo
from backend.data.repository import CandleRepository
from backend.data.binance_rest import BinanceRestClient
from backend.data.binance_ws import BinanceWsClient
from backend.kronos.manager import model_manager
from backend.indicators.technical import compute_indicators
from backend.market_structure.structure import analyze_market_structure
from backend.patterns.detector import detect_all_patterns
from backend.calibration.calibrator import calibrate_forecast, CalibratedConfidence
from backend.forecasting.intelligence import synthesize_market_intelligence, SynthesisResult
from backend.backtesting.engine import BacktestWalkForwardEngine
from backend.paper_journal.journal import paper_journal_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("apex.api")

repository = CandleRepository()
rest_client = BinanceRestClient()
ws_client = BinanceWsClient(repository)

# Connected frontend websocket clients
frontend_ws_clients: List[WebSocket] = []


def broadcast_to_frontend(candle: CandleData):
    """Callback for Binance WS to broadcast updates to connected frontend clients."""
    payload = {
        "type": "candle_tick",
        "data": candle.model_dump(),
    }
    # Settle any open paper positions on new closed price
    if candle.is_closed:
        paper_journal_manager.update_settlements(candle.close, candle.symbol)

    dead_clients = []
    for client in frontend_ws_clients:
        try:
            asyncio.create_task(client.send_text(json.dumps(payload)))
        except Exception:
            dead_clients.append(client)
    for dc in dead_clients:
        if dc in frontend_ws_clients:
            frontend_ws_clients.remove(dc)


ws_client.add_subscriber(broadcast_to_frontend)


async def initial_data_backfill():
    """Initial historical backfill on startup for supported symbols and intervals."""
    logger.info("Starting initial historical backfill from Binance public REST...")
    for sym in settings.supported_symbols:
        for tf in ["4h", "1d"]:
            try:
                existing = repository.get_candles(sym, tf, limit=10)
                if len(existing) < 100:
                    logger.info(f"Backfilling {sym} {tf} (target 250 candles)...")
                    candles, gaps = rest_client.backfill(sym, tf, target_count=250)
                    repository.save_candles(candles)
                    logger.info(f"Backfilled {len(candles)} candles for {sym} {tf} (detected {gaps} gaps).")
            except Exception as e:
                logger.error(f"Backfill failed for {sym} {tf}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing APEX Terminal Backend...")
    init_db()
    # Trigger initial data backfill in background
    asyncio.create_task(initial_data_backfill())
    # Start WebSocket live market stream
    await ws_client.start()
    yield
    # Shutdown
    logger.info("Shutting down APEX Terminal Backend...")
    await ws_client.stop()
    model_manager.unload_current_model()


app = FastAPI(
    title="APEX Market Intelligence API",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS setup for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def get_system_health():
    """System health and hardware detection."""
    return {
        "status": "ONLINE",
        "version": settings.app_version,
        "device": model_manager.device,
        "is_mps_verified": model_manager.device == "mps",
        "timestamp": int(time.time() * 1000),
    }


@app.get("/api/symbols")
def get_symbols():
    """Supported trading pairs and intervals."""
    return {
        "symbols": settings.supported_symbols,
        "default_symbol": settings.default_symbol,
        "timeframes": settings.supported_timeframes,
        "default_timeframe": settings.default_timeframe,
        "horizons": settings.horizons_map,
    }


@app.get("/api/candles")
def get_candles(
    symbol: str = Query("BTCUSDT"),
    timeframe: str = Query("4h"),
    limit: int = Query(250, ge=10, le=1000),
    only_closed: bool = Query(False)
):
    """Fetch stored historical candles."""
    candles = repository.get_candles(symbol, timeframe, limit=limit, only_closed=only_closed)
    # If DB is empty, fetch immediately via REST client
    if not candles:
        try:
            fetched, _ = rest_client.backfill(symbol, timeframe, target_count=limit)
            repository.save_candles(fetched)
            candles = repository.get_candles(symbol, timeframe, limit=limit, only_closed=only_closed)
        except Exception as e:
            logger.error(f"On-demand fetch failed: {e}")

    return {
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "count": len(candles),
        "candles": [c.model_dump() for c in candles],
    }


@app.get("/api/data/health")
def get_data_health(symbol: str = Query("BTCUSDT"), timeframe: str = Query("4h")):
    """Data health screen metrics."""
    health = repository.get_data_health(symbol, timeframe)
    health_dict = health.model_dump()
    health_dict["ws_connected"] = ws_client.connected
    return health_dict


@app.get("/api/indicators")
def get_indicators(symbol: str = Query("BTCUSDT"), timeframe: str = Query("4h"), limit: int = Query(200)):
    """Compute and return full indicator suite."""
    df = repository.get_candles_df(symbol, timeframe, limit=limit, only_closed=False)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"No data available for {symbol} {timeframe}")

    df_ind = compute_indicators(df)
    # Convert latest indicators to dictionary
    latest = df_ind.iloc[-1].to_dict()
    # Format NaN to None for JSON compliance
    clean_latest = {k: (None if isinstance(v, float) and (np.isnan(v) or np.isinf(v)) else v) for k, v in latest.items()}

    # Also return series for charting
    series_data = []
    for idx, row in df_ind.iterrows():
        series_data.append({
            "open_time": int(row["open_time"]),
            "ema_20": None if pd.isna(row.get("ema_20")) else round(float(row["ema_20"]), 2),
            "ema_50": None if pd.isna(row.get("ema_50")) else round(float(row["ema_50"]), 2),
            "ema_200": None if pd.isna(row.get("ema_200")) else round(float(row["ema_200"]), 2),
            "bb_upper": None if pd.isna(row.get("bb_upper")) else round(float(row["bb_upper"]), 2),
            "bb_middle": None if pd.isna(row.get("bb_middle")) else round(float(row["bb_middle"]), 2),
            "bb_lower": None if pd.isna(row.get("bb_lower")) else round(float(row["bb_lower"]), 2),
            "rsi_14": None if pd.isna(row.get("rsi_14")) else round(float(row["rsi_14"]), 2),
            "macd": None if pd.isna(row.get("macd")) else round(float(row["macd"]), 2),
            "macd_signal": None if pd.isna(row.get("macd_signal")) else round(float(row["macd_signal"]), 2),
            "macd_hist": None if pd.isna(row.get("macd_hist")) else round(float(row["macd_hist"]), 2),
            "atr_14": None if pd.isna(row.get("atr_14")) else round(float(row["atr_14"]), 2),
            "rvol": None if pd.isna(row.get("rvol")) else round(float(row["rvol"]), 2),
        })

    return {
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "latest": clean_latest,
        "series": series_data[-100:],
    }


@app.get("/api/market-structure")
def get_market_structure(symbol: str = Query("BTCUSDT"), timeframe: str = Query("4h")):
    """Market structure analysis, BOS, CHoCH, and SR zones."""
    df = repository.get_candles_df(symbol, timeframe, limit=150, only_closed=False)
    if df.empty:
        raise HTTPException(status_code=404, detail="No data available")
    df_ind = compute_indicators(df)
    analysis = analyze_market_structure(df_ind)
    return analysis.model_dump()


@app.get("/api/patterns")
def get_patterns(symbol: str = Query("BTCUSDT"), timeframe: str = Query("4h")):
    """Detected chart formations and candlestick patterns."""
    df = repository.get_candles_df(symbol, timeframe, limit=150, only_closed=False)
    if df.empty:
        return {"patterns": []}
    patterns = detect_all_patterns(df, timeframe)
    return {"patterns": [p.model_dump() for p in patterns]}


class ForecastRequest(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "4h"
    horizon_label: str = "3d"  # '1d', '3d', '5d'
    model_key: str = "NeoQuasar/Kronos-mini"
    sample_count: int = 5


@app.post("/api/forecast/generate")
def generate_forecast(req: ForecastRequest):
    """Execute Kronos forecast locally on MPS/CPU and compute calibrated confidence."""
    df = repository.get_candles_df(req.symbol, req.timeframe, limit=200, only_closed=True)
    if len(df) < 30:
        # Attempt backfill
        candles, _ = rest_client.backfill(req.symbol, req.timeframe, target_count=150)
        repository.save_candles(candles)
        df = repository.get_candles_df(req.symbol, req.timeframe, limit=200, only_closed=True)

    if len(df) < 30:
        raise HTTPException(status_code=400, detail=f"Insufficient candles for forecast (found {len(df)})")

    pred_len = settings.horizons_map.get(req.timeframe, {}).get(req.horizon_label, 18)
    
    # Run Kronos Predictor
    pred_df, meta = model_manager.generate_forecast(
        df=df,
        pred_len=pred_len,
        sample_count=req.sample_count,
        model_key=req.model_key,
        freq=req.timeframe,
    )

    current_price = float(df["close"].iloc[-1])
    median_pred_price = float(pred_df["close"].iloc[-1])
    pred_return = (median_pred_price - current_price) / current_price

    # Formatted future candles
    predicted_candles = []
    for idx, row in pred_df.iterrows():
        predicted_candles.append({
            "timestamp": int(idx.timestamp() * 1000),
            "open": round(float(row["open"]), 2),
            "high": round(float(row["high"]), 2),
            "low": round(float(row["low"]), 2),
            "close": round(float(row["close"]), 2),
            "volume": round(float(row["volume"]), 2),
        })

    # Calibrate confidence using historical evaluations
    # In walk-forward or initial phase, generate empirical out-of-sample residuals
    conn = get_sync_db()
    val_records = []
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT median_pred_price, realized_price, start_price
            FROM forecasts
            WHERE symbol = ? AND timeframe = ? AND status = 'EVALUATED'
            """,
            (req.symbol.upper(), req.timeframe),
        )
        for r in cursor.fetchall():
            p_ret = (r["median_pred_price"] - r["start_price"]) / r["start_price"]
            r_ret = (r["realized_price"] - r["start_price"]) / r["start_price"]
            val_records.append({
                "pred_return": p_ret,
                "realized_return": r_ret,
                "residual": r_ret - p_ret,
            })
    finally:
        conn.close()

    calibrated = calibrate_forecast(median_pred_price, current_price, val_records, min_samples=15)

    # Persist forecast to DB
    forecast_id = str(int(time.time() * 1000))
    expiry_time = predicted_candles[-1]["timestamp"]
    conn = get_sync_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO forecasts (
                id, symbol, timeframe, horizon_label, horizon_candles, model_id,
                model_revision, inference_device, generated_at, expiry_at, start_price,
                median_pred_price, median_pred_return, range_low, range_high, var_95,
                sample_count, calibrated_prob, confidence_interval_low, confidence_interval_high,
                validation_sample_count, predicted_candles_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                forecast_id,
                req.symbol.upper(),
                req.timeframe,
                req.horizon_label,
                pred_len,
                meta["model_id"],
                meta["model_revision"],
                meta["device"],
                meta["generated_at"],
                expiry_time,
                current_price,
                median_pred_price,
                round(pred_return * 100.0, 2),
                calibrated.empirical_range_95_low,
                calibrated.empirical_range_95_high,
                calibrated.var_95_pct,
                req.sample_count,
                calibrated.directional_probability,
                calibrated.confidence_interval_low,
                calibrated.confidence_interval_high,
                calibrated.sample_count,
                json.dumps(predicted_candles),
                "PENDING",
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "id": forecast_id,
        "symbol": req.symbol.upper(),
        "timeframe": req.timeframe,
        "horizon_label": req.horizon_label,
        "current_price": current_price,
        "median_target_price": round(median_pred_price, 2),
        "expected_return_pct": round(pred_return * 100.0, 2),
        "range_95_low": calibrated.empirical_range_95_low,
        "range_95_high": calibrated.empirical_range_95_high,
        "range_80_low": calibrated.empirical_range_80_low,
        "range_80_high": calibrated.empirical_range_80_high,
        "var_95_pct": calibrated.var_95_pct,
        "calibrated_prob": calibrated.directional_probability,
        "is_confidence_available": calibrated.is_available,
        "confidence_message": calibrated.diagnostic_message,
        "confidence_interval": [calibrated.confidence_interval_low, calibrated.confidence_interval_high] if calibrated.is_available else None,
        "predicted_candles": predicted_candles,
        "model_metadata": meta,
    }


@app.get("/api/analysis")
def get_analysis_thesis(
    symbol: str = Query("BTCUSDT"),
    timeframe: str = Query("4h"),
    horizon_label: str = Query("3d")
):
    """Full structured intelligence thesis breakdown."""
    df = repository.get_candles_df(symbol, timeframe, limit=150, only_closed=False)
    if df.empty:
        raise HTTPException(status_code=404, detail="No data available")

    df_ind = compute_indicators(df)
    structure = analyze_market_structure(df_ind)
    patterns = detect_all_patterns(df, timeframe)
    latest_ind = df_ind.iloc[-1].to_dict()

    current_price = float(df["close"].iloc[-1])

    # Fetch latest forecast or default to no forecast
    conn = get_sync_db()
    latest_fc = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM forecasts
            WHERE symbol = ? AND timeframe = ? AND horizon_label = ?
            ORDER BY generated_at DESC LIMIT 1
            """,
            (symbol.upper(), timeframe, horizon_label),
        )
        latest_fc = cursor.fetchone()
    finally:
        conn.close()

    if latest_fc:
        pred_final = latest_fc["median_pred_price"]
        expiry_t = latest_fc["expiry_at"]
        calibrated = CalibratedConfidence(
            is_available=bool(latest_fc["calibrated_prob"] is not None),
            directional_probability=latest_fc["calibrated_prob"],
            sample_count=latest_fc["validation_sample_count"] or 0,
            confidence_interval_low=latest_fc["confidence_interval_low"],
            confidence_interval_high=latest_fc["confidence_interval_high"],
            empirical_range_95_low=latest_fc["range_low"],
            empirical_range_95_high=latest_fc["range_high"],
            var_95_pct=latest_fc["var_95"],
            diagnostic_message="Validated via chronological evaluation" if latest_fc["calibrated_prob"] else "Insufficient validation data — confidence unavailable."
        )
    else:
        pred_final = current_price
        expiry_t = int(time.time() * 1000) + (72 * 3600 * 1000)
        calibrated = CalibratedConfidence(
            is_available=False,
            directional_probability=None,
            sample_count=0,
            empirical_range_95_low=round(current_price * 0.95, 2),
            empirical_range_95_high=round(current_price * 1.05, 2),
            var_95_pct=-3.5,
            diagnostic_message="Insufficient validation data — confidence unavailable."
        )

    thesis = synthesize_market_intelligence(
        symbol=symbol.upper(),
        timeframe=timeframe,
        horizon_label=horizon_label,
        current_price=current_price,
        pred_final_price=pred_final,
        pred_expiry_time=expiry_t,
        structure=structure,
        patterns=patterns,
        indicators=latest_ind,
        confidence=calibrated,
        data_quality="VALID"
    )
    return thesis.model_dump()


@app.get("/api/models/health")
def get_model_health():
    """Model health monitor diagnostics."""
    return model_manager.get_health()


class SwitchModelRequest(BaseModel):
    model_key: str  # 'NeoQuasar/Kronos-mini' or 'NeoQuasar/Kronos-base'


@app.post("/api/models/switch")
def switch_model(req: SwitchModelRequest):
    """Switch active Kronos model in memory."""
    try:
        model_manager.load_model(req.model_key)
        return {"status": "SUCCESS", "active_model": model_manager.active_model_name, "device": model_manager.device}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to switch model: {e}")


class BacktestRunRequest(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "4h"
    horizon_label: str = "3d"
    model_key: str = "NeoQuasar/Kronos-mini"
    max_origins: int = 15


@app.post("/api/backtest/run")
def run_backtest(req: BacktestRunRequest):
    """Execute walk-forward backtest and compare Kronos against simple baselines."""
    df = repository.get_candles_df(req.symbol, req.timeframe, limit=350, only_closed=True)
    if len(df) < 100:
        # Attempt backfill
        candles, _ = rest_client.backfill(req.symbol, req.timeframe, target_count=350)
        repository.save_candles(candles)
        df = repository.get_candles_df(req.symbol, req.timeframe, limit=350, only_closed=True)

    if len(df) < 100:
        raise HTTPException(status_code=400, detail=f"Need at least 100 historical candles for backtesting (found {len(df)})")

    engine = BacktestWalkForwardEngine(df, timeframe=req.timeframe)
    summary = engine.run_walk_forward(
        horizon_label=req.horizon_label,
        model_key=req.model_key,
        min_history_bars=80,
        step_bars=12,
        max_origins=req.max_origins
    )
    return summary.model_dump()


@app.get("/api/paper-journal")
def get_paper_journal():
    """List paper research records."""
    records = paper_journal_manager.list_records(limit=50)
    return {"records": [r.model_dump() for r in records]}


class CreatePaperSignalRequest(BaseModel):
    symbol: str
    timeframe: str
    stance: str
    entry_price: float
    target_price: float
    stop_loss: float
    horizon_hours: int = 72
    forecast_id: Optional[str] = None
    notes: Optional[str] = None


@app.post("/api/paper-journal/create")
def create_paper_signal(req: CreatePaperSignalRequest):
    """Log a hypothetical paper research position."""
    rec = paper_journal_manager.record_signal(
        symbol=req.symbol,
        timeframe=req.timeframe,
        stance=req.stance,
        entry_price=req.entry_price,
        target_price=req.target_price,
        stop_loss=req.stop_loss,
        horizon_hours=req.horizon_hours,
        forecast_id=req.forecast_id,
        notes=req.notes,
    )
    return rec.model_dump()


@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket stream to feed live candle updates directly to the frontend."""
    await websocket.accept()
    frontend_ws_clients.append(websocket)
    try:
        while True:
            # Keepalive receiver
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if websocket in frontend_ws_clients:
            frontend_ws_clients.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket client error: {e}")
        if websocket in frontend_ws_clients:
            frontend_ws_clients.remove(websocket)


# Mount Static Frontend Production Distribution
from pathlib import Path
from fastapi.staticfiles import StaticFiles

frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

