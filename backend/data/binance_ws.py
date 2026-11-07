"""Binance WebSocket Live Stream Connector with Auto-Reconnection & Candle Finalization."""
import asyncio
import json
import logging
import time
from typing import Callable, Dict, List, Optional, Set
import websockets
from backend.core.config import settings
from backend.data.models import CandleData
from backend.data.repository import CandleRepository

logger = logging.getLogger("apex.data.ws")


class BinanceWsClient:
    def __init__(self, repository: CandleRepository):
        self.repository = repository
        self.running = False
        self.connected = False
        self.last_msg_time = 0.0
        self.reconnect_delay = 2.0
        self.max_reconnect_delay = 30.0
        self.task: Optional[asyncio.Task] = None
        self.subscribers: List[Callable[[CandleData], None]] = []
        self.latest_ticks: Dict[str, CandleData] = {}
        self.active_streams: Set[str] = set()

    def add_subscriber(self, callback: Callable[[CandleData], None]):
        self.subscribers.append(callback)

    def _notify(self, candle: CandleData):
        key = f"{candle.symbol}_{candle.timeframe}"
        self.latest_ticks[key] = candle
        for sub in self.subscribers:
            try:
                sub(candle)
            except Exception as e:
                logger.error(f"Error in ws subscriber callback: {e}")

    def _build_stream_url(self) -> str:
        # Subscribe to BTCUSDT, ETHUSDT, SOLUSDT across 1h, 4h, 1d
        streams = []
        for sym in settings.supported_symbols:
            for tf in ["1h", "4h", "1d"]:
                stream = f"{sym.lower()}@kline_{tf}"
                streams.append(stream)
                self.active_streams.add(stream)
        stream_path = "/".join(streams)
        return f"{settings.binance_ws_base}/stream?streams={stream_path}"

    async def start(self):
        """Start the background WebSocket loop."""
        self.running = True
        self.task = asyncio.create_task(self._run_loop())

    async def stop(self):
        """Stop the background WebSocket loop."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.connected = False

    async def _run_loop(self):
        while self.running:
            url = self._build_stream_url()
            logger.info(f"Connecting to Binance WebSocket streams ({len(self.active_streams)} streams)...")
            try:
                async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                    self.connected = True
                    self.reconnect_delay = 2.0
                    logger.info("Binance WebSocket stream connected successfully.")
                    
                    while self.running:
                        msg = await ws.recv()
                        self.last_msg_time = time.time()
                        await self._handle_message(msg)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.connected = False
                logger.warning(f"Binance WebSocket disconnected: {e}. Reconnecting in {self.reconnect_delay:.1f}s...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 1.5, self.max_reconnect_delay)

    async def _handle_message(self, raw_msg: str):
        try:
            payload = json.loads(raw_msg)
            data = payload.get("data")
            if not data or data.get("e") != "kline":
                return
            
            k = data["k"]
            symbol = k["s"].upper()
            interval = k["i"]
            open_time = int(k["t"])
            close_time = int(k["T"])
            o = float(k["o"])
            c = float(k["c"])
            h = float(k["h"])
            l = float(k["l"])
            v = float(k["v"])
            q = float(k["q"])
            n = int(k["n"])
            is_closed = bool(k["x"])

            now_ms = int(time.time() * 1000)
            quality = "VALID" if is_closed else "PROVISIONAL"

            candle = CandleData(
                symbol=symbol,
                timeframe=interval,
                open_time=open_time,
                close_time=close_time,
                open=o,
                high=h,
                low=l,
                close=c,
                volume=v,
                amount=q,
                trades_count=n,
                is_closed=is_closed,
                provider="binance_spot",
                received_at=now_ms,
                quality_status=quality,
            )

            # If closed, persist directly to DB
            if is_closed:
                self.repository.save_candles([candle])

            # Broadcast update
            self._notify(candle)
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

