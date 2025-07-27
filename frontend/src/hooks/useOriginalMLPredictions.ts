import { useState, useEffect, useRef } from 'react';
import { API_BASE_URL } from '../constants/trading.constants';
import { useAPIError } from '../contexts/ErrorContext';
import { requestCache, RequestCache } from '../utils/requestCache';

interface MLPrediction {
  time: number;
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

interface MLPredictionResponse {
  success: boolean;
  data: MLPrediction[];
  stats?: {
    total_records: number;
    records_with_technical: number;
    records_with_reddit: number;
    avg_confidence: number;
  };
}

// Original ML predictions hook - connects to main backend (port 8000)
// This preserves the exact original functionality for TradingChart compatibility
export const useOriginalMLPredictions = (symbol: string, timeframe: string) => {
  const [mlPredictions, setMlPredictions] = useState<MLPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<MLPredictionResponse['stats'] | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const requestVersionRef = useRef(0);
  const { handleAPIError } = useAPIError();

  useEffect(() => {
    const fetchMLPredictions = async () => {
      // Increment request version to handle race conditions
      const currentVersion = ++requestVersionRef.current;
      
      try {
        // Use request cache to prevent duplicate concurrent requests
        const cacheKey = `ml_${symbol}_${timeframe}`;
        const cacheTime = RequestCache.getCacheTime('ml_predictions'); // 15 minutes
        
        console.log(`🔮 Fetching ML predictions for ${symbol} (${timeframe}) - Cache: ${Math.round(cacheTime / 60000)}min`);
        
        const data = await requestCache.getOrFetch(cacheKey, async () => {
          console.log(`🌐 Making API call for ${symbol} ML predictions`);
          const response = await fetch(`${API_BASE_URL}/banks/${symbol}/ml-indicators?period=${timeframe}`, {
            signal: abortControllerRef.current?.signal,
          });
          
          if (!response.ok) {
            throw new Error(`Failed to fetch ML predictions: ${response.statusText}`);
          }
          
          return response.json();
        }, cacheTime); // Use the 15-minute cache time for ML predictions
        
        // Only update state if this is still the current request
        if (currentVersion === requestVersionRef.current) {
          console.log(`✅ ML predictions updated for ${symbol}: ${data.data?.length || 0} records`);
          setMlPredictions(data.data || []);
          setStats(data.stats || null);
          setError(null); // Clear any previous errors
        }
      } catch (error: any) {
        // Only handle error if this is still the current request and not cancelled
        if (currentVersion === requestVersionRef.current && error.name !== 'AbortError') {
          console.error('Error fetching original ML predictions:', error);
          
          setError(error.message);
          
          handleAPIError(
            error, 
            `ML predictions for ${symbol}`,
            () => fetchMLPredictions() // Retry function
          );
          
          setMlPredictions([]);
          setStats(null);
        }
      } finally {
        // Only update loading if this is still the current request
        if (currentVersion === requestVersionRef.current) {
          setLoading(false);
        }
      }
    };

    // Add a delay to prevent rapid requests on component mount
    const timeoutId = setTimeout(() => {
      fetchMLPredictions();
    }, 2000); // Increased from 1500ms to 2000ms to stagger requests further

    // Cleanup function to cancel request on unmount or dependency change
    return () => {
      clearTimeout(timeoutId);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [symbol, timeframe, handleAPIError]);

  return { mlPredictions, loading, error, stats };
};
