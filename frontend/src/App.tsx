import React, { useState, useEffect, useCallback } from 'react';
import { SidebarNav } from './components/SidebarNav';
import { HeaderToolbar } from './components/HeaderToolbar';
import { OverviewPage } from './pages/OverviewPage';
import { MarketsPage } from './pages/MarketsPage';
import { ForecastLabPage } from './pages/ForecastLabPage';
import { PatternScannerPage } from './pages/PatternScannerPage';
import { BacktestingPage } from './pages/BacktestingPage';
import { PaperJournalPage } from './pages/PaperJournalPage';
import { ModelHealthPage } from './pages/ModelHealthPage';
import { DataHealthPage } from './pages/DataHealthPage';
import { SettingsPage } from './pages/SettingsPage';

import {
  fetchCandles,
  fetchIndicators,
  fetchMarketStructure,
  fetchPatterns,
  fetchAnalysis,
  fetchDataHealth,
  fetchModelHealth,
  fetchPaperJournal,
  generateForecast,
  createPaperSignal,
  liveStream,
} from './services/api';

import {
  Candle,
  IndicatorSeriesItem,
  SRZone,
  ForecastResult,
  AnalysisThesis,
  MarketStructure,
  DetectedPattern,
  DataHealth,
  ModelHealth,
  PaperRecord,
} from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [selectedSymbol, setSelectedSymbol] = useState<string>('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState<string>('4h');

  // Core Data State
  const [candles, setCandles] = useState<Candle[]>([]);
  const [indicators, setIndicators] = useState<IndicatorSeriesItem[]>([]);
  const [srZones, setSrZones] = useState<SRZone[]>([]);
  const [marketStructure, setMarketStructure] = useState<MarketStructure | null>(null);
  const [patterns, setPatterns] = useState<DetectedPattern[]>([]);
  const [analysis, setAnalysis] = useState<AnalysisThesis | null>(null);
  const [forecast, setForecast] = useState<ForecastResult | null>(null);
  const [dataHealth, setDataHealth] = useState<DataHealth | null>(null);
  const [modelHealth, setModelHealth] = useState<ModelHealth | null>(null);
  const [paperRecords, setPaperRecords] = useState<PaperRecord[]>([]);

  // Real-time telemetry
  const [currentPrice, setCurrentPrice] = useState<number>(0);
  const [priceDeltaPct, setPriceDeltaPct] = useState<number>(0);
  const [freshnessMs, setFreshnessMs] = useState<number>(42);
  const [isGeneratingForecast, setIsGeneratingForecast] = useState<boolean>(false);

  // Indicators visibility
  const [indicatorsVisible, setIndicatorsVisible] = useState({
    ema: true,
    vol: true,
    sr: true,
    cone: true,
  });

  const toggleIndicator = (key: 'ema' | 'vol' | 'sr' | 'cone') => {
    setIndicatorsVisible((prev) => ({ ...prev, [key]: !prev [key] }));
  };

  // Load all data for active symbol and timeframe
  const loadMarketData = useCallback(async () => {
    try {
      const [candleRes, indRes, structRes, patRes, analRes, dHealth, mHealth, paperRes] =
        await Promise.all([
          fetchCandles(selectedSymbol, selectedTimeframe, 200),
          fetchIndicators(selectedSymbol, selectedTimeframe),
          fetchMarketStructure(selectedSymbol, selectedTimeframe),
          fetchPatterns(selectedSymbol, selectedTimeframe),
          fetchAnalysis(selectedSymbol, selectedTimeframe, '3d'),
          fetchDataHealth(selectedSymbol, selectedTimeframe),
          fetchModelHealth(),
          fetchPaperJournal(),
        ]);

      if (candleRes.candles.length > 0) {
        setCandles(candleRes.candles);
        const latest = candleRes.candles[candleRes.candles.length - 1];
        const prev = candleRes.candles[0];
        setCurrentPrice(latest.close);
        const delta = ((latest.close - prev.open) / prev.open) * 100.0;
        setPriceDeltaPct(delta);
      }

      setIndicators(indRes.series || []);
      setMarketStructure(structRes);
      setSrZones(structRes.support_resistance || []);
      setPatterns(patRes.patterns || []);
      setAnalysis(analRes);
      setDataHealth(dHealth);
      setModelHealth(mHealth);
      setPaperRecords(paperRes.records || []);
      setFreshnessMs(dHealth.freshness_ms || 42);
    } catch (e) {
      console.error('Failed to load market data:', e);
    }
  }, [selectedSymbol, selectedTimeframe]);

  // Initial load
  useEffect(() => {
    loadMarketData();
  }, [loadMarketData]);

  // Connect live WebSocket stream
  useEffect(() => {
    liveStream.connect();
    const unsubscribe = liveStream.subscribe((candleTick: Candle) => {
      if (candleTick.symbol === selectedSymbol && candleTick.timeframe === selectedTimeframe) {
        setCurrentPrice(candleTick.close);
        setCandles((prev) => {
          if (!prev.length) return [candleTick];
          const last = prev[prev.length - 1];
          if (last.open_time === candleTick.open_time) {
            // Update current bar in place
            return [...prev.slice(0, -1), candleTick];
          } else if (candleTick.open_time > last.open_time) {
            // New bar confirmed
            return [...prev, candleTick];
          }
          return prev;
        });
      }
    });

    return () => {
      unsubscribe();
      liveStream.disconnect();
    };
  }, [selectedSymbol, selectedTimeframe]);

  // Trigger Forecast
  const handleRunForecast = async () => {
    setIsGeneratingForecast(true);
    try {
      const res = await generateForecast(
        selectedSymbol,
        selectedTimeframe,
        '3d',
        modelHealth?.active_model || 'NeoQuasar/Kronos-mini',
        5
      );
      setForecast(res);
      // Refresh thesis analysis with new forecast
      const anal = await fetchAnalysis(selectedSymbol, selectedTimeframe, '3d');
      setAnalysis(anal);
      const mHealth = await fetchModelHealth();
      setModelHealth(mHealth);
    } catch (e) {
      console.error('Forecast failed:', e);
    } finally {
      setIsGeneratingForecast(false);
    }
  };

  // Log Paper Signal
  const handleLogPaperTrade = async (stance: string, target: number, stopLoss: number) => {
    try {
      await createPaperSignal({
        symbol: selectedSymbol,
        timeframe: selectedTimeframe,
        stance,
        entry_price: currentPrice,
        target_price: target,
        stop_loss: stopLoss,
        horizon_hours: 72,
        forecast_id: forecast?.id,
        notes: `Signal logged from ${stance} thesis on ${selectedSymbol} ${selectedTimeframe}`,
      });
      const paperRes = await fetchPaperJournal();
      setPaperRecords(paperRes.records || []);
    } catch (e) {
      console.error('Failed to log paper trade:', e);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-text-prominent select-none font-sans">
      {/* Persistent Left Navigation */}
      <SidebarNav
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        modelHealth={modelHealth}
        onDeployModel={handleRunForecast}
      />

      {/* Main Terminal Frame */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Telemetry & Status Toolbar */}
        <HeaderToolbar
          selectedSymbol={selectedSymbol}
          onSelectSymbol={setSelectedSymbol}
          selectedTimeframe={selectedTimeframe}
          onSelectTimeframe={setSelectedTimeframe}
          currentPrice={currentPrice}
          priceDeltaPct={priceDeltaPct}
          isLive={true}
          freshnessMs={freshnessMs}
          modelHealth={modelHealth}
          indicatorsVisible={indicatorsVisible}
          onToggleIndicator={toggleIndicator}
          onRefresh={loadMarketData}
          onRunForecast={handleRunForecast}
          isGeneratingForecast={isGeneratingForecast}
        />

        {/* Viewport Router */}
        <div className="flex-1 min-h-0 overflow-hidden">
          {currentTab === 'overview' && (
            <OverviewPage
              candles={candles}
              indicators={indicators}
              srZones={srZones}
              forecast={forecast}
              analysis={analysis}
              structure={marketStructure}
              paperRecords={paperRecords}
              activeSymbol={selectedSymbol}
              currentPrice={currentPrice}
              indicatorsVisible={indicatorsVisible}
              onLogPaperTrade={handleLogPaperTrade}
            />
          )}

          {currentTab === 'markets' && (
            <MarketsPage
              activeSymbol={selectedSymbol}
              onSelectSymbol={(s) => {
                setSelectedSymbol(s);
                setCurrentTab('overview');
              }}
              currentPrices={{
                [selectedSymbol]: {
                  price: currentPrice,
                  change24h: priceDeltaPct,
                  volume24h: '$28.4B',
                  trend: marketStructure?.trend || 'BULLISH',
                },
              }}
              structure={marketStructure}
            />
          )}

          {currentTab === 'forecast-lab' && (
            <ForecastLabPage
              activeSymbol={selectedSymbol}
              activeTimeframe={selectedTimeframe}
              modelHealth={modelHealth}
              onForecastGenerated={(res) => setForecast(res)}
            />
          )}

          {currentTab === 'patterns' && (
            <PatternScannerPage
              patterns={patterns}
              activeSymbol={selectedSymbol}
            />
          )}

          {currentTab === 'backtesting' && (
            <BacktestingPage
              activeSymbol={selectedSymbol}
              activeTimeframe={selectedTimeframe}
            />
          )}

          {currentTab === 'paper-journal' && (
            <PaperJournalPage records={paperRecords} />
          )}

          {currentTab === 'model-health' && (
            <ModelHealthPage
              health={modelHealth}
              onRefresh={async () => {
                const mh = await fetchModelHealth();
                setModelHealth(mh);
              }}
            />
          )}

          {currentTab === 'data-health' && (
            <DataHealthPage
              health={dataHealth}
              activeSymbol={selectedSymbol}
              activeTimeframe={selectedTimeframe}
              onRefresh={loadMarketData}
            />
          )}

          {currentTab === 'settings' && <SettingsPage />}
        </div>
      </div>
    </div>
  );
};
