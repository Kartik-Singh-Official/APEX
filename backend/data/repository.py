"""Data Repository for Candle Storage, Retrieval, and Health Auditing."""
import sqlite3
import time
from typing import List, Optional, Tuple
import pandas as pd
from backend.core.config import settings
from backend.database.db import get_sync_db
from backend.data.models import CandleData, DataHealthInfo
from backend.data.binance_rest import get_interval_ms


class CandleRepository:
    def __init__(self, db_path=settings.db_path):
        self.db_path = db_path

    def save_candles(self, candles: List[CandleData]) -> int:
        """Insert or replace candle records with provenance."""
        if not candles:
            return 0
        conn = get_sync_db()
        inserted = 0
        try:
            records = [
                (
                    c.symbol,
                    c.timeframe,
                    c.open_time,
                    c.close_time,
                    c.open,
                    c.high,
                    c.low,
                    c.close,
                    c.volume,
                    c.amount,
                    c.trades_count,
                    1 if c.is_closed else 0,
                    c.provider,
                    c.received_at,
                    c.quality_status,
                )
                for c in candles
            ]
            cursor = conn.cursor()
            cursor.executemany(
                """
                INSERT OR REPLACE INTO candles (
                    symbol, timeframe, open_time, close_time, open, high, low, close,
                    volume, amount, trades_count, is_closed, provider, received_at, quality_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )
            inserted = cursor.rowcount
            conn.commit()
        finally:
            conn.close()
        return inserted

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        only_closed: bool = False
    ) -> List[CandleData]:
        """Retrieve chronological candle records."""
        conn = get_sync_db()
        try:
            cursor = conn.cursor()
            query = """
                SELECT symbol, timeframe, open_time, close_time, open, high, low, close,
                       volume, amount, trades_count, is_closed, provider, received_at, quality_status
                FROM candles
                WHERE symbol = ? AND timeframe = ?
            """
            params = [symbol.upper(), timeframe]
            if only_closed:
                query += " AND is_closed = 1"
            query += " ORDER BY open_time DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            # Reverse to chronological order (oldest to newest)
            candles = [
                CandleData(
                    symbol=row["symbol"],
                    timeframe=row["timeframe"],
                    open_time=row["open_time"],
                    close_time=row["close_time"],
                    open=row["open"],
                    high=row["high"],
                    low=row["low"],
                    close=row["close"],
                    volume=row["volume"],
                    amount=row["amount"],
                    trades_count=row["trades_count"],
                    is_closed=bool(row["is_closed"]),
                    provider=row["provider"],
                    received_at=row["received_at"],
                    quality_status=row["quality_status"],
                )
                for row in reversed(rows)
            ]
            return candles
        finally:
            conn.close()

    def get_candles_df(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        only_closed: bool = True
    ) -> pd.DataFrame:
        """Return pandas DataFrame indexed by UTC timestamps for ML inference & TA."""
        candles = self.get_candles(symbol, timeframe, limit=limit, only_closed=only_closed)
        if not candles:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume", "amount", "timestamps"])

        data = {
            "open": [c.open for c in candles],
            "high": [c.high for c in candles],
            "low": [c.low for c in candles],
            "close": [c.close for c in candles],
            "volume": [c.volume for c in candles],
            "amount": [c.amount for c in candles],
            "open_time": [c.open_time for c in candles],
            "close_time": [c.close_time for c in candles],
            "is_closed": [c.is_closed for c in candles],
        }
        df = pd.DataFrame(data)
        df["timestamps"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
        return df

    def get_data_health(self, symbol: str, timeframe: str) -> DataHealthInfo:
        """Compute live health status, missing count, and freshness metrics."""
        candles = self.get_candles(symbol, timeframe, limit=500, only_closed=False)
        now_ms = int(time.time() * 1000)

        if not candles:
            return DataHealthInfo(
                provider="binance_spot",
                status="OFFLINE",
                connected=False,
                last_update_ms=0,
                freshness_ms=0,
                last_closed_candle_time=None,
                missing_candles_count=0,
                stored_candles_count=0,
                last_error="No candles stored for this asset/timeframe",
                active_symbols=settings.supported_symbols,
                active_timeframes=settings.supported_timeframes,
            )

        interval_ms = get_interval_ms(timeframe)
        latest_candle = candles[-1]
        last_closed = next((c for c in reversed(candles) if c.is_closed), None)

        freshness_ms = max(0, now_ms - latest_candle.received_at)

        # Count gaps
        missing_count = 0
        for i in range(len(candles) - 1):
            diff = candles[i + 1].open_time - candles[i].open_time
            if diff > interval_ms:
                skipped = int((diff - interval_ms) // interval_ms)
                missing_count += skipped

        # Status determination
        # If last candle received is > 2 intervals old, consider DEGRADED
        status = "ONLINE"
        if freshness_ms > interval_ms * 2:
            status = "DEGRADED"

        return DataHealthInfo(
            provider="binance_spot",
            status=status,
            connected=True,
            last_update_ms=latest_candle.received_at,
            freshness_ms=freshness_ms,
            last_closed_candle_time=last_closed.open_time if last_closed else None,
            missing_candles_count=missing_count,
            stored_candles_count=len(candles),
            last_error=None,
            active_symbols=settings.supported_symbols,
            active_timeframes=settings.supported_timeframes,
        )
