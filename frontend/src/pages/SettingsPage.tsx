import React from 'react';
import { Settings as SettingsIcon, ShieldCheck, Cpu, HardDrive, RefreshCw } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  return (
    <div className="flex-1 bg-surface-lowest p-6 flex flex-col font-mono text-xs overflow-y-auto">
      {/* Header */}
      <div className="mb-6 border-b border-border pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold text-text-prominent tracking-wider flex items-center gap-2">
            <span className="w-2.5 h-2.5 bg-primary"></span>
            SYSTEM CONFIGURATION & VERSION MANAGEMENT
          </h1>
          <p className="text-text-muted text-[11px] mt-1">
            Environment settings, model registry pins, and quantitative research safeguards.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Pinned Upstream Specifications */}
        <div className="bg-surface border border-border p-4 flex flex-col gap-3">
          <h3 className="font-bold text-xs text-text-prominent uppercase tracking-wider border-b border-border pb-2 flex items-center gap-1.5">
            <Cpu size={13} className="text-primary" /> PINNED KRONOS ARCHITECTURE
          </h3>
          <div className="flex flex-col gap-2 text-[11px]">
            <div className="flex justify-between">
              <span className="text-text-muted">Upstream Git Commit:</span>
              <span className="text-primary font-mono font-bold">67b630e67f6a18c9e9be918d9b4337c960db1e9a</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Primary Checkpoint:</span>
              <span className="text-text-prominent">NeoQuasar/Kronos-mini (f4e6869)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Primary Tokenizer:</span>
              <span className="text-text-prominent">NeoQuasar/Kronos-Tokenizer-2k (26966d0)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Comparison Checkpoint:</span>
              <span className="text-text-prominent">NeoQuasar/Kronos-base (2b55474)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Comparison Tokenizer:</span>
              <span className="text-text-prominent">NeoQuasar/Kronos-Tokenizer-base (0e01173)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Auto-Update Policy:</span>
              <span className="text-bull font-bold">MANUAL ONLY (Explicit Audit Required)</span>
            </div>
          </div>
        </div>

        {/* Paper Research Safeguards */}
        <div className="bg-surface border border-border p-4 flex flex-col gap-3">
          <h3 className="font-bold text-xs text-text-prominent uppercase tracking-wider border-b border-border pb-2 flex items-center gap-1.5">
            <ShieldCheck size={13} className="text-bull" /> PAPER RESEARCH SAFEGUARDS
          </h3>
          <div className="flex flex-col gap-2 text-[11px]">
            <div className="flex justify-between">
              <span className="text-text-muted">System Operating Mode:</span>
              <span className="text-bull font-bold">READ-ONLY & PAPER RESEARCH</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Brokerage Transactions:</span>
              <span className="text-bear font-bold">DISABLED (No API Keys / No Wallets)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Maker/Taker Assumed Fee:</span>
              <span className="text-text-prominent font-bold">0.05% (5 bps each way)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Assumed Market Slippage:</span>
              <span className="text-text-prominent font-bold">0.05% (5 bps each way)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Local Database:</span>
              <span className="text-text-prominent font-mono">./data/apex.db (SQLite)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-text-muted">Weights Cache Directory:</span>
              <span className="text-text-prominent font-mono">./models_cache/</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
