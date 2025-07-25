import { useState, useEffect, useRef } from 'react';
import { requestCache } from '../utils/requestCache';
import { useAPIError } from '../contexts/ErrorContext';

interface ChartDataPoint {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export const useChartData = (symbol: string, timeframe: string) => {
  const [chartData, setChartData] = useState<ChartDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const requestVersionRef = useRef(0);
  const { handleAPIError } = useAPIError();

  useEffect(() => {
    const fetchChartData = async () => {
      // Increment request version to handle race conditions
      const currentVersion = ++requestVersionRef.current;
      
      try {
        // Use request cache to prevent duplicate concurrent requests
        const cacheKey = `chart_${symbol}_${timeframe}`;
        const data = await requestCache.getOrFetch(cacheKey, async () => {
          const response = await fetch(`/api/banks/${symbol}/ohlcv?period=${timeframe}`, {
            signal: abortControllerRef.current?.signal,
          });
          
          if (!response.ok) {
            throw new Error(`Failed to fetch chart data: ${response.statusText}`);
          }
          
          return response.json();
        });
        
        // Only update state if this is still the current request
        if (currentVersion === requestVersionRef.current) {
          // Extract the data array from the API response
          setChartData(data.data || []);
        }
      } catch (error: any) {
        // Only handle error if this is still the current request and not cancelled
        if (currentVersion === requestVersionRef.current && error.name !== 'AbortError') {
          console.error('Error fetching chart data:', error);
          
          handleAPIError(
            error, 
            `Chart data for ${symbol}`,
            () => fetchChartData() // Retry function
          );
          
          setChartData([]);
        }
      } finally {
        // Only update loading if this is still the current request
        if (currentVersion === requestVersionRef.current) {
          setLoading(false);
        }
      }
    };    // Add a longer delay to reduce excessive requests when switching symbols/timeframes
    const timeoutId = setTimeout(() => {
      fetchChartData();
    }, 1000); // Increased from 300ms to 1000ms

    // Cleanup function to cancel request on unmount or dependency change
    return () => {
      clearTimeout(timeoutId);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [symbol, timeframe, handleAPIError]);

  return { chartData, loading, error };
};
