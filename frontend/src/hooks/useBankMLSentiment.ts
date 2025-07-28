// Custom hook for individual bank ML sentiment data
// Used by the main dashboard's sentiment panel

import { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '../constants/trading.constants';

export interface BankMLSentiment {
  symbol: string;
  current_signal: string;           // BUY, SELL, HOLD, STRONG_BUY, STRONG_SELL
  confidence: number;               // 0-1 (percentage when displayed)
  sentiment_score: number;          // -1 to +1
  market_status: 'OPEN' | 'CLOSED' | 'PRE_MARKET' | 'AFTER_MARKET';
  signal_description: string;       // "Strong uptrend", "Bearish sentiment", etc.
  sentiment_description: string;    // "Bullish sentiment", "Neutral", etc.
  last_updated: string;
}

export const useBankMLSentiment = (symbol: string) => {
  const [sentiment, setSentiment] = useState<BankMLSentiment>({
    symbol,
    current_signal: 'HOLD',
    confidence: 0,
    sentiment_score: 0,
    market_status: 'CLOSED',
    signal_description: 'Loading...',
    sentiment_description: 'Loading...',
    last_updated: new Date().toISOString()
  });
  
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Helper function to determine market status
  const getMarketStatus = (): 'OPEN' | 'CLOSED' | 'PRE_MARKET' | 'AFTER_MARKET' => {
    const now = new Date();
    const sydneyTime = new Date(now.toLocaleString("en-US", { timeZone: "Australia/Sydney" }));
    const hour = sydneyTime.getHours();
    const day = sydneyTime.getDay();
    
    // Weekend
    if (day === 0 || day === 6) return 'CLOSED';
    
    // Weekday hours (ASX: 10:00 AM - 4:00 PM AEST)
    if (hour >= 10 && hour < 16) return 'OPEN';
    if (hour >= 8 && hour < 10) return 'PRE_MARKET';
    if (hour >= 16 && hour < 18) return 'AFTER_MARKET';
    
    return 'CLOSED';
  };

  // Helper functions for descriptions
  const getSignalDescription = (signal: string, confidence: number): string => {
    const confLevel = confidence > 0.8 ? 'Strong' : confidence > 0.6 ? 'Moderate' : 'Weak';
    
    switch (signal) {
      case 'STRONG_BUY':
        return 'Strong uptrend';
      case 'BUY':
        return confLevel === 'Strong' ? 'Bullish momentum' : 'Upward trend';
      case 'STRONG_SELL':
        return 'Strong downtrend';
      case 'SELL':
        return confLevel === 'Strong' ? 'Bearish momentum' : 'Downward trend';
      default:
        return 'Neutral trend';
    }
  };

  const getSentimentDescription = (score: number): string => {
    if (score > 0.5) return 'Very bullish';
    if (score > 0.2) return 'Bullish sentiment';
    if (score > -0.2) return 'Neutral';
    if (score > -0.5) return 'Bearish sentiment';
    return 'Very bearish';
  };

  // Fetch ML sentiment data
  const fetchMLSentiment = useCallback(async () => {
    if (!symbol) return;
    
    setIsLoading(true);
    setError(null);

    try {
      // Try the new ML prediction endpoint first
      const mlResponse = await fetch(`${API_BASE_URL}/live/ml-predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          symbol, 
          timeframe: '1d',
          timestamp: Date.now()
        })
      });

      if (mlResponse.ok) {
        const mlData = await mlResponse.json();
        if (mlData.success && mlData.prediction) {
          const pred = mlData.prediction;
          
          setSentiment({
            symbol,
            current_signal: pred.action || 'HOLD',
            confidence: pred.confidence || 0.5,
            sentiment_score: pred.sentiment_score || 0,
            market_status: getMarketStatus(),
            signal_description: getSignalDescription(pred.action || 'HOLD', pred.confidence || 0.5),
            sentiment_description: getSentimentDescription(pred.sentiment_score || 0),
            last_updated: new Date().toISOString()
          });
          setIsLoading(false);
          return;
        }
      }

      // Fallback to ML indicators endpoint
      const indicatorsResponse = await fetch(`${API_BASE_URL}/banks/${symbol}/ml-indicators`);
      if (indicatorsResponse.ok) {
        const indicatorsData = await indicatorsResponse.json();
        
        if (indicatorsData.success && indicatorsData.data && indicatorsData.data.length > 0) {
          const latest = indicatorsData.data[indicatorsData.data.length - 1];
          
          setSentiment({
            symbol,
            current_signal: latest.signal || 'HOLD',
            confidence: latest.confidence || 0.5,
            sentiment_score: latest.sentimentScore || 0,
            market_status: getMarketStatus(),
            signal_description: getSignalDescription(latest.signal || 'HOLD', latest.confidence || 0.5),
            sentiment_description: getSentimentDescription(latest.sentimentScore || 0),
            last_updated: new Date().toISOString()
          });
          setIsLoading(false);
          return;
        }
      }

      // Final fallback to current sentiment
      const sentimentResponse = await fetch(`${API_BASE_URL}/sentiment/current`);
      if (sentimentResponse.ok) {
        const sentimentData = await sentimentResponse.json();
        
        if (sentimentData.success && sentimentData.data[symbol]) {
          const data = sentimentData.data[symbol];
          
          setSentiment({
            symbol,
            current_signal: 'HOLD',
            confidence: data.confidence || 0.5,
            sentiment_score: data.sentiment_score || 0,
            market_status: getMarketStatus(),
            signal_description: 'Market analysis',
            sentiment_description: getSentimentDescription(data.sentiment_score || 0),
            last_updated: new Date().toISOString()
          });
        }
      }
      
    } catch (err) {
      console.error('Error fetching ML sentiment:', err);
      setError('Failed to load sentiment data');
    } finally {
      setIsLoading(false);
    }
  }, [symbol]);

  // Initial load and refresh interval
  useEffect(() => {
    fetchMLSentiment();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchMLSentiment, 30000);
    
    return () => clearInterval(interval);
  }, [fetchMLSentiment]);

  return {
    sentiment,
    isLoading,
    error,
    refresh: fetchMLSentiment
  };
};
