# APEX Terminal User Guide & Local Startup Instructions

## 1. Prerequisites

- **Machine**: Mac with Apple Silicon (M1/M2/M3/M4/M5)
- **Memory**: 16 GB unified RAM recommended
- **OS**: macOS 13+
- **Python**: 3.10 to 3.12 (Python 3.11 recommended)
- **Node.js**: v18+

## 2. Fast One-Command Startup

From the project root (`/Users/karhiksingh/APEX`):

```bash
# 1. Activate Python virtual environment
source .venv/bin/activate

# 2. Launch APEX unified terminal server (serves API, WebSocket, and compiled UI)
PYTHONPATH=. uvicorn backend.api.app:app --host 127.0.0.1 --port 8000
```

Open your browser to:
**`http://localhost:8000`**

The terminal will automatically:
1. Verify Apple Silicon MPS acceleration.
2. Ingest genuine historical Binance spot candles for BTC/USDT, ETH/USDT, and SOL/USDT.
3. Establish live streaming market streams via WebSocket.
4. Render the high-density trading workspace.

---

## 3. Alternative: Development Mode (Hot Reloading)

If modifying frontend React components with instant hot reload:

Terminal 1 (Backend API):
```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2 (Vite Frontend):
```bash
cd frontend
npm run dev
```

Open **`http://localhost:5173`**.

---

## 4. Key Navigation & Capabilities

- **Overview Screen (`/`)**: Main interactive candlestick chart with volume bars, EMA 20/50/200, support/resistance bands, Kronos forecast projection cone, and right quantitative thesis panel.
- **Markets Screen**: Watchlist of spot pairs with live prices, 24h delta, trend alignment, and 1-click pair switcher.
- **Forecast Lab**: Compare `Kronos-mini` (4.1M) vs `Kronos-base` (102.5M) across 1d, 3d, and 5d horizons with sampling controls and detailed candle breakdown.
- **Pattern Scanner**: Searchable and filterable table of confirmed candlestick formations (engulfing, hammer, morning star, outside bars) and chart patterns (double tops/bottoms, triangles, flags).
- **Backtesting**: Leakage-free walk-forward rolling origin historical backtester comparing Kronos against No-change Martingale, Drift, and Moving Average baselines.
- **Paper Research Journal**: Simulated position tracker enforcing 5 bps fees and 5 bps slippage, tracking gross and net PnL.
- **Model Health**: Monitor Apple Silicon MPS GPU memory, resident RAM, checkpoint revisions, and inference latency.
- **Data Health**: Audit feed status, latency, missing candle gaps, and last closed candle timestamp.
- **Settings**: System configurations, model registry pins, and quantitative disclaimers.

---

## 5. Running the Automated Test Suite

To execute the unit and integration tests:

```bash
source .venv/bin/activate
PYTHONPATH=. pytest backend/tests/ -v
```

