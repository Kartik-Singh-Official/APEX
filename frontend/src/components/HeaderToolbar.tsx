import React from 'react';
import { Cpu, RefreshCw, Radio, Layers, Eye } from 'lucide-react';
import { ModelHealth } from '../types';

interface HeaderToolbarProps {
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  selectedTimeframe: string;
  onSelectTimeframe: (tf: string) => void;
  currentPrice: number;
  priceDeltaPct: number;
  isLive: boolean;
  freshnessMs: number;
  modelHealth: ModelHealth | null;
  indicatorsVisible: {
    ema: boolean;
    vol: boolean;
    sr: boolean;
    cone: boolean;
  };
  onToggleIndicator: (key: 'ema' | 'vol' | 'sr' | 'cone') => void;
  onRefresh: () => void;
  onRunForecast: () => void;
  isGeneratingForecast: boolean;
}

export const HeaderToolbar: React.FC<HeaderToolbarProps> = ({
  selectedSymbol,
  onSelectSymbol,
  selectedTimeframe,
  onSelectTimeframe,
  currentPrice,
  priceDeltaPct,
  isLive,
  freshnessMs,
  modelHealth,
  indicatorsVisible,
  onToggleIndicator,
  onRefresh,
  onRunForecast,
  isGeneratingForecast,
}) => {
  const symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'];
  const timeframes = ['1h', '4h', '1d', '1w'];

  const formattedPrice = currentPrice > 0 ? `$${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '---';
  const deltaColor = priceDeltaPct >= 0 ? 'text-bull' : 'text-bear';
  const deltaSign = priceDeltaPct >= 0 ? '+' : '';

  const activeModelShort = modelHealth?.active_model ? modelHealth.active_model.replace('NeoQuasar/', '') : 'Kronos-mini';
  const deviceShort = modelHealth?.device ? modelHealth.device.toUpperCase() : 'MPS';

  return (
    <header className="h-9 px-3 bg-surface border-b border-border flex items-center justify-between shrink-0 select-none z-30 font-mono text-xs">
      {/* Left section: Pair selector, price, and timeframe */}
      <div className="flex items-center gap-3">
        {/* Symbol Selector */}
        <div className="flex items-center gap-1 bg-surface-lowest border border-border px-1 py-0.5">
          <select
            value={selectedSymbol}
            onChange={(e) => onSelectSymbol(e.target.value)}
            className="bg-transparent text-text-prominent font-bold cursor-pointer outline-none text-xs"
          >
            {symbols.map((s) => (
              <option key={s} value={s} className="bg-surface-high text-text-prominent">
                {s.replace('USDT', '/USDT')}
              </option>
            ))}
          </select>
          <span className="text-primary font-bold ml-1">{formattedPrice}</span>
          <span className={`font-bold ml-1 ${deltaColor}`}>
            {deltaSign}{priceDeltaPct.toFixed(2)}%
          </span>
        </div>

        {/* Timeframe switcher */}
        <div className="flex items-center bg-surface-low border border-border">
          {timeframes.map((tf) => (
            <button
              key={tf}
              onClick={() => onSelectTimeframe(tf)}
              className={`px-2 py-0.5 text-[11px] font-semibold transition-colors ${
                selectedTimeframe === tf
                  ? 'bg-surface-highest text-primary border-x border-primary'
                  : 'text-text-muted hover:text-text-prominent'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>

        {/* Indicators toggle strip */}
        <div className="hidden lg:flex items-center gap-1 text-[10px]">
          <button
            onClick={() => onToggleIndicator('ema')}
            className={`px-1.5 py-0.5 border ${
              indicatorsVisible.ema
                ? 'bg-primary/10 border-primary text-primary font-semibold'
                : 'border-border text-text-muted hover:text-text-prominent'
            }`}
          >
            EMA (20/50/200)
          </button>
          <button
            onClick={() => onToggleIndicator('vol')}
            className={`px-1.5 py-0.5 border ${
              indicatorsVisible.vol
                ? 'bg-primary/10 border-primary text-primary font-semibold'
                : 'border-border text-text-muted hover:text-text-prominent'
            }`}
          >
            VOL
          </button>
          <button
            onClick={() => onToggleIndicator('sr')}
            className={`px-1.5 py-0.5 border ${
              indicatorsVisible.sr
                ? 'bg-primary/10 border-primary text-primary font-semibold'
                : 'border-border text-text-muted hover:text-text-prominent'
            }`}
          >
            S/R ZONES
          </button>
          <button
            onClick={() => onToggleIndicator('cone')}
            className={`px-1.5 py-0.5 border ${
              indicatorsVisible.cone
                ? 'bg-primary/10 border-primary text-primary font-semibold'
                : 'border-border text-text-muted hover:text-text-prominent'
            }`}
          >
            FORECAST CONE
          </button>
        </div>
      </div>

      {/* Right section: Engine info, freshness indicator, actions */}
      <div className="flex items-center gap-2.5">
        {/* Engine Runtime Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-2 py-0.5 bg-surface-lowest border border-border text-text-muted text-[11px]">
          <Cpu size={12} className="text-primary" />
          <span>{activeModelShort}</span>
          <span className="text-primary font-semibold">[{deviceShort}]</span>
        </div>

        {/* Live Feed Freshness */}
        <div className="flex items-center gap-1.5 px-2 py-0.5 bg-bull/10 border border-bull/30 text-bull text-[11px] font-semibold">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-bull opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-bull"></span>
          </span>
          <span>LIVE ({freshnessMs}ms)</span>
        </div>

        {/* Refresh button */}
        <button
          onClick={onRefresh}
          className="p-1 text-text-muted hover:text-primary transition-colors border border-border hover:border-primary"
          title="Refresh candles & indicators"
        >
          <RefreshCw size={13} />
        </button>

        {/* Run Forecast Button */}
        <button
          onClick={onRunForecast}
          disabled={isGeneratingForecast}
          className={`px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider text-background transition-none ${
            isGeneratingForecast
              ? 'bg-surface-highest text-text-muted cursor-not-allowed'
              : 'bg-primary hover:bg-primary-glow'
          }`}
        >
          {isGeneratingForecast ? 'CALCULATING...' : 'GENERATE FORECAST'}
        </button>
      </div>
    </header>
  );
};
