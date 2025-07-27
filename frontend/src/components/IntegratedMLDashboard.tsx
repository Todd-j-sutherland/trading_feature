// Integrated ML Dashboard - Uses Real ML Training Pipeline
// Connects morning data collection → evening ML training → real-time evaluation

import React, { useState, useEffect } from 'react';
import { API_BASE_URL } from '../constants/trading.constants';

interface MLFeatures {
  // Sentiment features
  sentiment_score: number;
  confidence: number;
  news_count: number;
  reddit_sentiment: number;
  
  // Technical indicators
  rsi: number;
  macd_line: number;
  macd_signal: number;
  bollinger_upper: number;
  bollinger_lower: number;
  
  // Price features
  current_price: number;
  price_change_1d: number;
  price_vs_sma20: number;
  volatility_20d: number;
  
  // Volume features
  volume_ratio: number;
  on_balance_volume: number;
}

interface MLPrediction {
  symbol: string;
  bank_name: string;
  timestamp: string;
  
  // Input features
  features: MLFeatures;
  
  // ML Model predictions
  direction_predictions: {
    "1h": boolean;
    "4h": boolean; 
    "1d": boolean;
  };
  magnitude_predictions: {
    "1h": number;
    "4h": number;
    "1d": number;
  };
  confidence_scores: {
    "1h": number;
    "4h": number;
    "1d": number;
  };
  optimal_action: string;
  overall_confidence: number;
  
  // Model metadata
  model_version: string;
  feature_count: number;
  training_date: string;
}

interface MLTrainingStatus {
  last_training_run: string;
  model_accuracy: {
    direction_accuracy_1h: number;
    direction_accuracy_4h: number;
    direction_accuracy_1d: number;
    magnitude_mae_1h: number;
    magnitude_mae_4h: number;
    magnitude_mae_1d: number;
  };
  training_samples: number;
  feature_importance: Array<{
    feature: string;
    importance: number;
  }>;
  validation_status: string;
}

const IntegratedMLDashboard: React.FC = () => {
  const [predictions, setPredictions] = useState<MLPrediction[]>([]);
  const [trainingStatus, setTrainingStatus] = useState<MLTrainingStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [connectionStatus, setConnectionStatus] = useState('Connecting...');

  // Fetch ML predictions from enhanced training pipeline
  const fetchMLData = async () => {
    try {
      setConnectionStatus('Fetching ML data...');
      
      const [predictionsRes, statusRes] = await Promise.all([
        fetch(`${API_BASE_URL}/ml/enhanced-predictions`),
        fetch(`${API_BASE_URL}/ml/training-status`)
      ]);

      if (predictionsRes.ok && statusRes.ok) {
        const predictionsData = await predictionsRes.json();
        const statusData = await statusRes.json();
        
        setPredictions(predictionsData.predictions || []);
        setTrainingStatus(statusData);
        setLastUpdate(new Date());
        setConnectionStatus('Connected ✅');
        
        console.log('✅ Integrated ML Data loaded:', {
          predictions: predictionsData.predictions?.length || 0,
          training_status: statusData.validation_status
        });
      } else {
        // Fallback to mock data for testing
        console.warn('⚠️ ML API not available, using mock data');
        generateMockData();
        setConnectionStatus('Mock Data Mode ⚠️');
      }
    } catch (err) {
      console.error('❌ Error fetching ML data:', err);
      generateMockData(); // Fallback to mock data
      setConnectionStatus('Fallback Mode ⚠️');
    } finally {
      setIsLoading(false);
    }
  };

  // Generate mock data for development/testing
  const generateMockData = () => {
    const banks = [
      { symbol: 'CBA.AX', name: 'Commonwealth Bank' },
      { symbol: 'ANZ.AX', name: 'ANZ Banking Group' },
      { symbol: 'WBC.AX', name: 'Westpac Banking' },
      { symbol: 'NAB.AX', name: 'National Australia Bank' },
      { symbol: 'MQG.AX', name: 'Macquarie Group' }
    ];

    const mockPredictions: MLPrediction[] = banks.map(bank => ({
      symbol: bank.symbol,
      bank_name: bank.name,
      timestamp: new Date().toISOString(),
      features: {
        sentiment_score: (Math.random() - 0.5) * 2, // -1 to 1
        confidence: 0.6 + Math.random() * 0.4, // 0.6 to 1.0
        news_count: Math.floor(Math.random() * 10),
        reddit_sentiment: (Math.random() - 0.5) * 2,
        rsi: 30 + Math.random() * 40, // 30 to 70
        macd_line: (Math.random() - 0.5) * 4,
        macd_signal: (Math.random() - 0.5) * 4,
        bollinger_upper: 100 + Math.random() * 50,
        bollinger_lower: 90 + Math.random() * 30,
        current_price: 80 + Math.random() * 80, // $80-160
        price_change_1d: (Math.random() - 0.5) * 10, // -5% to +5%
        price_vs_sma20: (Math.random() - 0.5) * 0.2, // -10% to +10%
        volatility_20d: 0.1 + Math.random() * 0.3, // 10% to 40%
        volume_ratio: 0.5 + Math.random() * 1.5, // 0.5x to 2.0x
        on_balance_volume: Math.random() * 1000000
      },
      direction_predictions: {
        "1h": Math.random() > 0.5,
        "4h": Math.random() > 0.5,
        "1d": Math.random() > 0.5
      },
      magnitude_predictions: {
        "1h": (Math.random() - 0.5) * 4, // -2% to +2%
        "4h": (Math.random() - 0.5) * 8, // -4% to +4%
        "1d": (Math.random() - 0.5) * 12 // -6% to +6%
      },
      confidence_scores: {
        "1h": 0.5 + Math.random() * 0.5,
        "4h": 0.5 + Math.random() * 0.5,
        "1d": 0.5 + Math.random() * 0.5
      },
      optimal_action: ['BUY', 'SELL', 'HOLD', 'STRONG_BUY', 'STRONG_SELL'][Math.floor(Math.random() * 5)],
      overall_confidence: 0.6 + Math.random() * 0.4,
      model_version: 'enhanced_v1.2',
      feature_count: 54,
      training_date: '2025-07-27'
    }));

    const mockTrainingStatus: MLTrainingStatus = {
      last_training_run: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
      model_accuracy: {
        direction_accuracy_1h: 0.72,
        direction_accuracy_4h: 0.68,
        direction_accuracy_1d: 0.75,
        magnitude_mae_1h: 1.2,
        magnitude_mae_4h: 2.1,
        magnitude_mae_1d: 3.4
      },
      training_samples: 2847,
      feature_importance: [
        { feature: 'sentiment_score', importance: 0.18 },
        { feature: 'rsi', importance: 0.15 },
        { feature: 'price_vs_sma20', importance: 0.12 },
        { feature: 'volume_ratio', importance: 0.10 },
        { feature: 'macd_line', importance: 0.09 }
      ],
      validation_status: 'PASSED'
    };

    setPredictions(mockPredictions);
    setTrainingStatus(mockTrainingStatus);
  };

  // Initialize and set up auto-refresh
  useEffect(() => {
    fetchMLData();
    
    // Auto-refresh every 2 minutes
    const interval = setInterval(fetchMLData, 120000);
    
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

  const getConfidenceColor = (confidence: number) => {
    if (confidence > 0.8) return 'text-green-400';
    if (confidence > 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getDirectionIcon = (direction: boolean) => direction ? '📈' : '📉';

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-400 mx-auto mb-4"></div>
            <h2 className="text-xl">Loading Integrated ML Dashboard...</h2>
            <p className="text-gray-400">Connecting to Enhanced ML Training Pipeline</p>
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
              <h1 className="text-3xl font-bold">🧠 Integrated ML Dashboard</h1>
              <p className="text-gray-400">Real ML Training Pipeline: Morning Data → Evening Training → Live Predictions</p>
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
                🔄 Refresh ML Data
              </button>
            </div>
          </div>
        </div>

        {/* Training Status Summary */}
        {trainingStatus && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Model Status</h3>
              <div className={`text-2xl font-bold ${
                trainingStatus.validation_status === 'PASSED' ? 'text-green-400' : 'text-red-400'
              }`}>
                {trainingStatus.validation_status}
              </div>
              <div className="text-sm text-gray-400 mt-1">
                Last Training: {new Date(trainingStatus.last_training_run).toLocaleString()}
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Direction Accuracy</h3>
              <div className="space-y-1">
                <div className="flex justify-between">
                  <span>1H:</span>
                  <span className="font-bold text-blue-400">
                    {(trainingStatus.model_accuracy.direction_accuracy_1h * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>4H:</span>
                  <span className="font-bold text-blue-400">
                    {(trainingStatus.model_accuracy.direction_accuracy_4h * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>1D:</span>
                  <span className="font-bold text-blue-400">
                    {(trainingStatus.model_accuracy.direction_accuracy_1d * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Training Data</h3>
              <div className="text-3xl font-bold text-blue-400">
                {trainingStatus.training_samples.toLocaleString()}
              </div>
              <div className="text-sm text-gray-400">samples</div>
            </div>
            
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">Top Feature</h3>
              <div className="text-lg font-bold text-green-400">
                {trainingStatus.feature_importance[0]?.feature || 'N/A'}
              </div>
              <div className="text-sm text-gray-400">
                {((trainingStatus.feature_importance[0]?.importance || 0) * 100).toFixed(1)}% importance
              </div>
            </div>
          </div>
        )}

        {/* ML Predictions Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {predictions.map((prediction) => (
            <div key={prediction.symbol} className="bg-gray-800 rounded-lg p-6 hover:bg-gray-750 transition-colors">
              
              {/* Header */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold">{prediction.bank_name}</h3>
                  <p className="text-gray-400 text-sm">{prediction.symbol}</p>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-bold ${getActionColor(prediction.optimal_action)}`}>
                  {prediction.optimal_action}
                </span>
              </div>

              {/* Current Market Data */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <p className="text-gray-400 text-sm">Price</p>
                  <p className="text-lg font-bold">${prediction.features.current_price.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">1D Change</p>
                  <p className={`text-lg font-bold ${
                    prediction.features.price_change_1d >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {prediction.features.price_change_1d >= 0 ? '+' : ''}{prediction.features.price_change_1d.toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">RSI</p>
                  <p className={`text-lg font-bold ${
                    prediction.features.rsi > 70 ? 'text-red-400' : 
                    prediction.features.rsi < 30 ? 'text-green-400' : 'text-yellow-400'
                  }`}>
                    {prediction.features.rsi.toFixed(1)}
                  </p>
                </div>
              </div>

              {/* ML Predictions */}
              <div className="border-t border-gray-700 pt-4 mb-4">
                <h4 className="text-sm font-semibold text-gray-300 mb-2">ML Direction Predictions</h4>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl">{getDirectionIcon(prediction.direction_predictions["1h"])}</div>
                    <div className="text-xs text-gray-400">1H</div>
                    <div className={`text-sm font-bold ${getConfidenceColor(prediction.confidence_scores["1h"])}`}>
                      {(prediction.confidence_scores["1h"] * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl">{getDirectionIcon(prediction.direction_predictions["4h"])}</div>
                    <div className="text-xs text-gray-400">4H</div>
                    <div className={`text-sm font-bold ${getConfidenceColor(prediction.confidence_scores["4h"])}`}>
                      {(prediction.confidence_scores["4h"] * 100).toFixed(0)}%
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl">{getDirectionIcon(prediction.direction_predictions["1d"])}</div>
                    <div className="text-xs text-gray-400">1D</div>
                    <div className={`text-sm font-bold ${getConfidenceColor(prediction.confidence_scores["1d"])}`}>
                      {(prediction.confidence_scores["1d"] * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
              </div>

              {/* Sentiment & Technical */}
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-gray-400 text-sm">Sentiment</p>
                  <p className={`font-bold ${
                    prediction.features.sentiment_score > 0.2 ? 'text-green-400' :
                    prediction.features.sentiment_score < -0.2 ? 'text-red-400' : 'text-yellow-400'
                  }`}>
                    {prediction.features.sentiment_score.toFixed(3)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">News Count</p>
                  <p className="font-bold text-blue-400">{prediction.features.news_count}</p>
                </div>
              </div>

              {/* Overall Confidence */}
              <div className="border-t border-gray-700 pt-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400 text-sm">Overall ML Confidence</span>
                  <span className={`font-bold ${getConfidenceColor(prediction.overall_confidence)}`}>
                    {(prediction.overall_confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2 mt-2">
                  <div 
                    className="bg-blue-400 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${prediction.overall_confidence * 100}%` }}
                  ></div>
                </div>
              </div>

              {/* Model Info */}
              <div className="mt-3 text-xs text-gray-500">
                Model: {prediction.model_version} • Features: {prediction.feature_count} • 
                Trained: {prediction.training_date}
              </div>
            </div>
          ))}
        </div>

        {/* Feature Importance */}
        {trainingStatus && (
          <div className="mt-8 bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Top ML Features (Feature Importance)</h3>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {trainingStatus.feature_importance.slice(0, 5).map((feature, index) => (
                <div key={feature.feature} className="text-center">
                  <div className="text-2xl font-bold text-blue-400">#{index + 1}</div>
                  <div className="text-sm font-semibold">{feature.feature}</div>
                  <div className="text-xs text-gray-400">{(feature.importance * 100).toFixed(1)}%</div>
                  <div className="w-full bg-gray-700 rounded-full h-1 mt-1">
                    <div 
                      className="bg-blue-400 h-1 rounded-full"
                      style={{ width: `${feature.importance * 100}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500">
          <p>Integrated ML Dashboard • Enhanced Training Pipeline</p>
          <p className="text-sm">
            Morning Data Collection → Evening ML Training → Real-time Predictions • Auto-refresh every 2 minutes
          </p>
        </div>
      </div>
    </div>
  );
};

export default IntegratedMLDashboard;