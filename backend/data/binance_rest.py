"""Binance Public Market Data REST Connector.
Features:
- Rate-limited fetching with exponential backoff & jitter
- Strict OHLCV integrity validation
- Historical pagination and backfilling
- UTC timestamp alignment
- Missing candle detection
"""
import time
import random
import logging
from typing import List, Tuple, Optional
import requests
from backend.core.config import settings
from backend.data.models import CandleData

logger = logging.getLogger("apex.data.rest")


def get_interval_ms(timeframe: str) -> int:
    """Return milliseconds in a candle interval."""
    mapping = {
        "1h": 3600 * 1000,
        "4h": 4 * 3600 * 1000,
        "1d": 24 * 3600 * 1000,
        "1w": 7 * 24 * 3600 * 1000,
    }
    if timeframe not in mapping:
        raise ValueError(f"Unsupported timeframe: {timeframe}")
    return mapping[timeframe]


class BinanceRestClient:
    def __init__(self, base_url: str = settings.binance_rest_base):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "APEX-Terminal/4.12.0",
            "Accept": "application/json"
        })
        self.last_request_time = 0.0
        self.min_request_interval = 0.1  # 100ms throttle (max 10 req/s to respect rate limits)

    def _throttle(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()

    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
        max_retries: int = 4
    ) -> List[CandleData]:
        """Fetch raw klines from Binance public REST endpoint with exponential backoff."""
        url = f"{self.base_url}/api/v3/klines"
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": min(limit, 1000),
        }
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time

        attempt = 0
        backoff = 1.0

        while attempt < max_retries:
            self._throttle()
            try:
                response = self.session.get(url, params=params, timeout=10.0)
                if response.status_code == 200:
                    raw_data = response.json()
                    candles = []
                    now_ms = int(time.time() * 1000)
                    interval_ms = get_interval_ms(interval)

                    for item in raw_data:
                        open_time = int(item[0])
                        close_time = int(item[6])
                        o = float(item[1])
                        h = float(item[2])
                        l = float(item[3])
                        c = float(item[4])
                        vol = float(item[5])
                        amt = float(item[7])
                        trades = int(item[8])

                        # Candle is considered closed if now is strictly past the close_time
                        is_closed = now_ms > close_time

                        # Data Quality Check: OHLC integrity
                        quality = "VALID"
                        if o <= 0 or h <= 0 or l <= 0 or c <= 0:
                            quality = "ANOMALY"
                        elif h < max(o, c) or l > min(o, c):
                            quality = "ANOMALY"
                        elif not is_closed:
                            quality = "PROVISIONAL"

                        candle = CandleData(
                            symbol=symbol.upper(),
                            timeframe=interval,
                            open_time=open_time,
                            close_time=close_time,
                            open=o,
                            high=h,
                            low=l,
                            close=c,
                            volume=vol,
                            amount=amt,
                            trades_count=trades,
                            is_closed=is_closed,
                            provider="binance_spot",
                            received_at=now_ms,
                            quality_status=quality,
                        )
                        candles.append(candle)
                    return candles

                elif response.status_code == 429:
                    logger.warning("Binance REST 429 rate limit encountered. Backing off.")
                    time.sleep(backoff + random.uniform(0.5, 1.5))
                    backoff *= 2.0
                else:
                    logger.error(f"Binance REST error HTTP {response.status_code}: {response.text}")
                    time.sleep(backoff)
                    backoff *= 1.5
            except Exception as e:
                logger.warning(f"Binance REST fetch failed (attempt {attempt+1}/{max_retries}): {e}")
                time.sleep(backoff)
                backoff *= 2.0
            attempt += 1

        raise ConnectionError(f"Failed to fetch klines from Binance for {symbol} {interval} after {max_retries} attempts.")

    def backfill(self, symbol: str, interval: str, target_count: int = 500) -> Tuple[List[CandleData], int]:
        """Backfill historical candles up to target_count candles.
        Returns (list_of_candles, missing_count).
        """
        all_candles: dict[int, CandleData] = {}
        interval_ms = get_interval_ms(interval)
        
        # Start from latest candles
        batch = self.fetch_klines(symbol, interval, limit=min(target_count, 1000))
        for c in batch:
            all_candles[c.open_time] = c

        # Paginate backwards if needed
        while len(all_candles) < target_count:
            oldest_open_time = min(all_candles.keys())
            end_time = oldest_open_time - 1
            older_batch = self.fetch_klines(symbol, interval, end_time=end_time, limit=min(target_count - len(all_candles), 1000))
            if not older_batch:
                break
            added = 0
            for c in older_batch:
                if c.open_time not in all_candles:
                    all_candles[c.open_time] = c
                    added += 1
            if added == 0:
                break

        sorted_candles = sorted(all_candles.values(), key=lambda x: x.open_time)

        # Detect missing candles in sequence
        missing_count = 0
        for i in range(len(sorted_candles) - 1):
            diff = sorted_candles[i + 1].open_time - sorted_candles[i].open_time
            if diff > interval_ms:
                skipped = int((diff - interval_ms) // interval_ms)
                missing_count += skipped

        return sorted_candles, missing_count

