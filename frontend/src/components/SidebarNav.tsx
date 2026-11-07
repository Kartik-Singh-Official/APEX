import React from 'react';
import {
  LayoutDashboard,
  CandlestickChart,
  LineChart,
  Radar,
  History,
  BookOpen,
  Cpu,
  Database,
  Settings as SettingsIcon,
  Zap,
  Activity,
  HardDrive,
} from 'lucide-react';
import { ModelHealth } from '../types';

interface SidebarNavProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  modelHealth: ModelHealth | null;
  onDeployModel?: () => void;
}

export const SidebarNav: React.FC<SidebarNavProps> = ({
  currentTab,
  onSelectTab,
  modelHealth,
  onDeployModel,
}) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'markets', label: 'Markets', icon: CandlestickChart },
    { id: 'forecast-lab', label: 'Forecast Lab', icon: LineChart },
    { id: 'patterns', label: 'Pattern Scanner', icon: Radar },
    { id: 'backtesting', label: 'Backtesting', icon: History },
    { id: 'paper-journal', label: 'Paper Research Journal', icon: BookOpen },
    { id: 'model-health', label: 'Model Health', icon: Cpu },
    { id: 'data-health', label: 'Data Health', icon: Database },
    { id: 'settings', label: 'Settings', icon: SettingsIcon },
  ];

  const activeModelDisplay = modelHealth?.active_model
    ? modelHealth.active_model.replace('NeoQuasar/', '')
    : 'Kronos-mini';
  const deviceDisplay = modelHealth?.device?.toUpperCase() || 'MPS';
  const latencyDisplay = modelHealth?.last_latency_ms
    ? `${modelHealth.last_latency_ms.toFixed(0)}ms`
    : '42ms';
  const memResident = modelHealth?.memory_resident_mb || 420;
  const memPct = Math.min(100, Math.round((memResident / 16384) * 100));

  return (
    <aside className="w-56 bg-surface-low border-r border-border flex flex-col justify-between shrink-0 select-none z-20 h-full">
      {/* Top Branding & Nav */}
      <div className="flex flex-col p-2 gap-1">
        {/* Brand Bar */}
        <div className="flex items-center justify-between px-2 py-1.5 border-b border-border/60 mb-2">
          <div className="flex flex-col">
            <span className="font-mono text-xs font-bold text-text-prominent tracking-wider flex items-center gap-1">
              <span className="inline-block w-2 h-2 bg-primary"></span>
              APEX TERMINAL
            </span>
            <span className="font-mono text-[9px] text-text-faint tracking-wider">
              QUANT-RESEARCH-01
            </span>
          </div>
          <span className="font-mono text-[9px] px-1 py-0.2 bg-primary/10 text-primary border border-primary/30 font-semibold">
            v4.12
          </span>
        </div>

        {/* 9 Navigation Items */}
        <nav className="flex flex-col gap-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`flex items-center gap-2.5 px-2.5 py-1.5 text-xs font-mono text-left transition-colors ${
                  isActive
                    ? 'bg-surface-high text-primary border-l-2 border-primary font-semibold'
                    : 'text-text-standard hover:bg-surface-mid hover:text-text-prominent'
                }`}
              >
                <Icon size={14} className={isActive ? 'text-primary' : 'text-text-muted'} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Quick Action */}
        <div className="mt-4 px-1">
          <button
            onClick={onDeployModel}
            className="w-full py-1.5 px-2 bg-primary hover:bg-primary-glow text-background font-mono text-[11px] font-bold tracking-wider uppercase transition-none flex items-center justify-center gap-1.5"
          >
            <Zap size={12} className="fill-current" />
            <span>RUN FORECAST</span>
          </button>
        </div>
      </div>

      {/* Hardware Telemetry Dock */}
      <div className="p-2 border-t border-border/80 bg-surface-lowest flex flex-col gap-1.5 font-mono text-[10px]">
        <div className="flex items-center justify-between text-text-muted px-1">
          <span className="flex items-center gap-1">
            <Activity size={11} className="text-bull" />
            Engine:
          </span>
          <span className="text-text-prominent font-semibold">{activeModelDisplay}</span>
        </div>

        <div className="flex items-center justify-between text-text-muted px-1">
          <span className="flex items-center gap-1">
            <Zap size={11} className="text-primary" />
            Device:
          </span>
          <span className="text-primary font-semibold">{deviceDisplay} [{latencyDisplay}]</span>
        </div>

        <div className="flex items-center justify-between text-text-muted px-1">
          <span className="flex items-center gap-1">
            <HardDrive size={11} className="text-amber" />
            RAM:
          </span>
          <span className="text-text-prominent">{(memResident / 1024).toFixed(1)} / 16.0 GB</span>
        </div>

        {/* Progress bar */}
        <div className="w-full bg-surface-high h-1 overflow-hidden mt-0.5">
          <div
            className="bg-primary h-full transition-all duration-300"
            style={{ width: `${Math.max(memPct, 8)}%` }}
          />
        </div>
      </div>
    </aside>
  );
};

