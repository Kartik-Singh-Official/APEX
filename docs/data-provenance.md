# Market Data Engine & Provenance Audit

## 1. Provider & Data Integrity Principles

APEX implements a zero-synthetic market data rule. Every price point, volume bar, and candlestick in the database is ingested from genuine public cryptocurrency spot markets without fabrication or interpolation.

- **Primary Provider**: Binance Public Spot Market API.
- **Protocol**: 
  - REST: `https://api.binance.com/api/v3/klines`
  - WebSocket: `wss://stream.binance.com:9443/ws` and `/stream`
- **Authentication**: None required. Operates purely on public spot order books and trade aggregates. No exchange API keys, account credentials, or trading permissions are requested or stored.

## 2. Ingestion Lifecycle & Candle Finalization

```
+--------------------------+
|  Binance Public Stream   |
+--------------------------+
              |
              v (kline payload)
+--------------------------+       x == False
|   WebSocket Ingestion    | -------------------> In-Memory Provisional Tick
|      Connector           |                      (Broadcast to Frontend UI)
+--------------------------+
              |
              | x == True (Closed Candle)
              v
+--------------------------+
|  Validation & Provenance | ---> Verify OHLC: H >= max(O,C), L <= min(O,C), V >= 0
+--------------------------+
              |
              v (Passed)
+--------------------------+
|  SQLite Repository Save  | ---> INSERT OR REPLACE INTO candles (...)
+--------------------------+
              |
              v
+--------------------------+
| Paper Settlement Engine  | ---> Check Open Target/Stop-loss vs Realized Price
+--------------------------+
```

## 3. Data Schema & Provenance Metadata

Every stored candle record in SQLite carries immutable provenance fields:
- `symbol`: Ticker symbol (e.g. `BTCUSDT`).
- `timeframe`: Granularity (`1h`, `4h`, `1d`, `1w`).
- `open_time`: Unix UTC timestamp in milliseconds.
- `close_time`: Unix UTC timestamp in milliseconds.
- `open`, `high`, `low`, `close`: Genuine spot execution levels.
- `volume`: Base asset volume.
- `amount`: Quote asset traded volume (volume * price).
- `trades_count`: Aggregated trade count.
- `is_closed`: Boolean flag (1 = Confirmed, 0 = Provisional).
- `provider`: `'binance_spot'`.
- `received_at`: Local machine receipt timestamp (UTC ms).
- `quality_status`: `'VALID'`, `'PROVISIONAL'`, or `'ANOMALY'`.

## 4. Gap and Anomaly Detection

- The repository checks chronological continuity on every query:
  $$\Delta t = t_{i+1} - t_i$$
- If $\Delta t > \text{interval\_ms}$, missing candle count is incremented:
  $$\text{gaps} = \left\lfloor \frac{\Delta t - \text{interval\_ms}}{\text{interval\_ms}} \right\rfloor$$
- Missing intervals are displayed prominently on the Data Health screen.

