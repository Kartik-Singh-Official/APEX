import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle2,
  AlertTriangle,
  PlusCircle,
  HelpCircle,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { AnalysisThesis, ForecastResult } from '../types';

interface RightAnalysisPanelProps {
  analysis: AnalysisThesis | null;
  forecast: ForecastResult | null;
  currentPrice: number;
  onLogPaperTrade: (stance: string, target: number, stopLoss: number) => void;
}

export const RightAnalysisPanel: React.FC<RightAnalysisPanelProps> = ({
  analysis,
  forecast,
  currentPrice,
  onLogPaperTrade,
}) => {
  const [isLogged, setIsLogged] = useState(false);

  const stance = analysis?.research_stance || 'NEUTRAL';
  const isBull = stance.includes('BULLISH');
  const isBear = stance.includes('BEARISH');

  const stanceBadgeBg = isBull
    ? 'bg-bull text-background'
    : isBear
    ? 'bg-bear text-text-prominent'
    : 'bg-surface-high text-text-standard';

  const probDisplay =
    analysis?.calibrated_prob !== null && analysis?.calibrated_prob !== undefined
      ? `${(analysis.calibrated_prob * 100).toFixed(1)}%`
      : 'UNAVAILABLE';

  const targetPrice = forecast?.median_target_price || analysis?.expected_price_target || currentPrice;
  const expectedReturn = forecast?.expected_return_pct ?? analysis?.expected_return_pct ?? 0.0;
  const var95 = forecast?.var_95_pct ?? analysis?.var_95_pct ?? -3.5;
  const horizon = forecast?.horizon_label || analysis?.horizon_label || '3d';

  const stopLossPrice = isBull
    ? currentPrice * (1.0 - Math.abs(var95) / 100)
    : currentPrice * (1.0 + Math.abs(var95) / 100);

  const handleCreatePaperSignal = () => {
    onLogPaperTrade(stance, targetPrice, stopLossPrice);
    setIsLogged(true);
    setTimeout(() => setIsLogged(false), 3000);
  };

  return (
    <aside className="w-[340px] bg-surface-low border-l border-border flex flex-col shrink-0 select-none overflow-y-auto font-mono text-xs">
      {/* Header Bar */}
      <div className="h-7 px-3 bg-surface border-b border-border flex items-center justify-between shrink-0">
        <span className="text-[11px] font-bold text-text-muted tracking-wider uppercase flex items-center gap-1.5">
          <TrendingUp size={13} className="text-primary" />
          QUANTITATIVE INFERENCE
        </span>
        <span className="text-[9px] px-1 py-0 bg-primary/10 text-primary border border-primary/30">
          PROBABILISTIC THESIS
        </span>
      </div>

      <div className="p-3 flex flex-col gap-2.5">
        {/* 1. Research Stance Card */}
        <div className="p-2.5 bg-surface border border-border flex flex-col gap-2">
          <div className="flex items-center justify-between text-[10px] text-text-muted">
            <span>RESEARCH STANCE</span>
            <span className="text-primary font-bold">DIRECTIONAL ALPHA</span>
          </div>

          <div className="flex items-center justify-between">
            <div className={`px-2.5 py-1 text-sm font-bold tracking-wider uppercase ${stanceBadgeBg}`}>
              {stance.replace('_', ' ')}
            </div>
            <div className="text-right">
              <div className="text-lg font-bold text-primary">
                {probDisplay}
              </div>
              <div className="text-[9px] text-text-muted">
                CALIBRATED PROBABILITY
              </div>
            </div>
          </div>

          <div className="text-[10px] text-text-faint border-t border-border/60 pt-1 flex items-center justify-between">
            <span>{analysis?.confidence_interval_str || 'Confidence unavailable'}</span>
            <span>N={analysis?.sample_count ?? 0}</span>
          </div>
        </div>

        {/* 2. Forecast Horizon & Alpha Targets */}
        <div className="p-2.5 bg-surface border border-border flex flex-col gap-1.5 text-[11px]">
          <div className="flex justify-between items-center text-text-muted">
            <span>HORIZON EXP. RETURN</span>
            <span className={`font-bold ${expectedReturn >= 0 ? 'text-bull' : 'text-bear'}`}>
              {expectedReturn >= 0 ? '+' : ''}{expectedReturn.toFixed(2)}% [{horizon.toUpperCase()}]
            </span>
          </div>
          <div className="flex justify-between items-center text-text-muted">
            <span>MEDIAN PRICE TARGET</span>
            <span className="text-primary font-bold">
              ${targetPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>
          <div className="flex justify-between items-center text-text-muted">
            <span>VALUE AT RISK (VaR 95%)</span>
            <span className="text-bear font-semibold">
              {var95.toFixed(2)}% (${stopLossPrice.toFixed(0)})
            </span>
          </div>

          {/* Empirical Confidence Strip */}
          <div className="mt-1 pt-1.5 border-t border-border/60">
            <div className="flex justify-between text-[9px] text-text-faint mb-1">
              <span>95% L: ${forecast?.range_95_low?.toLocaleString() || (currentPrice * 0.95).toFixed(0)}</span>
              <span>95% U: ${forecast?.range_95_high?.toLocaleString() || (currentPrice * 1.05).toFixed(0)}</span>
            </div>
            <div className="h-2 w-full bg-surface-lowest border border-border relative flex items-center">
              <div className="absolute left-[15%] right-[15%] h-full bg-primary/20 border-x border-primary" />
              <div
                className="absolute h-3 w-0.5 bg-text-prominent shadow-sm z-10"
                style={{ left: '50%' }}
                title="Forecast Median"
              />
            </div>
          </div>
        </div>

        {/* 3. Detected Patterns */}
        <div className="p-2.5 bg-surface border border-border flex flex-col gap-1.5">
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-primary font-bold tracking-wider">PATTERN RECOGNITION</span>
            <span className="px-1 py-0 text-[9px] bg-bull/15 text-bull border border-bull/30">CONFIRMED</span>
          </div>
          <div className="text-xs font-semibold text-text-prominent">
            {analysis?.detected_patterns?.length
              ? analysis.detected_patterns.slice(0, 2).join(' • ')
              : 'No major chart patterns active'}
          </div>
          <div className="flex justify-between items-center text-[10px] text-text-muted border-t border-border/60 pt-1">
            <span>REGIME:</span>
            <span className="text-text-prominent font-semibold">{analysis?.market_regime || 'CONSOLIDATION'}</span>
          </div>
        </div>

        {/* 4. Structured Thesis Breakdown */}
        <div className="p-2.5 bg-surface border border-border flex flex-col gap-2 text-[10px]">
          <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">
            SYSTEMATIC THESIS BREAKDOWN
          </span>

          {/* Supporting Factors */}
          <div className="flex flex-col gap-1">
            <span className="text-bull font-semibold uppercase flex items-center gap-1">
              <PlusCircle size={11} /> Supporting Drivers (+)
            </span>
            <ul className="text-text-standard space-y-1 pl-1">
              {analysis?.supporting_factors?.length ? (
                analysis.supporting_factors.map((f, i) => (
                  <li key={i} className="flex items-start gap-1">
                    <span className="text-bull">•</span>
                    <span>{f}</span>
                  </li>
                ))
              ) : (
                <li className="text-text-faint">No strong supporting factors</li>
              )}
            </ul>
          </div>

          {/* Conflicting Factors */}
          <div className="flex flex-col gap-1 pt-1 border-t border-border/60">
            <span className="text-bear font-semibold uppercase flex items-center gap-1">
              <AlertTriangle size={11} /> Conflicting / Risk Factors (-)
            </span>
            <ul className="text-text-standard space-y-1 pl-1">
              {analysis?.conflicting_factors?.length ? (
                analysis.conflicting_factors.map((f, i) => (
                  <li key={i} className="flex items-start gap-1">
                    <span className="text-bear">•</span>
                    <span>{f}</span>
                  </li>
                ))
              ) : (
                <li className="text-text-faint">No conflicting factors detected</li>
              )}
            </ul>
          </div>

          {/* Invalidation Condition */}
          <div className="p-2 bg-surface-lowest border border-border/80 text-[10px] flex flex-col gap-1">
            <span className="text-amber font-semibold uppercase flex items-center gap-1">
              <ShieldAlert size={11} /> Thesis Invalidation:
            </span>
            <span className="text-text-muted">{analysis?.invalidation_conditions || 'Defined on structural pivot violation.'}</span>
          </div>
        </div>

        {/* 5. Paper Trade Execution Trigger */}
        <button
          onClick={handleCreatePaperSignal}
          className={`w-full py-2 px-3 text-xs font-mono font-bold tracking-wider uppercase transition-none border flex items-center justify-center gap-1.5 ${
            isLogged
              ? 'bg-bull text-background border-bull'
              : 'bg-surface-high hover:bg-surface-highest text-text-prominent border-border hover:border-primary'
          }`}
        >
          {isLogged ? (
            <>
              <CheckCircle2 size={13} />
              <span>RECORDED IN JOURNAL</span>
            </>
          ) : (
            <>
              <ArrowRight size={13} className="text-primary" />
              <span>LOG PAPER TRADE IN JOURNAL</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
};

