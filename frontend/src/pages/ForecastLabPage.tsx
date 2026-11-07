import React, { useState } from 'react';
import { Cpu, Play, CheckCircle2, TrendingUp, AlertCircle, BarChart2 } from 'lucide-react';
import { ForecastResult, ModelHealth } from '../types';
import { generateForecast, switchModel } from '../services/api';

interface ForecastLabPageProps {
  activeSymbol: string;
  activeTimeframe: string;
  modelHealth: ModelHealth | null;
  onForecastGenerated: (res: ForecastResult) => void;
}

export const ForecastLabPage: React.FC<ForecastLabPageProps> = ({
  activeSymbol,
  activeTimeframe,
  modelHealth,
  onForecastGenerated,
}) => {
  const [selectedModel, setSelectedModel] = useState<string>('NeoQuasar/Kronos-mini');
  const [selectedHorizon, setSelectedHorizon] = useState<string>('3d');
  const [sampleCount, setSampleCount] = useState<number>(5);
  const [temperature, setTemperature] = useState<number>(0.8);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [forecastResult, setForecastResult] = useState<ForecastResult | null>(null);

  const handleRunInference = async () => {
    setLoading(true);
    setError(null);
    try {
      // Ensure model is loaded/switched if different
      if (modelHealth?.active_model !== selectedModel) {
        await switchModel(selectedModel);
      }
      const res = await generateForecast(
        activeSymbol,
        activeTimeframe,
        selectedHorizon,
        selectedModel,
        sampleCount
      );
      setForecastResult(res);
      onForecastGenerated(res);
    } catch (e: any) {
      setError(e.message || 'Forecast generation failed');
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
            KRONOS FORECAST BENCHMARK LAB
          </h1>
          <p className="text-text-muted text-[11px] mt-1">
            Evaluate and compare autoregressive multi-step candlestick trajectories on Apple Silicon MPS.
          </p>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-text-faint px-2 py-1 bg-surface border border-border">
          <span>TARGET: {activeSymbol}</span>
          <span>TF: {activeTimeframe}</span>
        </div>
      </div>

      {/* Control Panel Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        {/* Model Architecture */}
        <div className="bg-surface border border-border p-3 flex flex-col gap-2">
          <span className="text-text-muted text-[10px] font-bold uppercase">1. MODEL ARCHITECTURE</span>
          <div className="flex flex-col gap-1.5">
            <label
              className={`p-2 border flex items-center justify-between cursor-pointer ${
                selectedModel === 'NeoQuasar/Kronos-mini'
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border text-text-muted hover:border-text-faint'
              }`}
            >
              <div className="flex items-center gap-2">
                <input
                  type="radio"
                  name="model"
                  checked={selectedModel === 'NeoQuasar/Kronos-mini'}
                  onChange={() => setSelectedModel('NeoQuasar/Kronos-mini')}
                  className="accent-primary"
                />
                <div>
                  <div className="font-bold text-xs text-text-prominent">Kronos-mini</div>
                  <div className="text-[10px] text-text-muted">4.1M params • 15.7 MB • Latency ~40ms</div>
                </div>
              </div>
              <span className="text-[9px] px-1 bg-surface-high border border-border">FAST INFERENCE</span>
            </label>

            <label
              className={`p-2 border flex items-center justify-between cursor-pointer ${
                selectedModel === 'NeoQuasar/Kronos-base'
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border text-text-muted hover:border-text-faint'
              }`}
            >
              <div className="flex items-center gap-2">
                <input
                  type="radio"
                  name="model"
                  checked={selectedModel === 'NeoQuasar/Kronos-base'}
                  onChange={() => setSelectedModel('NeoQuasar/Kronos-base')}
                  className="accent-primary"
                />
                <div>
                  <div className="font-bold text-xs text-text-prominent">Kronos-base</div>
                  <div className="text-[10px] text-text-muted">102.5M params • 390.3 MB • Higher Capacity</div>
                </div>
              </div>
              <span className="text-[9px] px-1 bg-surface-high border border-border">DEEP ARCHITECTURE</span>
            </label>
          </div>
        </div>

        {/* Forecast Horizon */}
        <div className="bg-surface border border-border p-3 flex flex-col gap-2">
          <span className="text-text-muted text-[10px] font-bold uppercase">2. FORECAST HORIZON</span>
          <div className="grid grid-cols-3 gap-2">
            {['1d', '3d', '5d'].map((h) => (
              <button
                key={h}
                onClick={() => setSelectedHorizon(h)}
                className={`py-3 border text-center font-bold text-sm transition-colors ${
                  selectedHorizon === h
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border text-text-muted hover:bg-surface-high'
                }`}
              >
                {h.toUpperCase()}
                <div className="text-[9px] font-normal text-text-faint mt-1">
                  {h === '1d' ? '6 candles' : h === '3d' ? '18 candles' : '30 candles'}
                </div>
              </button>
            ))}
          </div>

          <div className="mt-2 text-[10px] text-text-muted flex justify-between">
            <span>Sampling Paths: {sampleCount}</span>
            <input
              type="range"
              min="1"
              max="10"
              value={sampleCount}
              onChange={(e) => setSampleCount(Number(e.target.value))}
              className="w-24 accent-primary"
            />
          </div>
        </div>

        {/* Trigger Execution */}
        <div className="bg-surface border border-border p-3 flex flex-col justify-between">
          <div>
            <span className="text-text-muted text-[10px] font-bold uppercase">3. RUNTIME HARDWARE DISPATCH</span>
            <div className="mt-2 text-[11px] text-text-standard flex flex-col gap-1">
              <div className="flex justify-between">
                <span>Inference Device:</span>
                <span className="text-primary font-bold">{modelHealth?.device?.toUpperCase() || 'MPS'}</span>
              </div>
              <div className="flex justify-between">
                <span>Unified RAM:</span>
                <span className="text-text-prominent">{(modelHealth?.memory_resident_mb || 450).toFixed(0)} MB</span>
              </div>
              <div className="flex justify-between">
                <span>Sampling Mode:</span>
                <span className="text-text-prominent">Multinomial Autoregressive</span>
              </div>
            </div>
          </div>

          <button
            onClick={handleRunInference}
            disabled={loading}
            className={`w-full py-2.5 text-xs font-bold uppercase tracking-wider text-background transition-none flex items-center justify-center gap-2 mt-4 ${
              loading
                ? 'bg-surface-highest text-text-muted cursor-not-allowed'
                : 'bg-primary hover:bg-primary-glow'
            }`}
          >
            {loading ? (
              <span>RUNNING AUTOREGRESSION...</span>
            ) : (
              <>
                <Play size={14} className="fill-current" />
                <span>EXECUTE LOCAL BENCHMARK</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-3 mb-4 bg-bear/10 border border-bear text-bear text-xs flex items-center gap-2">
          <AlertCircle size={15} />
          <span>{error}</span>
        </div>
      )}

      {/* Result Display */}
      {forecastResult && (
        <div className="bg-surface border border-border p-4 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <span className="font-bold text-sm text-text-prominent flex items-center gap-2">
              <CheckCircle2 size={15} className="text-bull" />
              BENCHMARK COMPLETED: {forecastResult.model_metadata.model_name} on {forecastResult.model_metadata.device.toUpperCase()}
            </span>
            <span className="text-[10px] text-text-muted">
              Latency: {forecastResult.model_metadata.latency_ms}ms • Sample Count: {forecastResult.model_metadata.sample_count}
            </span>
          </div>

          {/* Metrics summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-2.5 bg-surface-lowest border border-border">
              <div className="text-[10px] text-text-muted">CURRENT CLOSE</div>
              <div className="text-base font-bold text-text-prominent">${forecastResult.current_price.toLocaleString()}</div>
            </div>
            <div className="p-2.5 bg-surface-lowest border border-border">
              <div className="text-[10px] text-text-muted">MEDIAN TARGET</div>
              <div className="text-base font-bold text-primary">${forecastResult.median_target_price.toLocaleString()}</div>
            </div>
            <div className="p-2.5 bg-surface-lowest border border-border">
              <div className="text-[10px] text-text-muted">EXPECTED ALPHA</div>
              <div className={`text-base font-bold ${forecastResult.expected_return_pct >= 0 ? 'text-bull' : 'text-bear'}`}>
                {forecastResult.expected_return_pct >= 0 ? '+' : ''}{forecastResult.expected_return_pct}%
              </div>
            </div>
            <div className="p-2.5 bg-surface-lowest border border-border">
              <div className="text-[10px] text-text-muted">CALIBRATED PROBABILITY</div>
              <div className="text-base font-bold text-bull">
                {forecastResult.is_confidence_available && forecastResult.calibrated_prob
                  ? `${(forecastResult.calibrated_prob * 100).toFixed(1)}%`
                  : 'UNAVAILABLE'}
              </div>
            </div>
          </div>

          {/* Forecasted Candles Table */}
          <div className="overflow-x-auto">
            <div className="text-[10px] font-bold text-text-muted uppercase mb-2">
              FORWARD PREDICTED CANDLES ({forecastResult.predicted_candles.length} STEPS)
            </div>
            <table className="w-full text-left border-collapse text-[11px]">
              <thead>
                <tr className="border-b border-border bg-surface-lowest text-text-faint uppercase text-[10px]">
                  <th className="py-1.5 px-3">Future Time (UTC)</th>
                  <th className="py-1.5 px-3 text-right">Pred Open</th>
                  <th className="py-1.5 px-3 text-right">Pred High</th>
                  <th className="py-1.5 px-3 text-right">Pred Low</th>
                  <th className="py-1.5 px-3 text-right">Pred Close</th>
                  <th className="py-1.5 px-3 text-right">Pred Volume</th>
                </tr>
              </thead>
              <tbody>
                {forecastResult.predicted_candles.map((c, i) => (
                  <tr key={i} className="border-b border-border/40 hover:bg-surface-high">
                    <td className="py-1.5 px-3 font-mono text-text-standard">
                      {new Date(c.timestamp).toUTCString().replace(' GMT', '')}
                    </td>
                    <td className="py-1.5 px-3 text-right text-text-prominent">${c.open.toLocaleString()}</td>
                    <td className="py-1.5 px-3 text-right text-bull">${c.high.toLocaleString()}</td>
                    <td className="py-1.5 px-3 text-right text-bear">${c.low.toLocaleString()}</td>
                    <td className="py-1.5 px-3 text-right text-primary font-bold">${c.close.toLocaleString()}</td>
                    <td className="py-1.5 px-3 text-right text-text-muted">{c.volume.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

