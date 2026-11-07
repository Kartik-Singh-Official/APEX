# APEX — Local AI-Powered Cryptocurrency Market Intelligence & Forecasting Platform

[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![PyTorch MPS](https://img.shields.io/badge/PyTorch-MPS%20Accelerated-green.svg)](https://pytorch.org/)
[![Kronos Model](https://img.shields.io/badge/Kronos-mini%20%7C%20base-cyan.svg)](https://github.com/shiyu-coder/Kronos)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

APEX is a serious, local, quantitative cryptocurrency market intelligence and forecasting terminal engineered specifically for Apple Silicon hardware (macOS / M-series unified memory).

It combines:
- **Official Kronos Neural Forecasting** (`NeoQuasar/Kronos-mini` & `NeoQuasar/Kronos-base`) running locally via Apple Silicon Metal Performance Shaders (MPS).
- **Genuine Spot Market Engine**: Real-time REST and WebSocket streaming connectors for public Binance cryptocurrency spot data (BTC/USDT, ETH/USDT, SOL/USDT) with automated candle finalization and zero synthetic filler data.
- **Independent Quantitative Technical Analysis**: EMA 20/50/200, RSI 14, MACD (12,26,9), ATR 14, ADX 14, Bollinger Bands, Volume MA, RVOL, and OBV.
- **Market Structure & Pivot Engine**: Algorithmically confirmed swing highs/lows without lookahead bias, Higher Highs/Lows, Break of Structure (BOS), Change of Character (CHoCH), and dynamic Support/Resistance clusters.
- **Pattern Scanner**: Documented detectors for candlestick formations (Engulfing, Hammer, Shooting Star, Doji, Morning/Evening Star, Inside/Outside Bars) and structural chart formations (Double Top/Bottom, Triangles, Wedges, Flags).
- **Calibrated Uncertainty**: Wilson score confidence intervals and empirical quantiles derived from chronologically separated out-of-sample walk-forward validation residuals (zero invented percentages).
- **Walk-Forward Historical Backtesting**: Rolling-origin chronological evaluation comparing Kronos against No-change Martingale, Drift, and Moving Average baselines.
- **Paper Research Journal**: Read-only simulation ledger with strictly accounted fee (0.05%) and slippage (0.05%) deductions.
- **Professional Institutional Terminal UX**: Designed via Google Stitch MCP with near-black `#0B0F14` aesthetic, crisp hairline boundaries, tabular JetBrains Mono numerals, and Lightweight Charts candlestick charting.

---

## Hardware & Local Runtime

- **Target System**: Apple Silicon Mac (M1/M2/M3/M4/M5), 16 GB unified memory.
- **Inference Runtime**: PyTorch 2.15.0 on `mps:0` (Apple Silicon GPU Metal Performance Shaders) with automatic CPU fallback.
- **Privacy & Local Autonomy**: 100% local model weights and inference. Zero historical candles or forecast prompts are dispatched to third-party AI cloud services.
- **Safety**: Pure paper research. No brokerage APIs, no real-money transactions, no wallet connections.

---

## Quickstart

### 1. Unified Production Run (Single Command)

```bash
# Activate environment
source .venv/bin/activate

# Launch APEX Terminal
PYTHONPATH=. uvicorn backend.api.app:app --host 127.0.0.1 --port 8000
```
Navigate to: **`http://localhost:8000`**

### 2. Development Mode (Hot Reloading)

Backend:
```bash
source .venv/bin/activate
PYTHONPATH=. uvicorn backend.api.app:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:
```bash
cd frontend
npm run dev
```
Navigate to: **`http://localhost:5173`**

### 3. Run Automated Tests

```bash
source .venv/bin/activate
PYTHONPATH=. pytest backend/tests/ -v
```

---

## Upstream Model Registry & Pins

| Model | Checkpoint SHA | Tokenizer ID & Revision | Parameters | Memory Footprint |
|---|---|---|---|---|
| **Kronos-mini** | `f4e68697d9d5aed55cef5c96aabc3376bcad9f81` | `NeoQuasar/Kronos-Tokenizer-2k` (`26966d0`) | 4.1M | 15.68 MB |
| **Kronos-base** | `2b554741eca47781b64468546e77fef3e85130e6` | `NeoQuasar/Kronos-Tokenizer-base` (`0e01173`) | 102.5M | 390.30 MB |

Upstream Git Commit: `67b630e67f6a18c9e9be918d9b4337c960db1e9a` (ShiYu/Kronos, MIT License).
