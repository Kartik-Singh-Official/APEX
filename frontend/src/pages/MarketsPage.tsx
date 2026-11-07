import React from 'react';
import { TrendingUp, TrendingDown, ArrowRight, Zap, CheckCircle2 } from 'lucide-react';
import { MarketStructure } from '../types';

interface MarketsPageProps {
  activeSymbol: string;
  onSelectSymbol: (symbol: string) => void;
  currentPrices: Record<string, { price: number; change24h: number; volume24h: string; trend: string }>;
  structure: MarketStructure | null;
}

export const MarketsPage: React.FC<MarketsPageProps> = ({
  activeSymbol,
  onSelectSymbol,
  currentPrices,
  structure,
}) => {
  const defaultMarkets = [
    {
      symbol: 'BTCUSDT',
      name: 'Bitcoin / Tether USD',
      basePrice: currentPrices['BTCUSDT']?.price || 76094.95,
      change24h: currentPrices['BTCUSDT']?.change24h || 2.41,
      vol24h: currentPrices['BTCUSDT']?.volume24h || '$28.4B',
      trend: currentPrices['BTCUSDT']?.trend || (structure?.trend || 'BULLISH'),
      forecastStance: 'BULLISH (+4.82% / 72h)',
    },
    {
      symbol: 'ETHUSDT',
      name: 'Ethereum / Tether USD',
      basePrice: currentPrices['ETHUSDT']?.price || 2840.5,
      change24h: currentPrices['ETHUSDT']?.change24h || 1.15,
      vol24h: currentPrices['ETHUSDT']?.volume24h || '$14.2B',
      trend: currentPrices['ETHUSDT']?.trend || 'CONSOLIDATION',
      forecastStance: 'NEUTRAL (+0.45% / 72h)',
    },
    {
      symbol: 'SOLUSDT',
      name: 'Solana / Tether USD',
      basePrice: currentPrices['SOLUSDT']?.price || 188.75,
      change24h: currentPrices['SOLUSDT']?.change24h || -0.85,
      vol24h: currentPrices['SOLUSDT']?.volume24h || '$4.8B',
      trend: currentPrices['SOLUSDT']?.trend || 'BEARISH',
      forecastStance: 'BEARISH (-2.14% / 72h)',
    },
  ];

  return (
    <div className="flex-1 bg-surface-lowest p-6 flex flex-col font-mono text-xs overflow-y-auto">
      {/* Header */}
      <div className="mb-6 border-b border-border pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold text-text-prominent tracking-wider flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-primary"></span>
            INSTITUTIONAL SPOT WATCHLIST
          </h1>
          <p className="text-text-muted text-[11px] mt-1">
            Real spot market quotes from Binance Public Data Engine with algorithmic trend alignment.
          </p>
        </div>
        <div className="text-[10px] text-text-faint px-2 py-1 bg-surface border border-border">
          FEED: BINANCE SPOT REST + WS (UTC-0)
        </div>
      </div>

      {/* Markets Table */}
      <div className="bg-surface border border-border overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-border bg-surface-lowest text-text-faint uppercase text-[10px]">
              <th className="py-2.5 px-4">Asset Pair</th>
              <th className="py-2.5 px-4 text-right">Spot Price</th>
              <th className="py-2.5 px-4 text-right">24H Delta</th>
              <th className="py-2.5 px-4 text-right">24H Volume</th>
              <th className="py-2.5 px-4 text-center">4H Trend Bias</th>
              <th className="py-2.5 px-4">Kronos Forecast Status</th>
              <th className="py-2.5 px-4 text-center">Action</th>
            </tr>
          </thead>
          <tbody>
            {defaultMarkets.map((m) => {
              const isActive = activeSymbol === m.symbol;
              const isUp = m.change24h >= 0;
              return (
                <tr
                  key={m.symbol}
                  className={`border-b border-border/40 hover:bg-surface-high transition-colors ${
                    isActive ? 'bg-surface-mid' : ''
                  }`}
                >
                  <td className="py-3 px-4">
                    <div className="flex flex-col">
                      <span className="font-bold text-text-prominent text-sm flex items-center gap-1.5">
                        {m.symbol.replace('USDT', '/USDT')}
                        {isActive && (
                          <span className="px-1 py-0 text-[9px] bg-primary/20 text-primary border border-primary/40 font-bold">
                            ACTIVE
                          </span>
                        )}
                      </span>
                      <span className="text-[10px] text-text-muted">{m.name}</span>
                    </div>
                  </td>

                  <td className="py-3 px-4 text-right font-bold text-text-prominent text-sm">
                    ${m.basePrice.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>

                  <td className="py-3 px-4 text-right">
                    <span
                      className={`inline-flex items-center gap-0.5 font-bold ${
                        isUp ? 'text-bull' : 'text-bear'
                      }`}
                    >
                      {isUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
                      {isUp ? '+' : ''}{m.change24h.toFixed(2)}%
                    </span>
                  </td>

                  <td className="py-3 px-4 text-right text-text-standard">{m.vol24h}</td>

                  <td className="py-3 px-4 text-center">
                    <span
                      className={`px-2 py-0.5 text-[10px] font-bold ${
                        m.trend.includes('BULL')
                          ? 'bg-bull/15 text-bull border border-bull/30'
                          : m.trend.includes('BEAR')
                          ? 'bg-bear/15 text-bear border border-bear/30'
                          : 'bg-surface-high text-text-muted border border-border'
                      }`}
                    >
                      {m.trend}
                    </span>
                  </td>

                  <td className="py-3 px-4 text-text-prominent">
                    <span className="text-primary font-semibold">{m.forecastStance}</span>
                  </td>

                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => onSelectSymbol(m.symbol)}
                      disabled={isActive}
                      className={`px-3 py-1 text-[11px] font-bold uppercase transition-none border flex items-center gap-1 mx-auto ${
                        isActive
                          ? 'bg-surface-lowest text-text-faint border-border cursor-default'
                          : 'bg-primary hover:bg-primary-glow text-background border-primary'
                      }`}
                    >
                      {isActive ? (
                        <>
                          <CheckCircle2 size={12} />
                          <span>LOADED</span>
                        </>
                      ) : (
                        <>
                          <span>ANALYZE</span>
                          <ArrowRight size={12} />
                        </>
                      )}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

