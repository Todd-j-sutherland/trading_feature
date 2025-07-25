// TypeScript types for the trading dashboard

export interface BankSymbol {
  code: string;
  name: string;
  sector: string;
}

export interface OHLCVData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MLPrediction {
  timestamp: string;
  symbol: string;
  sentimentScore: number;
  confidence: number;
  signal: 'BUY' | 'SELL' | 'HOLD';
  technicalScore: number;
  newsCount: number;
  features: {
    newsImpact: number;
    technicalScore: number;
    eventImpact: number;
    redditSentiment: number;
  };
}

export interface ChartMarker {
  time: number;
  position: 'aboveBar' | 'belowBar' | 'inBar';
  color: string;
  shape: 'circle' | 'square' | 'arrowUp' | 'arrowDown';
  text: string;
  size: number;
}

export interface MLIndicatorData {
  time: number;
  value: number;
  confidence: number;
}

export interface ConfidenceBand {
  time: number;
  upper: number;
  lower: number;
}

export interface APIResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  timestamp: string;
}
