# Walk-Forward Validation & Baseline Benchmarking

## 1. Leakage-Free Validation Principles

Financial time series violate the i.i.d. assumption. Standard $k$-fold cross validation or random train/test splitting leaks future volatility and serial correlation into historical models, producing artificially inflated backtest statistics.

APEX enforces strict chronological walk-forward validation (rolling origin):

```
Time ------------------------------------------------------------------------>
Origin t_1:  |--- Train History (<= t_1) ---| === Forecast [t_1+1 .. t_1+h] ===
Origin t_2:       |--- Train History (<= t_2) ---| === Forecast [t_2+1 .. t_2+h] ===
Origin t_3:            |--- Train History (<= t_3) ---| === Forecast [t_3+1 .. t_3+h] ===
```

- **Zero Future Information**: Bar $t$ receives data strictly timestamped $\le t$.
- **Closed Candles Only**: Unfinished bars are filtered out before entering backtest windows.
- **Untouched Target Evaluation**: Realized returns are computed on bars strictly $> t$.

## 2. Comparative Naive Baselines

A forecasting model is mathematically unproven unless it demonstrably outperforms simple baselines:

1. **No-Change Martingale Baseline**:
   $$\hat{P}_{t+h} = P_t$$
   Assumes prices follow a random walk; best single-point estimator under pure market efficiency.
2. **Historical Drift Baseline**:
   $$\hat{P}_{t+h} = P_t \cdot \left( 1 + \bar{r}_{\text{lookback}} \cdot h \right)$$
   Extrapolates recent sample mean drift across the horizon.
3. **Moving-Average Baseline**:
   $$\hat{P}_{t+h} = \text{SMA}_{20}(P_t)$$
   Tests whether deep transformer attention outperforms simple rolling linear smoothing.

## 3. Mathematical Evaluation Metrics

- **Mean Absolute Error (MAE)**:
  $$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} \left| \hat{P}_i - P_i \right|$$
- **Root Mean Squared Error (RMSE)**:
  $$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{i=1}^{N} \left( \hat{P}_i - P_i \right)^2}$$
- **Directional Accuracy**:
  $$\text{DA} = \frac{1}{N} \sum_{i=1}^{N} \mathbf{1}\left( \text{sign}(\hat{r}_i) == \text{sign}(r_i) \right)$$
- **Balanced Accuracy**:
  $$\text{BA} = \frac{\text{Sensitivity} + \text{Specificity}}{2}$$
- **Brier Score**:
  $$\text{BS} = \frac{1}{N} \sum_{i=1}^{N} \left( f_i - o_i \right)^2$$
  Measures probabilistic calibration ($0.25$ represents uninformative random guessing).
- **Outperformance Rule**:
  If a model's MAE exceeds the No-Change baseline, APEX flags the model as underperforming on that horizon and suppresses aggressive research stances.
