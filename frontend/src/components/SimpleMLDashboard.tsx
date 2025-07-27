// Simple ML Dashboard - Clean implementation for testing ML integration
// This is a standalone dashboard to isolate and test ML functionality

import React, { useState, useEffect } from 'react';

interface BankPrediction {
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

interface MarketSummary {
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

const SimpleMLDashboard: React.FC = () => {
  const [predictions, setPredictions] = useState<BankPrediction[]>([]);
  const [marketSummary, setMarketSummary] = useState<MarketSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');

  const API_BASE_URL = 'http://localhost:8001';

  // Fetch ML data
  const fetchMLData = async () => {
    try {
      setConnectionStatus('Fetching data...');
      
      const [predictionsRes, summaryRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/predictions`),
        fetch(`${API_BASE_URL}/api/market-summary`)
      ]);

      if (predictionsRes.ok && summaryRes.ok) {
        const predictionsData = await predictionsRes.json();
        const summaryData = await summaryRes.json();
        
        setPredictions(predictionsData);
        setMarketSummary(summaryData);
        setLastUpdate(new Date());
        setError(null);
        setConnectionStatus('Connected ✅');
        
        console.log('✅ ML Data loaded:', {
          predictions: predictionsData.length,
          summary: summaryData
        });
      } else {
        throw new Error(`API Error: ${predictionsRes.status} / ${summaryRes.status}`);
      }
    } catch (err) {
      console.error('❌ Error fetching ML data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch ML data');
      setConnectionStatus('Connection Failed ❌');
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize and set up auto-refresh
  useEffect(() => {
    fetchMLData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchMLData, 30000);
    
    return () => clearInterval(interval);
  }, []);

  // Utility functions
  const getActionColor = (action: string) => {
    switch (action) {
      case 'BUY': return 'bg-green-600 text-white';
      case 'STRONG_BUY': return 'bg-green-700 text-white';
      case 'SELL': return 'bg-red-600 text-white';
      case 'STRONG_SELL': return 'bg-red-700 text-white';
      default: return 'bg-yellow-500 text-black';
    }
  };

  const getSentimentColor = (score: number) => {
    if (score > 0.2) return 'text-green-400';
    if (score < -0.2) return 'text-red-400';
    return 'text-yellow-400';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-400 mx-auto mb-4"></div>
            <h2 className="text-xl">Loading ML Dashboard...</h2>
            <p className="text-gray-400">Connecting to ML API server</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <div className="text-red-400 text-6xl mb-4">❌</div>
            <h2 className="text-xl text-red-400 mb-4">Connection Error</h2>
            <p className="text-gray-300 mb-6">{error}</p>
            <button
              onClick={fetchMLData}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              Retry Connection
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h1 className="text-3xl font-bold">🤖 ML Trading Dashboard</h1>
              <p className="text-gray-400">Real-time ML predictions for Australian banks</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-400">Status: {connectionStatus}</div>
              <div className="text-sm text-gray-400">
                Last Update: {lastUpdate.toLocaleTimeString()}
              </div>
              <button
                onClick={fetchMLData}
                className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm transition-colors"
              >
                🔄 Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Market Summary */}
        {marketSummary && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Banks Analyzed</h3>
              <div className="text-3xl font-bold text-blue-400">
                {marketSummary.total_banks}
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Average 1D Change</h3>
              <div className={`text-3xl font-bold ${
                marketSummary.avg_change_1d >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {marketSummary.avg_change_1d >= 0 ? '+' : ''}{marketSummary.avg_change_1d.toFixed(2)}%
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">ML Signals</h3>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span>Buy:</span>
                  <span className="font-bold text-green-400">{marketSummary.buy_signals}</span>
                </div>
                <div className="flex justify-between">
                  <span>Hold:</span>
                  <span className="font-bold text-yellow-400">{marketSummary.hold_signals}</span>
                </div>
                <div className="flex justify-between">
                  <span>Sell:</span>
                  <span className="font-bold text-red-400">{marketSummary.sell_signals}</span>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Avg Sentiment</h3>
              <div className={`text-3xl font-bold ${getSentimentColor(marketSummary.avg_sentiment)}`}>
                {marketSummary.avg_sentiment.toFixed(3)}
              </div>
            </div>
          </div>
        )}

        {/* Live Predictions Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {predictions.map((prediction) => (
            <div key={prediction.symbol} className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-colors">
              {/* Header */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-lg font-semibold">{prediction.bank_name}</h3>
                  <p className="text-gray-400 text-sm">{prediction.symbol} • {prediction.sector}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-bold ${getActionColor(prediction.optimal_action)}`}>
                  {prediction.optimal_action}
                </span>
              </div>

              {/* Price Info */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-gray-400 text-sm">Current Price</p>
                  <p className="text-xl font-bold">${prediction.current_price.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">1D Change</p>
                  <p className={`text-xl font-bold ${
                    prediction.price_change_1d >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {prediction.price_change_1d >= 0 ? '+' : ''}{prediction.price_change_1d.toFixed(2)}%
                  </p>
                </div>
              </div>

              {/* Technical & Sentiment */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-gray-400 text-sm">RSI</p>
                  <p className="font-bold">{prediction.rsi.toFixed(1)}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Sentiment</p>
                  <p className={`font-bold ${getSentimentColor(prediction.sentiment_score)}`}>
                    {prediction.sentiment_score.toFixed(3)}
                  </p>
                </div>
              </div>

              {/* ML Confidence */}
              <div className="border-t border-gray-700 pt-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">ML Confidence</span>
                  <span className="font-bold text-blue-400">
                    {(prediction.prediction_confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
                  <div 
                    className="bg-blue-400 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${prediction.prediction_confidence * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Timestamp */}
              <div className="mt-3 text-xs text-gray-500">
                Updated: {new Date(prediction.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500">
          <p>Simple ML Dashboard • Real-time predictions from Enhanced ML System</p>
          <p className="text-sm">API: {API_BASE_URL} • Auto-refresh every 30 seconds</p>
        </div>
      </div>
    </div>
  );
};

export default SimpleMLDashboard;
