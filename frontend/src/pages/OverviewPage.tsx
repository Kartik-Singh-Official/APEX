import React from 'react';
import { CandleChart } from '../charts/CandleChart';
import { RightAnalysisPanel } from '../components/RightAnalysisPanel';
import { BottomMultiPane } from '../components/BottomMultiPane';
import {
  Candle,
  IndicatorSeriesItem,
  SRZone,
  ForecastResult,
  AnalysisThesis,
  MarketStructure,
  PaperRecord,
} from '../types';

interface OverviewPageProps {
  candles: Candle[];
  indicators: IndicatorSeriesItem[];
  srZones: SRZone[];
  forecast: ForecastResult | null;
  analysis: AnalysisThesis | null;
  structure: MarketStructure | null;
  paperRecords: PaperRecord[];
  activeSymbol: string;
  currentPrice: number;
  indicatorsVisible: {
    ema: boolean;
    vol: boolean;
    sr: boolean;
    cone: boolean;
  };
  onLogPaperTrade: (stance: string, target: number, stopLoss: number) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  candles,
  indicators,
  srZones,
  forecast,
  analysis,
  structure,
  paperRecords,
  activeSymbol,
  currentPrice,
  indicatorsVisible,
  onLogPaperTrade,
}) => {
  return (
    <div className="flex-1 flex flex-col overflow-hidden min-w-0 bg-surface-lowest h-full">
      {/* Upper split: Main Candlestick Chart & Right Quantitative Sidebar */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        <CandleChart
          candles={candles}
          indicators={indicators}
          srZones={srZones}
          forecast={forecast}
          indicatorsVisible={indicatorsVisible}
        />
        <RightAnalysisPanel
          analysis={analysis}
          forecast={forecast}
          currentPrice={currentPrice}
          onLogPaperTrade={onLogPaperTrade}
        />
      </div>

      {/* Bottom Multi-Timeframe Regime & Ledger */}
      <BottomMultiPane
        structure={structure}
        paperRecords={paperRecords}
        activeSymbol={activeSymbol}
      />
    </div>
  );
};

