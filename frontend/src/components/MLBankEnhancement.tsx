// ML Integration Component
// Adds real-time ML predictions to existing bank selector

import React from 'react';
import { useMLPredictions } from '../hooks/useMLPredictions';

interface MLBankEnhancementProps {
  selectedBank: {
    symbol: string;
    name: string;
  };
}

export const MLBankEnhancement: React.FC<MLBankEnhancementProps> = ({ selectedBank }) => {
  const { predictions, marketSummary, isConnected, isLoading, error, lastUpdate } = useMLPredictions();

  // Find prediction for selected bank
  const bankPrediction = predictions.find(p => p.symbol === selectedBank.symbol);

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
        <div className="text-red-800 text-sm">
          ML System Error: {error}
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="text-blue-800 text-sm flex items-center">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
          Loading ML predictions...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Connection Status */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center">
          <div className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
          <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
            {isConnected ? 'Live ML Data' : 'Disconnected'}
          </span>
        </div>
        <span className="text-gray-500">
          Updated: {lastUpdate.toLocaleTimeString()}
        </span>
      </div>

      {/* Market Summary */}
      {marketSummary && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-white font-bold mb-2">📊 Market Overview</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-400">Banks Analyzed:</span>
              <span className="text-white ml-2 font-bold">{marketSummary.total_banks}</span>
            </div>
            <div>
              <span className="text-gray-400">Avg Change:</span>
              <span className={`ml-2 font-bold ${
                marketSummary.avg_change_1d >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {marketSummary.avg_change_1d >= 0 ? '+' : ''}{marketSummary.avg_change_1d.toFixed(2)}%
              </span>
            </div>
            <div>
              <span className="text-gray-400">Buy Signals:</span>
              <span className="text-green-400 ml-2 font-bold">{marketSummary.buy_signals}</span>
            </div>
            <div>
              <span className="text-gray-400">Avg Sentiment:</span>
              <span className={`ml-2 font-bold ${
                marketSummary.avg_sentiment > 0.1 ? 'text-green-400' : 
                marketSummary.avg_sentiment < -0.1 ? 'text-red-400' : 'text-yellow-400'
              }`}>
                {marketSummary.avg_sentiment.toFixed(3)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Bank-Specific ML Prediction */}
      {bankPrediction && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-white font-bold mb-2">🤖 ML Prediction for {selectedBank.symbol}</h3>
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Action:</span>
              <span className={`px-2 py-1 rounded text-xs font-bold ${
                bankPrediction.optimal_action === 'BUY' || bankPrediction.optimal_action === 'STRONG_BUY' 
                  ? 'bg-green-600 text-white'
                  : bankPrediction.optimal_action === 'SELL' || bankPrediction.optimal_action === 'STRONG_SELL'
                  ? 'bg-red-600 text-white'
                  : 'bg-yellow-600 text-black'
              }`}>
                {bankPrediction.optimal_action}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-400">Current Price:</span>
              <span className="text-white font-bold">${bankPrediction.current_price.toFixed(2)}</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-400">1D Change:</span>
              <span className={`font-bold ${
                bankPrediction.price_change_1d >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {bankPrediction.price_change_1d >= 0 ? '+' : ''}{bankPrediction.price_change_1d.toFixed(2)}%
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-400">RSI:</span>
              <span className="text-white">{bankPrediction.rsi.toFixed(1)}</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-400">Sentiment:</span>
              <span className={`font-bold ${
                bankPrediction.sentiment_score > 0.2 ? 'text-green-400' :
                bankPrediction.sentiment_score < -0.2 ? 'text-red-400' : 'text-yellow-400'
              }`}>
                {bankPrediction.sentiment_score.toFixed(3)}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-400">ML Confidence:</span>
              <span className="text-white font-bold">
                {(bankPrediction.prediction_confidence * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      )}
      
      {/* Quick Actions */}
      <div className="bg-gray-800 rounded-lg p-4">
        <h3 className="text-white font-bold mb-2">⚡ Quick Actions</h3>
        <div className="space-y-2">
          <button
            onClick={() => window.open('http://localhost:8001/docs', '_blank')}
            className="w-full text-left text-sm text-blue-400 hover:text-blue-300"
          >
            📊 View Full ML Dashboard
          </button>
          <button
            onClick={() => window.open('/Users/toddsutherland/Repos/trading_feature/enhanced_ml_system/bank_performance_dashboard.html', '_blank')}
            className="w-full text-left text-sm text-blue-400 hover:text-blue-300"
          >
            📈 HTML Performance Report
          </button>
          <button
            onClick={() => {
              // Could trigger a refresh of ML data
              console.log('Refresh ML data for', selectedBank.symbol);
            }}
            className="w-full text-left text-sm text-blue-400 hover:text-blue-300"
          >
            🔄 Refresh ML Analysis
          </button>
        </div>
      </div>
    </div>
  );
};

export default MLBankEnhancement;
