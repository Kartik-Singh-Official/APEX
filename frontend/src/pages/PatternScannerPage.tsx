import React, { useState } from 'react';
import { Radar, Filter, CheckCircle2, Clock, Search } from 'lucide-react';
import { DetectedPattern } from '../types';

interface PatternScannerPageProps {
  patterns: DetectedPattern[];
  activeSymbol: string;
}

export const PatternScannerPage: React.FC<PatternScannerPageProps> = ({
  patterns,
  activeSymbol,
}) => {
  const [filterStance, setFilterStance] = useState<string>('ALL');
  const [filterCategory, setFilterCategory] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const filtered = patterns.filter((p) => {
    if (filterStance !== 'ALL' && p.stance !== filterStance) return false;
    if (filterCategory !== 'ALL' && p.pattern_category !== filterCategory) return false;
    if (searchTerm && !p.pattern_name.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="flex-1 bg-surface-lowest p-6 flex flex-col font-mono text-xs overflow-y-auto">
      {/* Header */}
      <div className="mb-6 border-b border-border pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold text-text-prominent tracking-wider flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-primary"></span>
            PATTERN SCANNER & FORMATION DETECTOR
          </h1>
          <p className="text-text-muted text-[11px] mt-1">
            Algorithmic detection of Japanese candlestick setups and structural chart formations without lookahead bias.
          </p>
        </div>
        <div className="text-[10px] text-text-faint px-2 py-1 bg-surface border border-border">
          ASSET: {activeSymbol} • DETECTIONS: {patterns.length}
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center gap-3 mb-4 bg-surface p-2.5 border border-border">
        {/* Search */}
        <div className="flex items-center gap-1.5 bg-surface-lowest border border-border px-2 py-1">
          <Search size={13} className="text-text-muted" />
          <input
            type="text"
            placeholder="Search pattern name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-transparent text-text-prominent placeholder-text-faint outline-none text-[11px] w-44"
          />
        </div>

        {/* Stance Filter */}
        <div className="flex items-center gap-1">
          <span className="text-text-muted text-[10px]">Stance:</span>
          {['ALL', 'BULLISH', 'BEARISH', 'NEUTRAL'].map((s) => (
            <button
              key={s}
              onClick={() => setFilterStance(s)}
              className={`px-2 py-0.5 text-[10px] border font-semibold ${
                filterStance === s
                  ? 'bg-primary/10 border-primary text-primary'
                  : 'border-border text-text-muted hover:text-text-prominent'
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* Category Filter */}
        <div className="flex items-center gap-1">
          <span className="text-text-muted text-[10px]">Type:</span>
          {['ALL', 'CANDLESTICK', 'CHART_FORMATION'].map((cat) => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-2 py-0.5 text-[10px] border font-semibold ${
                filterCategory === cat
                  ? 'bg-primary/10 border-primary text-primary'
                  : 'border-border text-text-muted hover:text-text-prominent'
              }`}
            >
              {cat.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Pattern Table */}
      <div className="bg-surface border border-border overflow-hidden">
        {filtered.length === 0 ? (
          <div className="text-center py-10 text-text-faint">
            No patterns match the active filters for {activeSymbol}.
          </div>
        ) : (
          <table className="w-full text-left border-collapse text-[11px]">
            <thead>
              <tr className="border-b border-border bg-surface-lowest text-text-faint uppercase text-[10px]">
                <th className="py-2.5 px-3">Pattern Name</th>
                <th className="py-2.5 px-3">Category</th>
                <th className="py-2.5 px-3 text-center">Bias</th>
                <th className="py-2.5 px-3">Confirmed At (UTC)</th>
                <th className="py-2.5 px-3">Trigger / Invalidation</th>
                <th className="py-2.5 px-3 text-center">Quality Score</th>
                <th className="py-2.5 px-3 text-center">Status</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => {
                const isBull = p.stance === 'BULLISH';
                const isBear = p.stance === 'BEARISH';
                const dateStr = new Date(p.confirmation_time).toUTCString().replace(' GMT', '');
                const levelsStr = Object.entries(p.price_levels)
                  .map(([k, v]) => `${k.replace('_', ' ')}: $${v.toLocaleString()}`)
                  .join(' • ');

                return (
                  <tr key={p.id} className="border-b border-border/40 hover:bg-surface-high transition-colors">
                    <td className="py-2.5 px-3 font-bold text-text-prominent">
                      {p.pattern_name}
                    </td>

                    <td className="py-2.5 px-3 text-text-muted">
                      {p.pattern_category.replace('_', ' ')}
                    </td>

                    <td className="py-2.5 px-3 text-center">
                      <span
                        className={`px-1.5 py-0.2 text-[10px] font-bold ${
                          isBull
                            ? 'bg-bull/15 text-bull border border-bull/30'
                            : isBear
                            ? 'bg-bear/15 text-bear border border-bear/30'
                            : 'bg-surface-high text-text-muted border border-border'
                        }`}
                      >
                        {p.stance}
                      </span>
                    </td>

                    <td className="py-2.5 px-3 text-text-standard">{dateStr}</td>

                    <td className="py-2.5 px-3 text-text-standard text-[10px]">{levelsStr}</td>

                    <td className="py-2.5 px-3 text-center font-bold text-primary">
                      {(p.quality_score * 100).toFixed(0)}%
                    </td>

                    <td className="py-2.5 px-3 text-center">
                      <span className="inline-flex items-center gap-1 text-[10px] px-1.5 py-0.2 bg-bull/15 text-bull border border-bull/40">
                        <CheckCircle2 size={11} />
                        CONFIRMED
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
