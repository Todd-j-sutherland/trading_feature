import { BankSymbol } from '../types/trading.types';

export const ASX_BANKS: BankSymbol[] = [
  { code: 'CBA.AX', name: 'Commonwealth Bank', sector: 'Major Bank' },
  { code: 'ANZ.AX', name: 'ANZ Banking Group', sector: 'Major Bank' },
  { code: 'WBC.AX', name: 'Westpac Banking', sector: 'Major Bank' },
  { code: 'NAB.AX', name: 'National Australia Bank', sector: 'Major Bank' },
  { code: 'MQG.AX', name: 'Macquarie Group', sector: 'Investment Bank' },
  { code: 'SUN.AX', name: 'Suncorp Group', sector: 'Regional Bank' },
  { code: 'QBE.AX', name: 'QBE Insurance', sector: 'Insurance' },
];

export const TIMEFRAMES = [
  { label: '1H', value: '1H' },
  { label: '1D', value: '1D' },
  { label: '1W', value: '1W' },
  { label: '1M', value: '1M' },
];

export const CHART_COLORS = {
  background: '#1a1a1a',
  grid: '#2a2a2a',
  text: '#d1d4dc',
  buySignal: '#00ff88',
  sellSignal: '#ff0088',
  holdSignal: '#ffa500',
  sentiment: '#00ff88',
  confidence: '#4a9eff',
  upCandle: '#00C851',
  downCandle: '#FF4444',
};

// Environment-based API configuration
const getApiBaseUrl = () => {
  // Always use backend port 8000 for API calls
  return 'http://localhost:8000/api';
};

const getMLApiBaseUrl = () => {
  // Always use backend port 8001 for ML API calls
  return 'http://localhost:8001';
};

const getWebSocketUrl = (port: number) => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `ws://localhost:${port}`;
    } else {
      return `ws://${hostname}:${port}`;
    }
  }
  return `ws://localhost:${port}`;
};

export const API_BASE_URL = getApiBaseUrl();
export const ML_API_BASE_URL = getMLApiBaseUrl();
export const WS_BASE_URL_8000 = getWebSocketUrl(8000);
export const WS_BASE_URL_8001 = getWebSocketUrl(8001);
