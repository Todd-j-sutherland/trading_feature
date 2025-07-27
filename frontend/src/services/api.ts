import axios, { AxiosError } from 'axios';
import { API_BASE_URL, WS_BASE_URL_8000 } from '../constants/trading.constants';
import { MLPrediction, OHLCVData } from '../types/trading.types';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Network status detection
let isOnline = navigator.onLine;
window.addEventListener('online', () => { isOnline = true; });
window.addEventListener('offline', () => { isOnline = false; });

// Exponential backoff retry function
const retryWithBackoff = async <T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> => {
  let lastError: any;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      // Don't retry on certain errors
      if (error instanceof AxiosError) {
        if (error.response?.status === 404 || error.response?.status === 401) {
          throw error;
        }
      }
      
      // Don't retry on the last attempt
      if (attempt === maxRetries) {
        break;
      }
      
      // Calculate delay with exponential backoff
      const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
};

// Enhanced error handling function
const handleAPIError = (error: any, context: string): never => {
  if (!isOnline) {
    throw new Error(`No internet connection. Please check your network and try again.`);
  }
  
  if (error instanceof AxiosError) {
    if (error.code === 'ECONNABORTED') {
      throw new Error(`Request timeout for ${context}. The server may be overloaded.`);
    }
    
    if (error.response) {
      const status = error.response.status;
      const message = error.response.data?.message || error.message;
      
      switch (status) {
        case 404:
          throw new Error(`${context} not found. Please check the symbol and try again.`);
        case 429:
          throw new Error(`Too many requests. Please wait a moment and try again.`);
        case 500:
          throw new Error(`Server error while fetching ${context}. Please try again later.`);
        case 503:
          throw new Error(`Service temporarily unavailable. Please try again in a few minutes.`);
        default:
          throw new Error(`Error fetching ${context}: ${message} (Status: ${status})`);
      }
    }
    
    if (error.request) {
      throw new Error(`No response received for ${context}. Please check your connection.`);
    }
  }
  
  throw new Error(`Unexpected error fetching ${context}: ${error.message || 'Unknown error'}`);
};

// API service functions with enhanced error handling
export const tradingAPI = {
  // Get OHLCV data for a symbol
  async getOHLCV(symbol: string, period: string = '1D', limit: number = 500): Promise<OHLCVData[]> {
    try {
      return await retryWithBackoff(async () => {
        const response = await api.get(`/banks/${symbol}/ohlcv`, {
          params: { period, limit }
        });
        return response.data.data || [];
      });
    } catch (error) {
      handleAPIError(error, `OHLCV data for ${symbol}`);
      return []; // This will never be reached due to handleAPIError throwing, but satisfies TypeScript
    }
  },

  // Get ML indicators for a symbol
  async getMLIndicators(symbol: string, period: string = '1D'): Promise<MLPrediction[]> {
    try {
      return await retryWithBackoff(async () => {
        const response = await api.get(`/banks/${symbol}/ml-indicators`, {
          params: { period }
        });
        return response.data.data || [];
      });
    } catch (error) {
      handleAPIError(error, `ML indicators for ${symbol}`);
      return []; // This will never be reached due to handleAPIError throwing, but satisfies TypeScript
    }
  },

  // Get latest predictions for a symbol
  async getLatestPredictions(symbol: string): Promise<MLPrediction | null> {
    try {
      return await retryWithBackoff(async () => {
        const response = await api.get(`/banks/${symbol}/predictions/latest`);
        return response.data.data || null;
      });
    } catch (error) {
      console.warn(`Warning: Could not fetch latest predictions for ${symbol}:`, error);
      return null; // Non-critical, return null instead of throwing
    }
  },

  // Get current sentiment data
  async getCurrentSentiment(): Promise<any> {
    try {
      return await retryWithBackoff(async () => {
        const response = await api.get('/sentiment/current');
        return response.data;
      });
    } catch (error) {
      console.warn('Warning: Could not fetch current sentiment:', error);
      return null; // Non-critical, return null instead of throwing
    }
  },

  // Health check endpoint
  async healthCheck(): Promise<boolean> {
    try {
      await api.get('/health', { timeout: 5000 });
      return true;
    } catch (error) {
      return false;
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
    this.url = `${WS_BASE_URL_8000}/api/stream/predictions`;
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
