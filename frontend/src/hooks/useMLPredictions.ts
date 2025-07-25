import { useState, useEffect } from 'react';

interface MLPrediction {
  time: number;
  sentimentScore: number;
  confidence: number;
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

export const useMLPredictions = (symbol: string, timeframe: string) => {
  const [mlPredictions, setMlPredictions] = useState<MLPrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<MLPredictionResponse['stats'] | null>(null);

  useEffect(() => {
    const fetchMLPredictions = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`http://localhost:8000/api/banks/${symbol}/ml-indicators?period=${timeframe}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch ML predictions: ${response.statusText}`);
        }
        
        const data: MLPredictionResponse = await response.json();
        if (data.success && data.data) {
          setMlPredictions(data.data);
          setStats(data.stats || null);
        } else {
          setMlPredictions([]);
          setStats(null);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        console.error('Error fetching ML predictions:', err);
        setMlPredictions([]);
        setStats(null);
      } finally {
        setLoading(false);
      }
    };

    fetchMLPredictions();
  }, [symbol, timeframe]);

  return { mlPredictions, loading, error, stats };
};
