import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, UTCTimestamp, ColorType, LineStyle } from 'lightweight-charts';
import { Candle, IndicatorSeriesItem, SRZone, PredictedCandle, ForecastResult } from '../types';

interface CandleChartProps {
  candles: Candle[];
  indicators: IndicatorSeriesItem[];
  srZones: SRZone[];
  forecast: ForecastResult | null;
  indicatorsVisible: {
    ema: boolean;
    vol: boolean;
    sr: boolean;
    cone: boolean;
  };
}

export const CandleChart: React.FC<CandleChartProps> = ({
  candles,
  indicators,
  srZones,
  forecast,
  indicatorsVisible,
}) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const volumeSeriesRef = useRef<ISeriesApi<'Histogram'> | null>(null);
  const ema20SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema50SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const ema200SeriesRef = useRef<ISeriesApi<'Line'> | null>(null);
  const forecastSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const forecastMedianLineRef = useRef<ISeriesApi<'Line'> | null>(null);
  const forecast95UpperRef = useRef<ISeriesApi<'Line'> | null>(null);
  const forecast95LowerRef = useRef<ISeriesApi<'Line'> | null>(null);

  const priceLinesRef = useRef<any[]>([]);

  const [hoverData, setHoverData] = useState<{
    time?: string;
    open?: number;
    high?: number;
    low?: number;
    close?: number;
    volume?: number;
  }>({});

  // Initialize Lightweight Chart
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0B0F14' },
        textColor: '#869397',
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: '#161F2A' },
        horzLines: { color: '#161F2A' },
      },
      crosshair: {
        vertLine: {
          color: '#06B6D4',
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: '#111820',
        },
        horzLine: {
          color: '#06B6D4',
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: '#111820',
        },
      },
      rightPriceScale: {
        borderColor: '#1F2937',
        textColor: '#9CA3AF',
        scaleMargins: {
          top: 0.1,
          bottom: 0.25,
        },
      },
      timeScale: {
        borderColor: '#1F2937',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // Volume Series (base pane)
    const volumeSeries = chart.addHistogramSeries({
      priceFormat: { type: 'volume' },
      priceScaleId: '', // overlay
    });
    chart.priceScale('').applyOptions({
      scaleMargins: {
        top: 0.78,
        bottom: 0.0,
      },
    });
    volumeSeriesRef.current = volumeSeries;

    // Main Historical Candlestick Series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10B981',
      downColor: '#EF4444',
      borderVisible: true,
      borderUpColor: '#10B981',
      borderDownColor: '#EF4444',
      wickUpColor: '#10B981',
      wickDownColor: '#EF4444',
    });
    candleSeriesRef.current = candleSeries;

    // EMA Overlays
    const ema20 = chart.addLineSeries({
      color: '#06B6D4',
      lineWidth: 1,
      priceLineVisible: false,
      title: 'EMA 20',
    });
    ema20SeriesRef.current = ema20;

    const ema50 = chart.addLineSeries({
      color: '#F59E0B',
      lineWidth: 1,
      priceLineVisible: false,
      title: 'EMA 50',
    });
    ema50SeriesRef.current = ema50;

    const ema200 = chart.addLineSeries({
      color: '#869397',
      lineWidth: 1,
      priceLineVisible: false,
      title: 'EMA 200',
    });
    ema200SeriesRef.current = ema200;

    // Forecast Series: Translucent Phantom Future Candles
    const forecastSeries = chart.addCandlestickSeries({
      upColor: 'rgba(6, 182, 212, 0.45)',
      downColor: 'rgba(6, 182, 212, 0.25)',
      borderVisible: true,
      borderUpColor: '#06B6D4',
      borderDownColor: '#06B6D4',
      wickUpColor: '#4CD7F6',
      wickDownColor: '#4CD7F6',
      priceLineVisible: false,
    });
    forecastSeriesRef.current = forecastSeries;

    // Forecast Median Path Line
    const forecastMedian = chart.addLineSeries({
      color: '#4CD7F6',
      lineWidth: 2,
      lineStyle: LineStyle.Solid,
      priceLineVisible: true,
      title: 'Median Path',
    });
    forecastMedianLineRef.current = forecastMedian;

    // Forecast 95% Confidence Bounds
    const f95U = chart.addLineSeries({
      color: 'rgba(6, 182, 212, 0.6)',
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      priceLineVisible: false,
      title: '95% Upper',
    });
    forecast95UpperRef.current = f95U;

    const f95L = chart.addLineSeries({
      color: 'rgba(6, 182, 212, 0.6)',
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      priceLineVisible: false,
      title: '95% Lower',
    });
    forecast95LowerRef.current = f95L;

    // Tooltip Tracker
    chart.subscribeCrosshairMove((param) => {
      if (!param.time || !param.seriesData) {
        setHoverData({});
        return;
      }
      const data = param.seriesData.get(candleSeries) as any;
      if (data) {
        setHoverData({
          time: new Date((param.time as number) * 1000).toUTCString(),
          open: data.open,
          high: data.high,
          low: data.low,
          close: data.close,
        });
      }
    });

    // Resize Observer
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // Update Data & Indicators
  useEffect(() => {
    if (!chartRef.current || !candleSeriesRef.current || !candles.length) return;

    // Candlesticks
    const candleData = candles.map((c) => ({
      time: (c.open_time / 1000) as UTCTimestamp,
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));
    candleSeriesRef.current.setData(candleData);

    // Volume
    if (volumeSeriesRef.current && indicatorsVisible.vol) {
      const volData = candles.map((c) => ({
        time: (c.open_time / 1000) as UTCTimestamp,
        value: c.volume,
        color: c.close >= c.open ? 'rgba(16, 185, 129, 0.35)' : 'rgba(239, 68, 68, 0.35)',
      }));
      volumeSeriesRef.current.setData(volData);
    } else if (volumeSeriesRef.current) {
      volumeSeriesRef.current.setData([]);
    }

    // EMA Overlays
    if (indicatorsVisible.ema && indicators.length) {
      const validEma20 = indicators
        .filter((i) => i.ema_20 !== null)
        .map((i) => ({ time: (i.open_time / 1000) as UTCTimestamp, value: i.ema_20! }));
      const validEma50 = indicators
        .filter((i) => i.ema_50 !== null)
        .map((i) => ({ time: (i.open_time / 1000) as UTCTimestamp, value: i.ema_50! }));
      const validEma200 = indicators
        .filter((i) => i.ema_200 !== null)
        .map((i) => ({ time: (i.open_time / 1000) as UTCTimestamp, value: i.ema_200! }));

      ema20SeriesRef.current?.setData(validEma20);
      ema50SeriesRef.current?.setData(validEma50);
      ema200SeriesRef.current?.setData(validEma200);
    } else {
      ema20SeriesRef.current?.setData([]);
      ema50SeriesRef.current?.setData([]);
      ema200SeriesRef.current?.setData([]);
    }

    // Support & Resistance Lines
    priceLinesRef.current.forEach((pl) => candleSeriesRef.current?.removePriceLine(pl));
    priceLinesRef.current = [];

    if (indicatorsVisible.sr && srZones.length) {
      srZones.forEach((z) => {
        const isRes = z.type === 'RESISTANCE';
        const pl = candleSeriesRef.current?.createPriceLine({
          price: z.level,
          color: isRes ? '#EF4444' : '#10B981',
          lineWidth: 1,
          lineStyle: LineStyle.Dotted,
          axisLabelVisible: true,
          title: `${z.type} $${z.level.toLocaleString()}`,
        });
        if (pl) priceLinesRef.current.push(pl);
      });
    }

    // Forecast Horizon & Projection
    if (forecast && forecast.predicted_candles.length && indicatorsVisible.cone) {
      const lastCandle = candles[candles.length - 1];
      const lastTime = lastCandle.open_time / 1000;

      // Predicted phantom candles
      const predCandles = forecast.predicted_candles.map((p) => ({
        time: (p.timestamp / 1000) as UTCTimestamp,
        open: p.open,
        high: p.high,
        low: p.low,
        close: p.close,
      }));
      forecastSeriesRef.current?.setData(predCandles);

      // Median Path Line (joining last real candle close to future forecast closes)
      const medianPath = [
        { time: lastTime as UTCTimestamp, value: lastCandle.close },
        ...forecast.predicted_candles.map((p) => ({
          time: (p.timestamp / 1000) as UTCTimestamp,
          value: p.close,
        })),
      ];
      forecastMedianLineRef.current?.setData(medianPath);

      // 95% Uncertainty Corridor Cones
      const fUpper = [
        { time: lastTime as UTCTimestamp, value: lastCandle.close },
        ...forecast.predicted_candles.map((p, idx) => {
          const ratio = (idx + 1) / forecast.predicted_candles.length;
          const bound = lastCandle.close + (forecast.range_95_high - lastCandle.close) * ratio;
          return { time: (p.timestamp / 1000) as UTCTimestamp, value: bound };
        }),
      ];
      const fLower = [
        { time: lastTime as UTCTimestamp, value: lastCandle.close },
        ...forecast.predicted_candles.map((p, idx) => {
          const ratio = (idx + 1) / forecast.predicted_candles.length;
          const bound = lastCandle.close + (forecast.range_95_low - lastCandle.close) * ratio;
          return { time: (p.timestamp / 1000) as UTCTimestamp, value: bound };
        }),
      ];
      forecast95UpperRef.current?.setData(fUpper);
      forecast95LowerRef.current?.setData(fLower);
    } else {
      forecastSeriesRef.current?.setData([]);
      forecastMedianLineRef.current?.setData([]);
      forecast95UpperRef.current?.setData([]);
      forecast95LowerRef.current?.setData([]);
    }
  }, [candles, indicators, srZones, forecast, indicatorsVisible]);

  const latestCandle = candles[candles.length - 1];
  const activeO = hoverData.open ?? latestCandle?.open;
  const activeH = hoverData.high ?? latestCandle?.high;
  const activeL = hoverData.low ?? latestCandle?.low;
  const activeC = hoverData.close ?? latestCandle?.close;

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-surface-lowest relative h-full">
      {/* Chart Telemetry Sub-bar */}
      <div className="h-6 px-3 bg-surface border-b border-border flex items-center justify-between font-mono text-[11px] text-text-muted shrink-0">
        <div className="flex items-center gap-3">
          <span>O: <strong className="text-text-prominent font-normal">{activeO?.toFixed(2) || '---'}</strong></span>
          <span>H: <strong className="text-bull font-normal">{activeH?.toFixed(2) || '---'}</strong></span>
          <span>L: <strong className="text-bear font-normal">{activeL?.toFixed(2) || '---'}</strong></span>
          <span>C: <strong className="text-primary font-semibold">{activeC?.toFixed(2) || '---'}</strong></span>
        </div>
        <div className="flex items-center gap-2">
          {forecast && (
            <span className="text-[10px] px-1.5 py-0 bg-primary/10 text-primary border border-primary/30 font-semibold">
              FORECAST: {forecast.expected_return_pct >= 0 ? '+' : ''}{forecast.expected_return_pct}% [{forecast.horizon_label}]
            </span>
          )}
          <span className="text-[10px] text-text-faint">GRID: LOGARITHMIC (UTC)</span>
        </div>
      </div>

      {/* Chart Canvas */}
      <div ref={chartContainerRef} className="flex-1 w-full relative" />
    </div>
  );
};
