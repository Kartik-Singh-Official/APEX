"""APEX System Configuration and Hardware Runtime Detection.
Target: MacBook Air M5 / Apple Silicon with MPS support and CPU fallback.
"""
from pathlib import Path
from typing import List, Literal
import os
import torch
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_CACHE_DIR = BASE_DIR / "models_cache"

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_CACHE_DIR.mkdir(parents=True, exist_ok=True)


def detect_optimal_device() -> str:
    """Detect Apple Silicon MPS acceleration with verified runtime check."""
    preferred = os.getenv("INFERENCE_DEVICE", "auto").lower()
    if preferred == "cpu":
        return "cpu"
    if preferred == "mps":
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() and torch.backends.mps.is_built():
            try:
                # Verify that MPS actually executes a basic tensor op
                t = torch.ones(2, 2, device="mps")
                _ = t + t
                return "mps"
            except Exception:
                return "cpu"
        return "cpu"

    # Auto mode:
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() and torch.backends.mps.is_built():
        try:
            t = torch.ones(2, 2, device="mps")
            _ = t + t
            return "mps"
        except Exception:
            return "cpu"
    return "cpu"


class Settings(BaseModel):
    app_name: str = "APEX"
    app_version: str = "4.12.0-INSTITUTIONAL"
    db_path: Path = DATA_DIR / "apex.db"
    models_cache: Path = MODELS_CACHE_DIR
    
    # Target inference device (verified at startup)
    device: str = Field(default_factory=detect_optimal_device)
    
    # Supported Symbols & Intervals
    supported_symbols: List[str] = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    supported_timeframes: List[str] = ["1h", "4h", "1d", "1w"]
    default_symbol: str = "BTCUSDT"
    default_timeframe: str = "4h"
    
    # Supported Horizons
    # 4h: 1d (6 candles), 3d (18 candles), 5d (30 candles)
    # 1d: 1d (1 candle), 3d (3 candles), 5d (5 candles)
    horizons_map: dict = {
        "4h": {
            "1d": 6,
            "3d": 18,
            "5d": 30,
        },
        "1d": {
            "1d": 1,
            "3d": 3,
            "5d": 5,
        },
        "1h": {
            "1d": 24,
            "3d": 72,
        }
    }
    
    # Pinned Model Registrations
    model_mini_id: str = "NeoQuasar/Kronos-mini"
    model_mini_revision: str = "f4e68697d9d5aed55cef5c96aabc3376bcad9f81"
    tokenizer_mini_id: str = "NeoQuasar/Kronos-Tokenizer-2k"
    tokenizer_mini_revision: str = "26966d0035065a0cae0ebad7af8ece35bc1fb51c"
    
    model_base_id: str = "NeoQuasar/Kronos-base"
    model_base_revision: str = "2b554741eca47781b64468546e77fef3e85130e6"
    tokenizer_base_id: str = "NeoQuasar/Kronos-Tokenizer-base"
    tokenizer_base_revision: str = "0e0117387f39004a9016484a186a908917e22426"
    
    # Upstream source git commit
    kronos_upstream_commit: str = "67b630e67f6a18c9e9be918d9b4337c960db1e9a"
    
    # Market Data
    binance_rest_base: str = "https://api.binance.com"
    binance_ws_base: str = "wss://stream.binance.com:9443"


settings = Settings()
