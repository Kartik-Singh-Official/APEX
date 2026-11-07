/**
 * APEX Terminal API & WebSocket Service Layer
 */
import {
  Candle,
  IndicatorLatest,
  IndicatorSeriesItem,
  MarketStructure,
  DetectedPattern,
  AnalysisThesis,
  ForecastResult,
  DataHealth,
  ModelHealth,
  BacktestSummary,
  PaperRecord,
} from '../types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<{ status: string; version: string; device: string; is_mps_verified: boolean }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function fetchSymbols(): Promise<{
  symbols: string[];
  default_symbol: string;
  timeframes: string[];
  default_timeframe: string;
  horizons: Record<string, Record<string, number>>;
}> {
  const res = await fetch(`${API_BASE}/symbols`);
  return res.json();
}

export async function fetchCandles(symbol: string, timeframe: string, limit = 250): Promise<{ count: number; candles: Candle[] }> {
  const res = await fetch(`${API_BASE}/candles?symbol=${symbol}&timeframe=${timeframe}&limit=${limit}`);
  return res.json();
}

export async function fetchIndicators(symbol: string, timeframe: string): Promise<{
  symbol: string;
  timeframe: string;
  latest: IndicatorLatest;
  series: IndicatorSeriesItem[];
}> {
  const res = await fetch(`${API_BASE}/indicators?symbol=${symbol}&timeframe=${timeframe}`);
  return res.json();
}

export async function fetchMarketStructure(symbol: string, timeframe: string): Promise<MarketStructure> {
  const res = await fetch(`${API_BASE}/market-structure?symbol=${symbol}&timeframe=${timeframe}`);
  return res.json();
}

export async function fetchPatterns(symbol: string, timeframe: string): Promise<{ patterns: DetectedPattern[] }> {
  const res = await fetch(`${API_BASE}/patterns?symbol=${symbol}&timeframe=${timeframe}`);
  return res.json();
}

export async function fetchAnalysis(symbol: string, timeframe: string, horizon = '3d'): Promise<AnalysisThesis> {
  const res = await fetch(`${API_BASE}/analysis?symbol=${symbol}&timeframe=${timeframe}&horizon_label=${horizon}`);
  return res.json();
}

export async function generateForecast(
  symbol: string,
  timeframe: string,
  horizon = '3d',
  modelKey = 'NeoQuasar/Kronos-mini',
  sampleCount = 5
): Promise<ForecastResult> {
  const res = await fetch(`${API_BASE}/forecast/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbol,
      timeframe,
      horizon_label: horizon,
      model_key: modelKey,
      sample_count: sampleCount,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Forecast generation failed');
  }
  return res.json();
}

export async function fetchDataHealth(symbol: string, timeframe: string): Promise<DataHealth> {
  const res = await fetch(`${API_BASE}/data/health?symbol=${symbol}&timeframe=${timeframe}`);
  return res.json();
}

export async function fetchModelHealth(): Promise<ModelHealth> {
  const res = await fetch(`${API_BASE}/models/health`);
  return res.json();
}

export async function switchModel(modelKey: string): Promise<{ status: string; active_model: string; device: string }> {
  const res = await fetch(`${API_BASE}/models/switch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_key: modelKey }),
  });
  return res.json();
}

export async function runBacktest(
  symbol: string,
  timeframe: string,
  horizon = '3d',
  modelKey = 'NeoQuasar/Kronos-mini'
): Promise<BacktestSummary> {
  const res = await fetch(`${API_BASE}/backtest/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbol,
      timeframe,
      horizon_label: horizon,
      model_key: modelKey,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Backtest execution failed');
  }
  return res.json();
}

export async function fetchPaperJournal(): Promise<{ records: PaperRecord[] }> {
  const res = await fetch(`${API_BASE}/paper-journal`);
  return res.json();
}

export async function createPaperSignal(data: {
  symbol: string;
  timeframe: string;
  stance: string;
  entry_price: number;
  target_price: number;
  stop_loss: number;
  horizon_hours?: number;
  forecast_id?: string;
  notes?: string;
}): Promise<PaperRecord> {
  const res = await fetch(`${API_BASE}/paper-journal/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

/**
 * WebSocket Stream Manager for Live Ticks
 */
export class LiveStreamManager {
  private ws: WebSocket | null = null;
  private subscribers: ((candle: Candle) => void)[] = [];
  private reconnectTimer: any = null;

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/stream`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        // Send keepalive ping
        setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send('ping');
          }
        }, 15000);
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'candle_tick') {
            this.subscribers.forEach((fn) => fn(payload.data));
          }
        } catch (e) {
          // ignore keepalive pong
        }
      };

      this.ws.onclose = () => {
        this.reconnectTimer = setTimeout(() => this.connect(), 3000);
      };

      this.ws.onerror = () => {
        if (this.ws) this.ws.close();
      };
    } catch (e) {
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    }
  }

  subscribe(callback: (candle: Candle) => void) {
    this.subscribers.push(callback);
    return () => {
      this.subscribers = this.subscribers.filter((fn) => fn !== callback);
    };
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    if (this.ws) this.ws.close();
  }
}

export const liveStream = new LiveStreamManager();

