// API service for real-time ML predictions
// Connects React frontend to Python ML backend

import { ML_API_BASE_URL, WS_BASE_URL_8001 } from '../constants/trading.constants';

export interface BankPrediction {
  symbol: string;
  bank_name: string;
  sector: string;
  current_price: number;
  price_change_1d: number;
  price_change_5d: number;
  rsi: number;
  sentiment_score: number;
  sentiment_confidence: number;
  predicted_direction: string;
  predicted_magnitude: number;
  prediction_confidence: number;
  optimal_action: string;
  timestamp: string;
}

export interface MarketSummary {
  total_banks: number;
  avg_change_1d: number;
  avg_sentiment: number;
  buy_signals: number;
  sell_signals: number;
  hold_signals: number;
  best_performer: {
    symbol: string;
    name: string;
    change: number;
    action: string;
  };
  worst_performer: {
    symbol: string;
    name: string;
    change: number;
    action: string;
  };
  last_updated: string;
}

export interface SentimentHeadline {
  symbol: string;
  headline: string;
  sentiment_score: number;
  confidence: number;
  category: string;
  timestamp: string;
}

class MLPredictionService {
  private baseURL = ML_API_BASE_URL;
  private websocket: WebSocket | null = null;
  private listeners: ((data: any) => void)[] = [];

  // REST API methods
  async getPredictions(): Promise<BankPrediction[]> {
    const response = await fetch(`${this.baseURL}/api/predictions`);
    if (!response.ok) throw new Error('Failed to fetch predictions');
    return response.json();
  }

  async getMarketSummary(): Promise<MarketSummary> {
    const response = await fetch(`${this.baseURL}/api/market-summary`);
    if (!response.ok) throw new Error('Failed to fetch market summary');
    return response.json();
  }

  async getSentimentHeadlines(limit = 10): Promise<SentimentHeadline[]> {
    const response = await fetch(`${this.baseURL}/api/sentiment-headlines?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch sentiment headlines');
    return response.json();
  }

  async getBankPrediction(symbol: string): Promise<BankPrediction> {
    const response = await fetch(`${this.baseURL}/api/bank/${symbol}`);
    if (!response.ok) throw new Error(`Failed to fetch prediction for ${symbol}`);
    return response.json();
  }

  async refreshData(): Promise<void> {
    const response = await fetch(`${this.baseURL}/api/refresh-data`, { method: 'POST' });
    if (!response.ok) throw new Error('Failed to refresh data');
  }

  // WebSocket methods for real-time updates
  connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.websocket = new WebSocket(`${WS_BASE_URL_8001}/ws/live-updates`);
        
        this.websocket.onopen = () => {
          console.log('🔗 Connected to ML real-time updates');
          resolve();
        };
        
        this.websocket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.notifyListeners(data);
          } catch (err) {
            console.error('Error parsing WebSocket message:', err);
          }
        };
        
        this.websocket.onclose = () => {
          console.log('🔌 WebSocket connection closed');
          // Auto-reconnect after 5 seconds
          setTimeout(() => this.connectWebSocket(), 5000);
        };
        
        this.websocket.onerror = (error) => {
          console.error('WebSocket error:', error);
          reject(error);
        };
        
      } catch (err) {
        reject(err);
      }
    });
  }

  subscribe(listener: (data: any) => void): () => void {
    this.listeners.push(listener);
    return () => {
      const index = this.listeners.indexOf(listener);
      if (index > -1) {
        this.listeners.splice(index, 1);
      }
    };
  }

  private notifyListeners(data: any): void {
    this.listeners.forEach(listener => listener(data));
  }

  disconnect(): void {
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
    this.listeners = [];
  }
}

export const mlPredictionService = new MLPredictionService();
