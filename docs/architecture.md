# APEX Architecture & System Design Specification

## 1. System Overview

APEX is a local AI-powered cryptocurrency market intelligence and forecasting terminal designed for quantitative research on Apple Silicon hardware (macOS / M-series unified memory). It pairs institutional-grade technical analysis and market structure algorithms with local autoregressive neural forecasting via Kronos.

```
+-----------------------------------------------------------------------------------+
|                               APEX DESKTOP TERMINAL                               |
|                                                                                   |
|  +--------------------+  +---------------------------------+  +----------------+  |
|  |    SIDEBAR NAV     |  |      MAIN WORKSPACE (CANVAS)    |  | QUANT ANALYSIS |  |
|  | - Overview         |  | - Candlestick Chart (Lightweight|  | - Stance Badge |  |
|  | - Markets          |  | - Volume Histogram              |  | - Directional P|  |
|  | - Forecast Lab     |  | - EMA 20/50/200 Overlays        |  | - Target & VaR |  |
|  | - Pattern Scanner  |  | - Support / Resistance Bands    |  | - CI Strip     |  |
|  | - Backtesting      |  | - Projected Forecast Horizon    |  | - Patterns     |  |
|  | - Paper Journal    |  | - 80% / 95% Uncertainty Cones   |  | - Thesis Driver|  |
|  | - Model Health     |  +---------------------------------+  | - Invalidation |  |
|  | - Data Health      |  |   MULTI-TIMEFRAME REGIME MATRIX |  | - Log Paper Pos|  |
|  | - Settings         |  |   & WALK-FORWARD RESEARCH LEDGER|  +----------------+  |
|  +--------------------+  +---------------------------------+                      |
+-----------------------------------------------------------------------------------+
                                    | REST / WebSocket
                                    v
+-----------------------------------------------------------------------------------+
|                            FASTAPI LOCAL BACKEND (8000)                           |
|                                                                                   |
|  +-------------------+  +--------------------+  +-------------------------------+ |
|  |   DATA ENGINE     |  | QUANT COMPUTATION  |  |    KRONOS INFERENCE ENGINE    | |
|  | - Binance REST    |  | - Indicators (TA)  |  | - Kronos-mini / Kronos-base   | |
|  | - WebSocket Stream|  | - Market Structure |  | - KronosTokenizer (BSQ)       | |
|  | - Gap Detection   |  | - Pattern Scanner  |  | - KronosPredictor             | |
|  | - Candle Finalizer|  | - Thesis Synthesizer| | - Apple Silicon MPS Metal     | |
|  | - SQLite DB Layer |  | - Walk-Forward BT  |  | - Lazy Loading / Unloading    | |
|  +-------------------+  +--------------------+  +-------------------------------+ |
+-----------------------------------------------------------------------------------+
```

## 2. Directory Structure & Separation of Concerns

```
APEX/
├── backend/
│   ├── api/                 # FastAPI routes, schemas, CORS, WebSocket stream
│   ├── core/                # Configuration, hardware detection, settings
│   ├── data/                # Ingestion: Binance REST, WebSocket, Repository, Models
│   ├── database/            # SQLite schema migrations, connection pooling
│   ├── kronos/              # Upstream Kronos model, tokenizer, and lazy manager
│   ├── indicators/          # Pure vector technical indicators (EMA, RSI, MACD, BB)
│   ├── market_structure/    # Swing pivots, HH/HL/LH/LL, BOS, CHoCH, S/R zones
│   ├── patterns/            # Candlestick and geometric chart formation scanners
│   ├── forecasting/         # Forecast synthesis and probabilistic thesis generator
│   ├── calibration/         # Wilson score CI, Brier score, empirical residual bands
│   ├── backtesting/         # Walk-forward rolling origin validator with baselines
│   ├── paper_journal/       # Read-only position ledger with fee/slippage tracking
│   ├── monitoring/          # Model health, data freshness, latency profiling
│   └── tests/               # Pytest suite verifying correctness & leakage prevention
├── frontend/
│   ├── src/
│   │   ├── charts/          # Lightweight Charts canvas with forecast overlay
│   │   ├── components/      # HeaderToolbar, SidebarNav, RightAnalysisPanel, etc.
│   │   ├── pages/           # 9 Dedicated screens
│   │   ├── services/        # Typed API client and WebSocket streaming manager
│   │   └── types/           # Full TypeScript data contract interfaces
├── docs/                    # Quantitative and operational documentation
├── models_cache/            # Local directory storing downloaded HF safetensors
└── data/                    # SQLite database storage (apex.db)
```

## 3. Communication Protocols

1. **HTTP/REST (localhost:8000)**:
   - Synchronous data retrieval for historical candles, indicator series, market structure, pattern tables, backtest summaries, and paper journal operations.
2. **WebSocket (ws://localhost:8000/ws/stream)**:
   - Full-duplex persistent stream receiving live candle ticks (`k.x == false`) and closed candle notifications (`k.x == true`) from Binance spot streams, broadcasting in real time to connected UI terminals.
