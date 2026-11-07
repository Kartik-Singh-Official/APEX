import React, { useState } from 'react';
import { History, Play, AlertTriangle, CheckCircle2, TrendingUp, Layers, HelpCircle } from 'lucide-react';
import { BacktestSummary } from '../types';
import { runBacktest } from '../services/api';

interface BacktestingPageProps {
  activeSymbol: string;
  activeTimeframe: string;
}

export const BacktestingPage: React.FC<BacktestingPageProps> = ({
  activeSymbol,
  activeTimeframe,
}) => {
  const [selectedHorizon, setSelectedHorizon] = useState<string>('3d');
  const [selectedModel, setSelectedModel] = useState<string>('NeoQuasar/Kronos-mini');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<BacktestSummary | null>(null);

  const handleExecuteBacktest = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runBacktest(activeSymbol, activeTimeframe, selectedHorizon, selectedModel);
      setSummary(res);
    } catch (e: any) {
      setError(e.message || 'Backtest failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 bg-surface-lowest p-6 flex flex-col font-mono text-xs overflow-y-auto">
      {/* Header */}
      <div className="mb-6 border-b border-border pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold text-text-prominent tracking-wider flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-primary"></span>
            WALK-FORWARD VALIDATION & BASELINE BENCHMARKS
          </h1>
          <p className="text-text-muted text-[11px] mt-1">
            Leakage-free rolling origin historical evaluation comparing Kronos against Martingale, Drift, and Moving Average baselines.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-text-faint px-2 py-1 bg-surface border border-border">
          <span>METHOD: EXPANDING WALK-FORWARD (NO FUTURE CONTAMINATION)</span>
        </div>
      </div>

      {/* Control Strip */}
      <div className="bg-surface border border-border p-3.5 mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-text-muted">Target Model:</span>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-surface-lowest text-text-prominent border border-border px-2 py-1 text-xs outline-none"
            >
              <option value="NeoQuasar/Kronos-mini">Kronos-mini (4.1M)</option>
              <option value="NeoQuasar/Kronos-base">Kronos-base (102.5M)</option>
            </select>
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-[10px] text-text-muted">Horizon:</span>
            <div className="flex items-center bg-surface-lowest border border-border">
              {['1d', '3d', '5d'].map((h) => (
                <button
                  key={h}
                  onClick={() => setSelectedHorizon(h)}
                  className={`px-2.5 py-1 text-xs font-semibold ${
                    selectedHorizon === h ? 'bg-primary text-background' : 'text-text-muted hover:text-text-prominent'
                  }`}
                >
                  {h.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>

        <button
          onClick={handleExecuteBacktest}
          disabled={loading}
          className={`px-4 py-2 text-xs font-bold uppercase tracking-wider text-background transition-none flex items-center gap-1.5 ${
            loading
              ? 'bg-surface-highest text-text-muted cursor-not-allowed'
              : 'bg-primary hover:bg-primary-glow'
          }`}
        >
          {loading ? (
            <span>COMPUTING WALK-FORWARD VALIDATION...</span>
          ) : (
            <>
              <Play size={13} className="fill-current" />
              <span>RUN WALK-FORWARD BACKTEST</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-3 mb-4 bg-bear/10 border border-bear text-bear text-xs flex items-center gap-2">
          <AlertTriangle size={15} />
          <span>{error}</span>
        </div>
      )}

      {/* Results Section */}
      {summary ? (
        <div className="flex flex-col gap-6">
          {/* Outperformance Banner */}
          <div
            className={`p-3.5 border flex items-center justify-between ${
              summary.outperforms_no_change
                ? 'bg-bull/10 border-bull/40 text-bull'
                : 'bg-amber/10 border-amber/40 text-amber'
            }`}
          >
            <div className="flex items-center gap-2">
              <CheckCircle2 size={16} />
              <span className="font-bold text-xs uppercase">
                {summary.outperforms_no_change
                  ? `ALPHA CONFIRMED: ${summary.model_name} outperforms No-Change Martingale Baseline (MAE $${summary.mae} vs $${summary.baseline_no_change_mae})`
                  : `UNDERPERFORMS BASELINE: ${summary.model_name} MAE ($${summary.mae}) higher than No-Change ($${summary.baseline_no_change_mae})`}
              </span>
            </div>
            <span className="text-[10px] text-text-faint">
              Evaluated N={summary.evaluated_samples} out-of-sample origins in {summary.evaluation_time_s}s
            </span>
          </div>

          {/* Metric Cards Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 bg-surface border border-border">
              <span className="text-[10px] text-text-muted">DIRECTIONAL ACCURACY</span>
              <div className="text-xl font-bold text-primary mt-1">
                {(summary.directional_accuracy * 100).toFixed(1)}%
              </div>
              <span className="text-[10px] text-text-faint mt-1 block">
                Balanced: {(summary.balanced_accuracy * 100).toFixed(1)}%
              </span>
            </div>

            <div className="p-3 bg-surface border border-border">
              <span className="text-[10px] text-text-muted">BRIER SCORE (CALIBRATION)</span>
              <div className="text-xl font-bold text-text-prominent mt-1">{summary.brier_score.toFixed(4)}</div>
              <span className="text-[10px] text-text-faint mt-1 block">Benchmark: 0.2500 (Random)</span>
            </div>

            <div className="p-3 bg-surface border border-border">
              <span className="text-[10px] text-text-muted">MEAN ABSOLUTE ERROR (MAE)</span>
              <div className="text-xl font-bold text-text-prominent mt-1">${summary.mae.toLocaleString()}</div>
              <span className="text-[10px] text-text-faint mt-1 block">RMSE: ${summary.rmse.toLocaleString()}</span>
            </div>

            <div className="p-3 bg-surface border border-border">
              <span className="text-[10px] text-text-muted">EMPIRICAL 95% COVERAGE</span>
              <div className="text-xl font-bold text-bull mt-1">{(summary.coverage_95 * 100).toFixed(1)}%</div>
              <span className="text-[10px] text-text-faint mt-1 block">
                80% Coverage: {(summary.coverage_80 * 100).toFixed(1)}%
              </span>
            </div>
          </div>

          {/* Comparative Baseline Table */}
          <div className="bg-surface border border-border p-4">
            <h3 className="font-bold text-xs text-text-prominent uppercase tracking-wider mb-3">
              MODEL ERROR VS SIMPLE NAIVE BASELINES
            </h3>
            <table className="w-full text-left border-collapse text-[11px]">
              <thead>
                <tr className="border-b border-border bg-surface-lowest text-text-faint uppercase text-[10px]">
                  <th className="py-2 px-3">Predictive Model / Baseline</th>
                  <th className="py-2 px-3 text-right">MAE ($)</th>
                  <th className="py-2 px-3 text-right">Relative Error vs Best</th>
                  <th className="py-2 px-3 text-center">Verdict</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-border/40 bg-primary/5">
                  <td className="py-2 px-3 font-bold text-primary">{summary.model_name} (Kronos Deep AutoRegressive)</td>
                  <td className="py-2 px-3 text-right font-bold text-primary">${summary.mae.toLocaleString()}</td>
                  <td className="py-2 px-3 text-right font-bold text-bull">Primary Candidate</td>
                  <td className="py-2 px-3 text-center">
                    <span className="px-1.5 py-0.2 bg-primary/20 text-primary border border-primary/30 text-[9px] font-bold">
                      PROBABILISTIC ML
                    </span>
                  </td>
                </tr>

                <tr className="border-b border-border/40 hover:bg-surface-high">
                  <td className="py-2 px-3 text-text-prominent">No-Change Baseline (Martingale P_t+h = P_t)</td>
                  <td className="py-2 px-3 text-right text-text-standard">${summary.baseline_no_change_mae.toLocaleString()}</td>
                  <td className="py-2 px-3 text-right text-text-muted">
                    {((summary.baseline_no_change_mae - summary.mae) / summary.mae * 100).toFixed(1)}% delta
                  </td>
                  <td className="py-2 px-3 text-center text-text-faint">Baseline A</td>
                </tr>

                <tr className="border-b border-border/40 hover:bg-surface-high">
                  <td className="py-2 px-3 text-text-prominent">Historical Drift Baseline (P_t * (1 + μ_h))</td>
                  <td className="py-2 px-3 text-right text-text-standard">${summary.baseline_drift_mae.toLocaleString()}</td>
                  <td className="py-2 px-3 text-right text-text-muted">
                    {((summary.baseline_drift_mae - summary.mae) / summary.mae * 100).toFixed(1)}% delta
                  </td>
                  <td className="py-2 px-3 text-center text-text-faint">Baseline B</td>
                </tr>

                <tr className="hover:bg-surface-high">
                  <td className="py-2 px-3 text-text-prominent">Moving Average Baseline (20-bar SMA)</td>
                  <td className="py-2 px-3 text-right text-text-standard">${summary.baseline_sma_mae.toLocaleString()}</td>
                  <td className="py-2 px-3 text-right text-text-muted">
                    {((summary.baseline_sma_mae - summary.mae) / summary.mae * 100).toFixed(1)}% delta
                  </td>
                  <td className="py-2 px-3 text-center text-text-faint">Baseline C</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="p-8 bg-surface border border-border text-center text-text-muted">
          Select target model and horizon, then click <strong className="text-primary font-mono">RUN WALK-FORWARD BACKTEST</strong> to initiate chronological walk-forward validation.
        </div>
      )}
    </div>
  );
};
