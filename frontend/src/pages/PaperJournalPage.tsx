import React from 'react';
import { BookOpen, CheckCircle2, XCircle, Clock, ShieldAlert } from 'lucide-react';
import { PaperRecord } from '../types';

interface PaperJournalPageProps {
  records: PaperRecord[];
}

export const PaperJournalPage: React.FC<PaperJournalPageProps> = ({ records }) => {
  const winCount = records.filter((r) => r.status === 'WIN').length;
  const lossCount = records.filter((r) => r.status === 'LOSS').length;
  const closedCount = winCount + lossCount;
  const winRate = closedCount > 0 ? (winCount / closedCount) * 100 : 0;

  const totalNetPnL = records
    .filter((r) => r.net_pnl_pct !== null && r.net_pnl_pct !== undefined)
    .reduce((acc, r) => acc + (r.net_pnl_pct || 0), 0);

  return (
    <div className="flex-1 bg-surface-lowest p-6 flex flex-col font-mono text-xs overflow-y-auto">
      {/* Header */}
      <div className="mb-6 border-b border-border pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold text-text-prominent tracking-wider flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-primary"></span>
            PAPER RESEARCH JOURNAL & EXECUTION LEDGER
          </h1>
          <p className="text-text-muted text-[11px] mt-1">
            Read-only paper research tracking hypothetical trades with strictly deducted fee (0.05% maker/taker) and slippage (0.05%) assumptions.
          </p>
        </div>
        <div className="text-[10px] text-amber border border-amber/40 bg-amber/10 px-2 py-1 flex items-center gap-1">
          <ShieldAlert size={12} />
          <span>READ-ONLY • ZERO BROKERAGE TRANSACTIONS</span>
        </div>
      </div>

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <div className="p-3 bg-surface border border-border">
          <span className="text-[10px] text-text-muted">TOTAL PAPER SIGNALS</span>
          <div className="text-xl font-bold text-text-prominent mt-1">{records.length}</div>
          <span className="text-[10px] text-text-faint">Active & Settled</span>
        </div>

        <div className="p-3 bg-surface border border-border">
          <span className="text-[10px] text-text-muted">PAPER WIN RATE</span>
          <div className="text-xl font-bold text-bull mt-1">{winRate.toFixed(1)}%</div>
          <span className="text-[10px] text-text-faint">
            {winCount} Wins / {lossCount} Losses
          </span>
        </div>

        <div className="p-3 bg-surface border border-border">
          <span className="text-[10px] text-text-muted">CUMULATIVE NET PNL</span>
          <div className={`text-xl font-bold mt-1 ${totalNetPnL >= 0 ? 'text-bull' : 'text-bear'}`}>
            {totalNetPnL >= 0 ? '+' : ''}{totalNetPnL.toFixed(2)}%
          </div>
          <span className="text-[10px] text-text-faint">Net of 10 bps total drag</span>
        </div>

        <div className="p-3 bg-surface border border-border">
          <span className="text-[10px] text-text-muted">COST ASSUMPTIONS</span>
          <div className="text-xs font-bold text-text-prominent mt-1">0.05% Fee + 0.05% Slip</div>
          <span className="text-[10px] text-text-faint">Round-trip drag: -0.20%</span>
        </div>
      </div>

      {/* Journal Table */}
      <div className="bg-surface border border-border overflow-hidden">
        {records.length === 0 ? (
          <div className="text-center py-12 text-text-faint">
            No paper positions recorded yet. Click 'LOG PAPER TRADE IN JOURNAL' on the Overview screen to test a quantitative hypothesis.
          </div>
        ) : (
          <table className="w-full text-left border-collapse text-[11px]">
            <thead>
              <tr className="border-b border-border bg-surface-lowest text-text-faint uppercase text-[10px]">
                <th className="py-2.5 px-3">Signal ID</th>
                <th className="py-2.5 px-3">Timestamp (UTC)</th>
                <th className="py-2.5 px-3">Pair / TF</th>
                <th className="py-2.5 px-3">Stance</th>
                <th className="py-2.5 px-3 text-right">Entry Price</th>
                <th className="py-2.5 px-3 text-right">Target Price</th>
                <th className="py-2.5 px-3 text-right">Stop Loss</th>
                <th className="py-2.5 px-3 text-right">Exit Price</th>
                <th className="py-2.5 px-3 text-center">Status</th>
                <th className="py-2.5 px-3 text-right">Net PnL %</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => {
                const isWin = r.status === 'WIN';
                const isLoss = r.status === 'LOSS';
                const isOpen = r.status === 'OPEN';
                return (
                  <tr key={r.id} className="border-b border-border/40 hover:bg-surface-high">
                    <td className="py-2.5 px-3 text-text-muted font-mono">{r.id}</td>
                    <td className="py-2.5 px-3 text-text-standard">
                      {new Date(r.entry_time).toUTCString().replace(' GMT', '')}
                    </td>
                    <td className="py-2.5 px-3 font-bold text-text-prominent">
                      {r.symbol} <span className="text-primary font-normal">[{r.timeframe}]</span>
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`px-1.5 py-0.2 text-[10px] font-bold ${
                          r.stance.includes('BULL')
                            ? 'bg-bull/15 text-bull'
                            : r.stance.includes('BEAR')
                            ? 'bg-bear/15 text-bear'
                            : 'bg-surface-high text-text-muted'
                        }`}
                      >
                        {r.stance}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-right text-text-prominent">${r.entry_price.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-right text-primary font-semibold">${r.target_price.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-right text-bear">${r.stop_loss.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-right text-text-standard">
                      {r.exit_price ? `$${r.exit_price.toLocaleString()}` : '---'}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span
                        className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 font-bold ${
                          isWin
                            ? 'bg-bull/20 text-bull border border-bull/40'
                            : isLoss
                            ? 'bg-bear/20 text-bear border border-bear/40'
                            : 'bg-surface-high text-text-muted'
                        }`}
                      >
                        {isWin && <CheckCircle2 size={11} />}
                        {isLoss && <XCircle size={11} />}
                        {isOpen && <Clock size={11} />}
                        {r.status}
                      </span>
                    </td>
                    <td
                      className={`py-2.5 px-3 text-right font-bold ${
                        r.net_pnl_pct && r.net_pnl_pct >= 0 ? 'text-bull' : 'text-bear'
                      }`}
                    >
                      {r.net_pnl_pct !== null && r.net_pnl_pct !== undefined
                        ? `${r.net_pnl_pct >= 0 ? '+' : ''}${r.net_pnl_pct.toFixed(2)}%`
                        : '---'}
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

