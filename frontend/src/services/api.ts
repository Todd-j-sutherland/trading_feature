import axios from 'axios';
import { API_BASE_URL } from '../constants/trading.constants';
import { MLPrediction, OHLCVData, APIResponse } from '../types/trading.types';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API service functions
export const tradingAPI = {
  // Get OHLCV data for a symbol
  async getOHLCV(symbol: string, period: string = '1D', limit: number = 500): Promise<OHLCVData[]> {
    try {
      const response = await api.get(`/banks/${symbol}/ohlcv`, {
        params: { period, limit }
      });
      return response.data.data || [];
    } catch (error) {
      console.error(`Error fetching OHLCV for ${symbol}:`, error);
      return [];
    }
  },

  // Get ML indicators for a symbol
  async getMLIndicators(symbol: string, period: string = '1D'): Promise<MLPrediction[]> {
    try {
      const response = await api.get(`/banks/${symbol}/ml-indicators`, {
        params: { period }
      });
      return response.data.data || [];
    } catch (error) {
      console.error(`Error fetching ML indicators for ${symbol}:`, error);
      return [];
    }
  },

  // Get latest predictions for a symbol
  async getLatestPredictions(symbol: string): Promise<MLPrediction | null> {
    try {
      const response = await api.get(`/banks/${symbol}/predictions/latest`);
      return response.data.data || null;
    } catch (error) {
      console.error(`Error fetching latest predictions for ${symbol}:`, error);
      return null;
    }
  },

  // Get current sentiment data (for now, we'll use your existing dashboard data)
  async getCurrentSentiment(): Promise<any> {
    try {
      // This will connect to your existing Streamlit dashboard data
      // We'll create a simple endpoint that returns the current sentiment
      const response = await api.get('/sentiment/current');
      return response.data;
    } catch (error) {
      console.error('Error fetching current sentiment:', error);
      return null;
    }
  }
};

// WebSocket connection for real-time updates
export class TradingWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private onMessage: (data: any) => void;
  private onError: (error: any) => void;

  constructor(onMessage: (data: any) => void, onError: (error: any) => void = console.error) {
    this.url = 'ws://localhost:8000/api/stream/predictions';
    this.onMessage = onMessage;
    this.onError = onError;
  }

  connect() {
    try {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.onMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.onError(error);
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Auto-reconnect after 5 seconds
        setTimeout(() => this.connect(), 5000);
      };
    } catch (error) {
      console.error('Error connecting WebSocket:', error);
      this.onError(error);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

export default tradingAPI;
