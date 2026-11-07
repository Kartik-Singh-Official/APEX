# Quantitative Forecasting & Uncertainty Calibration Methodology

## 1. Forecast Horizon Mapping

APEX supports swing research horizons rather than noisy micro-scalping:

| Timeframe | Horizon Label | Autoregressive Step Count | Realized Window |
|---|---|---|---|
| **4h** | 1d | 6 candles | 24 hours |
| **4h** | 3d | 18 candles | 72 hours |
| **4h** | 5d | 30 candles | 120 hours |
| **1d** | 1d | 1 candle | 24 hours |
| **1d** | 3d | 3 candles | 72 hours |
| **1d** | 5d | 5 candles | 120 hours |

## 2. Distinction: Model Confidence vs Historical Reliability

A common pitfall in algorithmic machine learning is confusing the softmax probability output of a neural model or the dispersion of random sampling paths with true forward-looking predictive reliability.

In Kronos, multinomial sampling across $K$ autoregressive paths generates candidate paths, but an average across these paths is not a calibrated probability distribution.

### Calibration Framework
APEX derives directional probability and empirical forecast corridors strictly from **out-of-sample historical validation residuals**:

1. **Directional Probability**:
   For an asset/timeframe/horizon, let $\mathcal{D}_{\text{val}}$ be the chronologically separated out-of-sample walk-forward evaluation set where past forecasts $\hat{r}_i$ and realized returns $r_i$ are recorded.
   $$P(r > 0 \mid \hat{r} > 0) = \frac{\sum_{i=1}^{N} \mathbf{1}(r_i > 0 \land \hat{r}_i > 0)}{\sum_{i=1}^{N} \mathbf{1}(\hat{r}_i > 0)}$$
2. **Wilson Score Confidence Interval**:
   Because sample sizes in financial time series are finite, APEX computes the 95% Wilson score interval for the binomial proportion:
   $$w = \frac{\hat{p} + \frac{z^2}{2N} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{N} + \frac{z^2}{4N^2}}}{1 + \frac{z^2}{N}}$$
3. **Threshold for Credibility**:
   If $N < 20$ out-of-sample observations are available, the platform refuses to fabricate a confidence number and explicitly outputs:
   `"Insufficient validation data — confidence unavailable."`
4. **Empirical Prediction Bands (80% and 95%)**:
   Rather than assuming Gaussian returns (which fail in crypto due to fat tails), the upper and lower forecast cones are built directly from the empirical $2.5\%$, $10\%$, $90\%$, and $97.5\%$ quantiles of historical out-of-sample residuals:
   $$\text{Range}_{95\%} = \left[ \hat{P}_{\text{target}} \cdot (1 + q_{0.025}), \; \hat{P}_{\text{target}} \cdot (1 + q_{0.975}) \right]$$

