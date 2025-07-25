/**
 * Real-time ML evaluation service
 * Continuously fetches Yahoo Finance data and runs ML predictions
 */

import { useState, useEffect } from 'react';

export interface LiveMLPrediction {
  timestamp: number;
  symbol: string;
  price: number;
  change: number;
  volume: number;
  sentimentScore: number;
  confidence: number;
  signal: 'BUY' | 'SELL' | 'HOLD';
  technicalScore: number;
  features: {
    // Core technical indicators (matching ML pipeline)
    rsi: number;
    macd: number;
    moving_avg_20: number;
    volume_ratio: number;
    price_momentum: number;
    volatility: number;
    // Extended features for ML compatibility
    current_price: number;
    price_change_pct: number;
    news_count: number;
    impact_score: number;
  };
}

export interface LiveOHLCV {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

class LiveMLService {
  private updateInterval: number = 30000; // 30 seconds
  private intervalId: NodeJS.Timeout | null = null;
  private subscribers: Map<string, (prediction: LiveMLPrediction) => void> = new Map();
  private priceSubscribers: Map<string, (data: LiveOHLCV) => void> = new Map();

  constructor() {
    this.startLiveUpdates();
  }

  /**
   * Subscribe to live ML predictions for a symbol
   */
  subscribeToMLPredictions(symbol: string, callback: (prediction: LiveMLPrediction) => void): void {
    this.subscribers.set(symbol, callback);
  }

  /**
   * Subscribe to live price data for a symbol
   */
  subscribeToPriceData(symbol: string, callback: (data: LiveOHLCV) => void): void {
    this.priceSubscribers.set(symbol, callback);
  }

  /**
   * Unsubscribe from updates
   */
  unsubscribe(symbol: string): void {
    this.subscribers.delete(symbol);
    this.priceSubscribers.delete(symbol);
  }

  /**
   * Start continuous live updates
   */
  private startLiveUpdates(): void {
    this.intervalId = setInterval(async () => {
      for (const symbol of this.subscribers.keys()) {
        try {
          await this.updateSymbol(symbol);
        } catch (error) {
          console.error(`Error updating ${symbol}:`, error);
        }
      }
    }, this.updateInterval);
  }

  /**
   * Stop live updates
   */
  stopLiveUpdates(): void {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  /**
   * Update a specific symbol with latest data and ML prediction
   */
  private async updateSymbol(symbol: string): Promise<void> {
    // 1. Fetch latest price data from Yahoo Finance via our API
    const priceData = await this.fetchLatestPrice(symbol);
    
    if (priceData && this.priceSubscribers.has(symbol)) {
      this.priceSubscribers.get(symbol)!(priceData);
    }

    // 2. Calculate technical indicators
    const technicalFeatures = await this.calculateTechnicalIndicators(symbol);

    // 3. Run ML prediction
    const mlPrediction = await this.runMLPrediction(symbol, priceData, technicalFeatures);

    // 4. Notify subscribers
    if (mlPrediction && this.subscribers.has(symbol)) {
      this.subscribers.get(symbol)!(mlPrediction);
    }
  }

  /**
   * Fetch latest price from Yahoo Finance
   */
  private async fetchLatestPrice(symbol: string): Promise<LiveOHLCV | null> {
    try {
      const response = await fetch(`/api/live/price/${symbol}`);
      if (!response.ok) throw new Error(`Failed to fetch price: ${response.statusText}`);
      
      const data = await response.json();
      return data.success ? data.data : null;
    } catch (error) {
      console.error('Error fetching latest price:', error);
      return null;
    }
  }

  /**
   * Calculate technical indicators
   */
  private async calculateTechnicalIndicators(symbol: string): Promise<any> {
    try {
      const response = await fetch(`/api/live/technical/${symbol}`);
      if (!response.ok) throw new Error(`Failed to fetch technical indicators: ${response.statusText}`);
      
      const data = await response.json();
      return data.success ? data.indicators : {};
    } catch (error) {
      console.error('Error calculating technical indicators:', error);
      return {};
    }
  }

  /**
   * Run ML prediction on latest data
   */
  private async runMLPrediction(symbol: string, priceData: LiveOHLCV | null, technicalFeatures: any): Promise<LiveMLPrediction | null> {
    if (!priceData) return null;

    try {
      const response = await fetch('/api/live/ml-predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symbol,
          priceData,
          technicalFeatures,
          timestamp: Date.now(),
        }),
      });

      if (!response.ok) throw new Error(`ML prediction failed: ${response.statusText}`);
      
      const data = await response.json();
      return data.success ? data.prediction : null;
    } catch (error) {
      console.error('Error running ML prediction:', error);
      return null;
    }
  }

  /**
   * Get current market status
   */
  isMarketOpen(): boolean {
    const now = new Date();
    const aestTime = new Date(now.toLocaleString('en-US', { timeZone: 'Australia/Sydney' }));
    const hours = aestTime.getHours();
    const day = aestTime.getDay();
    
    // ASX trading hours: Monday-Friday, 10:00 AM - 4:00 PM AEST
    const isWeekday = day >= 1 && day <= 5;
    const isAfterOpen = hours >= 10;
    const isBeforeClose = hours < 16;
    
    return isWeekday && isAfterOpen && isBeforeClose;
  }

  /**
   * Set update frequency (in milliseconds)
   */
  setUpdateInterval(interval: number): void {
    this.updateInterval = interval;
    
    // Restart with new interval
    this.stopLiveUpdates();
    this.startLiveUpdates();
  }
}

// Singleton instance
export const liveMLService = new LiveMLService();

// React hook for live ML predictions
export const useLiveMLPredictions = (symbol: string) => {
  const [prediction, setPrediction] = useState<LiveMLPrediction | null>(null);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    setIsLive(true);
    
    liveMLService.subscribeToMLPredictions(symbol, (newPrediction) => {
      setPrediction(newPrediction);
    });

    return () => {
      liveMLService.unsubscribe(symbol);
      setIsLive(false);
    };
  }, [symbol]);

  return { prediction, isLive };
};

// React hook for live price data
export const useLivePriceData = (symbol: string) => {
  const [priceData, setPriceData] = useState<LiveOHLCV | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    setIsConnected(true);
    
    liveMLService.subscribeToPriceData(symbol, (newPriceData) => {
      setPriceData(newPriceData);
    });

    return () => {
      liveMLService.unsubscribe(symbol);
      setIsConnected(false);
    };
  }, [symbol]);

  return { priceData, isConnected };
};
