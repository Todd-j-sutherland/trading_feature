import { useState, useEffect } from 'react';

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

  useEffect(() => {
    const fetchChartData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`http://localhost:8000/api/banks/${symbol}/ohlcv?period=${timeframe}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch chart data: ${response.statusText}`);
        }
        
        const data = await response.json();
        if (data.success && data.data) {
          setChartData(data.data);
        } else {
          setChartData([]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        console.error('Error fetching chart data:', err);
        setChartData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchChartData();
  }, [symbol, timeframe]);

  return { chartData, loading, error };
};
