# Kronos Neural Forecasting Integration

## 1. Upstream Provenance & Attribution

- **Official Upstream Repository**: [https://github.com/shiyu-coder/Kronos](https://github.com/shiyu-coder/Kronos)
- **Pinned Git Commit**: `67b630e67f6a18c9e9be918d9b4337c960db1e9a`
- **Hugging Face Hub**: `https://huggingface.co/NeoQuasar`
- **License**: MIT License (Copyright 2025 ShiYu)

APEX uses the authentic upstream implementation without approximation. All core modules (`Kronos`, `KronosTokenizer`, `KronosPredictor`, `BSQuantizer`, `TransformerBlock`) are vendored cleanly in `backend/kronos/upstream/` with full provenance preservation.

## 2. Pinned Model Checkpoints & Revisions

| Candidate | Model Checkpoint ID | Git SHA Revision | Tokenizer ID | Tokenizer Revision | Parameters | Disk Size |
|---|---|---|---|---|---|---|
| **Primary** | `NeoQuasar/Kronos-mini` | `f4e68697d9d5aed55cef5c96aabc3376bcad9f81` | `NeoQuasar/Kronos-Tokenizer-2k` | `26966d0035065a0cae0ebad7af8ece35bc1fb51c` | 4.1M | 15.68 MB |
| **Comparison** | `NeoQuasar/Kronos-base` | `2b554741eca47781b64468546e77fef3e85130e6` | `NeoQuasar/Kronos-Tokenizer-base` | `0e0117387f39004a9016484a186a908917e22426` | 102.5M | 390.30 MB |

## 3. Hardware Runtime & Apple Silicon MPS Acceleration

APEX is built to run natively on Apple Silicon (M-series, e.g. M1/M2/M3/M4/M5) with 16 GB unified memory:

1. **Metal Performance Shaders (MPS)**:
   - At startup, the system probes `torch.backends.mps.is_available()` and `torch.backends.mps.is_built()`.
   - It performs an actual operational verification tensor computation on `mps:0`.
   - If verified, the tokenizer and model are transferred to `device="mps"`.
   - If any MPS execution error occurs, the manager catches it safely and falls back to CPU without crashing.
2. **Memory Protection & Lazy Loading**:
   - To preserve the 16 GB unified memory envelope, only one model is loaded at any given time.
   - When switching from `Kronos-mini` to `Kronos-base`, the manager invokes explicit memory release:
     ```python
     del self.current_model
     del self.current_tokenizer
     gc.collect()
     torch.mps.empty_cache()
     ```
   - Process resident memory (`ru_maxrss`) and MPS memory allocations are monitored continuously.

## 4. Input Alignment & Data Preparation

In accordance with Kronos requirements, input series must be chronological and strictly structured:
- Feature vector: `[open, high, low, close, volume, amount]`
- Standardized via dynamic z-score normalization:
  $$x_{\text{norm}} = \frac{x - \mu}{\sigma + 10^{-5}}$$
- Clipped within $[-5.0, 5.0]$
- Temporal timestamp calendar features:
  - `minute`, `hour`, `weekday`, `day`, `month`
- Autoregressive multi-step decoding produces future OHLCV sequences preserving exact UTC timestamps.

