import React, { useState } from 'react';
import { MarketStructure, PaperRecord } from '../types';

interface BottomMultiPaneProps {
  structure: MarketStructure | null;
  paperRecords: PaperRecord[];
  activeSymbol: string;
}

export const BottomMultiPane: React.FC<BottomMultiPaneProps> = ({
  structure,
  paperRecords,
  activeSymbol,
}) => {
  const [activeTab, setActiveTab] = useState<'regime' | 'ledger'>('regime');

  const regimeRows = [
    {
      tf: '1h',
      regime: structure?.regime === 'TRENDING_BULL' ? 'Trending Bull' : 'Consolidation',
      trend: structure?.trend || 'NEUTRAL',
      volState: 'Expansion',
      atrPct: `${structure?.atr_percentile || 54}%`,
    },
    {
      tf: '4h',
      regime: structure?.regime ? structure.regime.replace('_', ' ') : 'Consolidation',
      trend: structure?.trend || 'NEUTRAL',
      volState: structure?.volatility_state || 'NORMAL',
      atrPct: `${structure?.atr_percentile || 50}%`,
    },
    {
      tf: '1d',
      regime: 'Macro Accumulation',
      trend: 'BULLISH',
      volState: 'Normal',
      atrPct: '62%',
    },
  ];

  return (
    <footer className="h-44 bg-surface border-t border-border flex flex-col shrink-0 select-none font-mono text-xs z-10">
      {/* Tab Header Strip */}
      <div className="h-7 px-3 bg-surface-lowest border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveTab('regime')}
            className={`px-3 py-1 text-[11px] font-semibold border-b-2 transition-colors ${
              activeTab === 'regime'
                ? 'border-primary text-primary bg-surface/60'
                : 'border-transparent text-text-muted hover:text-text-prominent'
            }`}
          >
            MULTI-TIMEFRAME REGIME MATRIX
          </button>
          <button
            onClick={() => setActiveTab('ledger')}
            className={`px-3 py-1 text-[11px] font-semibold border-b-2 transition-colors ${
              activeTab === 'ledger'
                ? 'border-primary text-primary bg-surface/60'
                : 'border-transparent text-text-muted hover:text-text-prominent'
            }`}
          >
            PREDICTION EVALUATION & PAPER LEDGER ({paperRecords.length})
          </button>
        </div>
        <div className="text-[10px] text-text-faint">
          ACTIVE ASSET: {activeSymbol}
        </div>
      </div>

      {/* Pane Content */}
      <div className="flex-1 overflow-y-auto p-2">
        {activeTab === 'regime' ? (
          <table className="w-full text-left border-collapse text-[11px]">
            <thead>
              <tr className="border-b border-border text-text-faint uppercase text-[10px]">
                <th className="py-1 px-2">Timeframe</th>
                <th className="py-1 px-2">Market Regime</th>
                <th className="py-1 px-2">Structural Bias</th>
                <th className="py-1 px-2">Volatility State</th>
                <th className="py-1 px-2 text-right">ATR Percentile</th>
              </tr>
            </thead>
            <tbody>
              {regimeRows.map((r) => (
                <tr key={r.tf} className="border-b border-border/40 hover:bg-surface-high">
                  <td className="py-1.5 px-2 font-bold text-primary">{r.tf}</td>
                  <td className="py-1.5 px-2 text-text-prominent">{r.regime}</td>
                  <td className="py-1.5 px-2">
                    <span
                      className={`px-1.5 py-0.2 text-[10px] font-bold ${
                        r.trend === 'BULLISH'
                          ? 'bg-bull/15 text-bull'
                          : r.trend === 'BEARISH'
                          ? 'bg-bear/15 text-bear'
                          : 'bg-surface-high text-text-muted'
                      }`}
                    >
                      {r.trend}
                    </span>
                  </td>
                  <td className="py-1.5 px-2 text-text-standard">{r.volState}</td>
                  <td className="py-1.5 px-2 text-right text-text-prominent">{r.atrPct}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="w-full">
            {paperRecords.length === 0 ? (
              <div className="text-text-faint text-center py-6 text-xs">
                No paper positions recorded yet. Click 'LOG PAPER TRADE IN JOURNAL' in the right panel to test a thesis.
              </div>
            ) : (
              <table className="w-full text-left border-collapse text-[11px]">
                <thead>
                  <tr className="border-b border-border text-text-faint uppercase text-[10px]">
                    <th className="py-1 px-2">Time</th>
                    <th className="py-1 px-2">Pair</th>
                    <th className="py-1 px-2">Stance</th>
                    <th className="py-1 px-2 text-right">Entry</th>
                    <th className="py-1 px-2 text-right">Target</th>
                    <th className="py-1 px-2 text-right">Stop Loss</th>
                    <th className="py-1 px-2 text-center">Status</th>
                    <th className="py-1 px-2 text-right">Net PnL</th>
                  </tr>
                </thead>
                <tbody>
                  {paperRecords.map((rec) => {
                    const isWin = rec.status === 'WIN';
                    const isLoss = rec.status === 'LOSS';
                    return (
                      <tr key={rec.id} className="border-b border-border/40 hover:bg-surface-high">
                        <td className="py-1 px-2 text-text-muted">
                          {new Date(rec.entry_time).toLocaleTimeString()}
                        </td>
                        <td className="py-1 px-2 font-bold text-text-prominent">{rec.symbol}</td>
                        <td className="py-1 px-2">
                          <span
                            className={`px-1 py-0 text-[10px] ${
                              rec.stance.includes('BULL') ? 'text-bull' : 'text-bear'
                            }`}
                          >
                            {rec.stance}
                          </span>
                        </td>
                        <td className="py-1 px-2 text-right">${rec.entry_price.toLocaleString()}</td>
                        <td className="py-1 px-2 text-right text-primary">${rec.target_price.toLocaleString()}</td>
                        <td className="py-1 px-2 text-right text-bear">${rec.stop_loss.toLocaleString()}</td>
                        <td className="py-1 px-2 text-center">
                          <span
                            className={`px-1.5 py-0.2 text-[9px] font-bold ${
                              isWin
                                ? 'bg-bull/20 text-bull border border-bull/40'
                                : isLoss
                                ? 'bg-bear/20 text-bear border border-bear/40'
                                : 'bg-surface-high text-text-muted'
                            }`}
                          >
                            {rec.status}
                          </span>
                        </td>
                        <td
                          className={`py-1 px-2 text-right font-bold ${
                            rec.net_pnl_pct && rec.net_pnl_pct >= 0 ? 'text-bull' : 'text-bear'
                          }`}
                        >
                          {rec.net_pnl_pct !== null && rec.net_pnl_pct !== undefined
                            ? `${rec.net_pnl_pct >= 0 ? '+' : ''}${rec.net_pnl_pct}%`
                            : '---'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>
    </footer>
  );
};

