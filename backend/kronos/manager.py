"""Kronos Model Manager for Local Apple Silicon MPS & CPU Inference.
Features:
- Lazy loading & unloading to conserve unified memory
- Verified runtime device telemetry
- Latency and memory benchmarking
- Upstream Kronos model & tokenizer wrapping
"""
import gc
import os
import resource
import time
import logging
from typing import Dict, Optional, Tuple, Any
import torch
import pandas as pd
import numpy as np

from backend.core.config import settings, detect_optimal_device
from backend.kronos.upstream import Kronos, KronosTokenizer, KronosPredictor

logger = logging.getLogger("apex.kronos.manager")


def get_process_memory_mb() -> float:
    """Return resident memory usage in MB on macOS."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # On macOS, ru_maxrss is in bytes
    return usage.ru_maxrss / (1024.0 * 1024.0)


def get_mps_memory_mb() -> float:
    """Return MPS allocated memory in MB if available."""
    if hasattr(torch, "mps") and hasattr(torch.mps, "current_allocated_memory"):
        try:
            return torch.mps.current_allocated_memory() / (1024.0 * 1024.0)
        except Exception:
            return 0.0
    return 0.0


class KronosModelManager:
    """Manages local loading, unloading, and inference of Kronos models."""

    def __init__(self):
        self.device = detect_optimal_device()
        self.active_model_name: Optional[str] = None
        self.current_model: Optional[Kronos] = None
        self.current_tokenizer: Optional[KronosTokenizer] = None
        self.current_predictor: Optional[KronosPredictor] = None
        
        self.last_load_time: float = 0.0
        self.last_inference_latency_ms: float = 0.0
        self.last_forecast_time: Optional[int] = None
        self.inference_count: int = 0
        
        # Registry metadata
        self.registry = {
            "NeoQuasar/Kronos-mini": {
                "name": "Kronos-mini",
                "model_id": settings.model_mini_id,
                "model_revision": settings.model_mini_revision,
                "tokenizer_id": settings.tokenizer_mini_id,
                "tokenizer_revision": settings.tokenizer_mini_revision,
                "parameter_count": "4.1M",
                "size_mb": 15.68,
            },
            "NeoQuasar/Kronos-base": {
                "name": "Kronos-base",
                "model_id": settings.model_base_id,
                "model_revision": settings.model_base_revision,
                "tokenizer_id": settings.tokenizer_base_id,
                "tokenizer_revision": settings.tokenizer_base_revision,
                "parameter_count": "102.5M",
                "size_mb": 390.30,
            },
        }

    def unload_current_model(self):
        """Unload active model to immediately release unified memory."""
        if self.current_model is not None or self.current_tokenizer is not None:
            logger.info(f"Unloading model {self.active_model_name} from memory...")
            del self.current_predictor
            del self.current_model
            del self.current_tokenizer
            self.current_predictor = None
            self.current_model = None
            self.current_tokenizer = None
            self.active_model_name = None
            gc.collect()
            if self.device == "mps" and hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
                try:
                    torch.mps.empty_cache()
                except Exception:
                    pass

    def load_model(self, model_key: str = "NeoQuasar/Kronos-mini", device: Optional[str] = None):
        """Lazily load a Kronos model and tokenizer onto the target device."""
        if model_key not in self.registry:
            raise ValueError(f"Unknown model key '{model_key}'. Available: {list(self.registry.keys())}")

        if device:
            self.device = device
        else:
            self.device = detect_optimal_device()

        # If already loaded on the requested device, return
        if self.active_model_name == model_key and self.current_predictor is not None:
            return

        # Avoid keeping multiple large models in memory
        self.unload_current_model()

        t0 = time.time()
        meta = self.registry[model_key]
        logger.info(f"Loading {meta['name']} ({meta['model_id']}) onto {self.device}...")

        # Load Tokenizer & Model from HuggingFace cache
        tokenizer = KronosTokenizer.from_pretrained(
            meta["tokenizer_id"],
            cache_dir=str(settings.models_cache)
        )
        model = Kronos.from_pretrained(
            meta["model_id"],
            cache_dir=str(settings.models_cache)
        )

        # Move to target device with verification
        try:
            tokenizer = tokenizer.to(self.device)
            model = model.to(self.device)
            model.eval()
            
            predictor = KronosPredictor(
                model=model,
                tokenizer=tokenizer,
                device=self.device,
                max_context=512,
                clip=5.0
            )
        except Exception as e:
            if self.device == "mps":
                logger.warning(f"Failed to place {meta['name']} on MPS: {e}. Falling back to CPU.")
                self.device = "cpu"
                tokenizer = tokenizer.to("cpu")
                model = model.to("cpu")
                model.eval()
                predictor = KronosPredictor(
                    model=model,
                    tokenizer=tokenizer,
                    device="cpu",
                    max_context=512,
                    clip=5.0
                )
            else:
                raise

        self.current_tokenizer = tokenizer
        self.current_model = model
        self.current_predictor = predictor
        self.active_model_name = model_key
        self.last_load_time = time.time() - t0
        logger.info(f"Loaded {meta['name']} in {self.last_load_time:.2f}s on {self.device}.")

    def generate_forecast(
        self,
        df: pd.DataFrame,
        pred_len: int,
        sample_count: int = 5,
        temperature: float = 0.8,
        top_p: float = 0.9,
        model_key: str = "NeoQuasar/Kronos-mini",
        freq: str = "4h"
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """Generate forward candlestick forecasts using official KronosPredictor.
        Returns:
            (pred_df, metadata_dict)
        """
        # Ensure model is loaded
        if self.active_model_name != model_key or self.current_predictor is None:
            self.load_model(model_key)

        assert self.current_predictor is not None

        # Clean historical input
        if len(df) < 30:
            raise ValueError(f"Insufficient historical data: {len(df)} candles provided. Need at least 30.")

        df_input = df[["open", "high", "low", "close", "volume", "amount"]].copy()
        x_timestamp = pd.Series(pd.to_datetime(df["timestamps"]))

        # Construct future timestamps
        last_time = x_timestamp.iloc[-1]
        future_dates = pd.date_range(start=last_time, periods=pred_len + 1, freq=freq)[1:]
        y_timestamp = pd.Series(future_dates)

        t_start = time.time()
        
        # Execute official predictor
        # When sample_count > 1, Kronos generates multiple autoregressive paths and averages them
        pred_df = self.current_predictor.predict(
            df=df_input,
            x_timestamp=x_timestamp,
            y_timestamp=y_timestamp,
            pred_len=pred_len,
            T=temperature,
            top_p=top_p,
            sample_count=sample_count,
            verbose=False,
        )
        
        latency_ms = (time.time() - t_start) * 1000.0
        self.last_inference_latency_ms = latency_ms
        self.last_forecast_time = int(time.time() * 1000)
        self.inference_count += 1

        meta = self.registry[self.active_model_name]
        info = {
            "model_name": meta["name"],
            "model_id": meta["model_id"],
            "model_revision": meta["model_revision"],
            "tokenizer_id": meta["tokenizer_id"],
            "device": self.device,
            "latency_ms": round(latency_ms, 2),
            "memory_resident_mb": round(get_process_memory_mb(), 2),
            "memory_mps_mb": round(get_mps_memory_mb(), 2),
            "sample_count": sample_count,
            "pred_len": pred_len,
            "generated_at": self.last_forecast_time,
        }

        return pred_df, info

    def get_health(self) -> Dict[str, Any]:
        """Telemetry diagnostics for Model Health monitor."""
        return {
            "active_model": self.active_model_name,
            "device": self.device,
            "is_mps_available": hasattr(torch.backends, "mps") and torch.backends.mps.is_available(),
            "is_mps_built": hasattr(torch.backends, "mps") and torch.backends.mps.is_built(),
            "last_load_time_s": round(self.last_load_time, 2),
            "last_latency_ms": round(self.last_inference_latency_ms, 2),
            "inference_count": self.inference_count,
            "last_forecast_timestamp": self.last_forecast_time,
            "memory_resident_mb": round(get_process_memory_mb(), 2),
            "memory_mps_mb": round(get_mps_memory_mb(), 2),
            "available_models": list(self.registry.keys()),
        }


# Global singleton instance
model_manager = KronosModelManager()

