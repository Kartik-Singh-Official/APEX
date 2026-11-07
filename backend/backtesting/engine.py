"""Walk-Forward Backtesting & Model Validation Engine for APEX.
Implements:
- Chronological walk-forward validation (rolling origin)
- Strict leakage-free timestamp alignment
- Benchmark comparisons (No-Change, Historical Drift, Moving Average)
- Comprehensive metrics: MAE, RMSE, Directional Accuracy, Balanced Accuracy,
  Brier Score, Empirical Coverage (80%, 95%), Calibration Diagnostics
"""
import time
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from pydantic import BaseModel

from backend.kronos.manager import model_manager
from backend.core.config import settings


class BacktestMetricSummary(BaseModel):
    model_name: str
    horizon_label: str
    evaluated_samples: int
    mae: float
    rmse: float
    directional_accuracy: float
    balanced_accuracy: float
    brier_score: float
    coverage_80: float
    coverage_95: float
    # Baselines
    baseline_no_change_mae: float
    baseline_drift_mae: float
    baseline_sma_mae: float
    outperforms_no_change: bool
    evaluation_time_s: float


class BacktestWalkForwardEngine:
    def __init__(self, df: pd.DataFrame, timeframe: str = "4h"):
        self.df = df.copy()
        self.timeframe = timeframe
        # Ensure only closed candles are in backtest
        if "is_closed" in self.df.columns:
            self.df = self.df[self.df["is_closed"] == 1].copy()
        self.df = self.df.sort_values("open_time").reset_index(drop=True)

    def run_walk_forward(
        self,
        horizon_label: str = "3d",
        model_key: str = "NeoQuasar/Kronos-mini",
        min_history_bars: int = 80,
        step_bars: int = 12,
        max_origins: int = 25
    ) -> BacktestMetricSummary:
        """Execute chronologically separated walk-forward evaluation.
        At each rolling origin t:
        - Past data strictly <= t is provided to the model.
        - Predict next pred_len bars.
        - Evaluate against realized bars from t+1 to t+pred_len.
        """
        t0 = time.time()
        pred_len = settings.horizons_map.get(self.timeframe, {}).get(horizon_label, 18)
        n = len(self.df)

        if n < min_history_bars + pred_len + 10:
            raise ValueError(f"Insufficient history for walk-forward: {n} candles. Need at least {min_history_bars + pred_len + 10}.")

        origins = []
        # Create rolling origins backwards from end of dataframe
        start_idx = n - pred_len - 1
        curr = start_idx
        while curr >= min_history_bars and len(origins) < max_origins:
            origins.append(curr)
            curr -= step_bars

        origins.reverse()  # Chronological order

        model_errors = []
        squared_errors = []
        directional_hits = []
        tp, fp, tn, fn = 0, 0, 0, 0
        brier_scores = []
        in_80_count = 0
        in_95_count = 0

        # Baselines
        no_change_errors = []
        drift_errors = []
        sma_errors = []

        for origin in origins:
            history_df = self.df.iloc[:origin + 1].copy()
            future_actual = self.df.iloc[origin + 1: origin + 1 + pred_len].copy()

            if len(future_actual) < pred_len:
                continue

            current_close = float(history_df["close"].iloc[-1])
            realized_target = float(future_actual["close"].iloc[-1])
            realized_return = (realized_target - current_close) / current_close

            # 1. Kronos Model Forecast
            pred_df, _ = model_manager.generate_forecast(
                df=history_df.tail(min_history_bars),
                pred_len=pred_len,
                sample_count=3,
                model_key=model_key,
                freq=self.timeframe,
            )
            model_target = float(pred_df["close"].iloc[-1])
            model_return = (model_target - current_close) / current_close

            # Error metrics
            err = abs(model_target - realized_target)
            model_errors.append(err)
            squared_errors.append(err ** 2)

            # Directional metrics
            pred_dir = 1 if model_return >= 0 else -1
            real_dir = 1 if realized_return >= 0 else -1
            is_hit = (pred_dir == real_dir)
            directional_hits.append(1 if is_hit else 0)

            if pred_dir == 1 and real_dir == 1:
                tp += 1
            elif pred_dir == 1 and real_dir == -1:
                fp += 1
            elif pred_dir == -1 and real_dir == -1:
                tn += 1
            else:
                fn += 1

            # Brier score
            prob_up = 1.0 if pred_dir == 1 else 0.0
            actual_up = 1.0 if real_dir == 1 else 0.0
            brier_scores.append((prob_up - actual_up) ** 2)

            # 2. Baseline A: No-Change (Martingale)
            no_change_pred = current_close
            no_change_errors.append(abs(no_change_pred - realized_target))

            # 3. Baseline B: Historical Drift
            past_returns = history_df["close"].pct_change().dropna()
            mean_drift = past_returns.mean() * pred_len
            drift_pred = current_close * (1.0 + mean_drift)
            drift_errors.append(abs(drift_pred - realized_target))

            # 4. Baseline C: 20-bar Moving Average
            sma20_pred = float(history_df["close"].tail(20).mean())
            sma_errors.append(abs(sma20_pred - realized_target))

            # Empirical Coverage checks
            std_ret = past_returns.std() * np.sqrt(pred_len)
            c80_low = current_close * (1.0 - 1.28 * std_ret)
            c80_high = current_close * (1.0 + 1.28 * std_ret)
            c95_low = current_close * (1.0 - 1.96 * std_ret)
            c95_high = current_close * (1.0 + 1.96 * std_ret)

            if c80_low <= realized_target <= c80_high:
                in_80_count += 1
            if c95_low <= realized_target <= c95_high:
                in_95_count += 1

        total_samples = len(model_errors)
        if total_samples == 0:
            raise RuntimeError("Zero valid evaluation steps in walk-forward backtest.")

        mae = float(np.mean(model_errors))
        rmse = float(np.sqrt(np.mean(squared_errors)))
        dir_acc = float(np.mean(directional_hits))

        # Balanced Accuracy = 0.5 * (TPR + TNR)
        tpr = tp / (tp + fn) if (tp + fn) > 0 else 0.5
        tnr = tn / (tn + fp) if (tn + fp) > 0 else 0.5
        bal_acc = float(0.5 * (tpr + tnr))

        brier = float(np.mean(brier_scores))
        cov_80 = in_80_count / total_samples
        cov_95 = in_95_count / total_samples

        no_change_mae = float(np.mean(no_change_errors))
        drift_mae = float(np.mean(drift_errors))
        sma_mae = float(np.mean(sma_errors))

        eval_time = time.time() - t0

        return BacktestMetricSummary(
            model_name=model_key.split("/")[-1],
            horizon_label=horizon_label,
            evaluated_samples=total_samples,
            mae=round(mae, 2),
            rmse=round(rmse, 2),
            directional_accuracy=round(dir_acc, 3),
            balanced_accuracy=round(bal_acc, 3),
            brier_score=round(brier, 4),
            coverage_80=round(cov_80, 3),
            coverage_95=round(cov_95, 3),
            baseline_no_change_mae=round(no_change_mae, 2),
            baseline_drift_mae=round(drift_mae, 2),
            baseline_sma_mae=round(sma_mae, 2),
            outperforms_no_change=bool(mae < no_change_mae),
            evaluation_time_s=round(eval_time, 2),
        )

