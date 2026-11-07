"""Market Data Models and Provenance Tracking."""
from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, Field


class CandleData(BaseModel):
    symbol: str
    timeframe: str
    open_time: int
    close_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float
    trades_count: int = 0
    is_closed: bool = True
    provider: str = "binance_spot"
    received_at: int = Field(default_factory=lambda: int(datetime.now(timezone.utc).timestamp() * 1000))
    quality_status: Literal["VALID", "PROVISIONAL", "GAP_FILLED", "ANOMALY"] = "VALID"

    @property
    def open_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.open_time / 1000.0, tz=timezone.utc)

    @property
    def close_datetime(self) -> datetime:
        return datetime.fromtimestamp(self.close_time / 1000.0, tz=timezone.utc)


class DataHealthInfo(BaseModel):
    provider: str = "binance_spot"
    status: Literal["ONLINE", "DEGRADED", "OFFLINE"] = "ONLINE"
    connected: bool = True
    last_update_ms: int = 0
    freshness_ms: int = 0
    last_closed_candle_time: Optional[int] = None
    missing_candles_count: int = 0
    stored_candles_count: int = 0
    last_error: Optional[str] = None
    active_symbols: list[str] = []
    active_timeframes: list[str] = []
