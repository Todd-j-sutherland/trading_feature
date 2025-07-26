// Custom React hook for ML predictions
// Provides real-time data updates to components

import { useState, useEffect, useCallback } from 'react';
import { mlPredictionService, BankPrediction, MarketSummary, SentimentHeadline } from '../services/mlPredictionService';

export interface MLDataState {
  predictions: BankPrediction[];
  marketSummary: MarketSummary | null;
  sentimentHeadlines: SentimentHeadline[];
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
  lastUpdate: Date;
}

export const useMLPredictions = () => {
  const [state, setState] = useState<MLDataState>({
    predictions: [],
    marketSummary: null,
    sentimentHeadlines: [],
    isConnected: false,
    isLoading: true,
    error: null,
    lastUpdate: new Date()
  });

  // Update state helper
  const updateState = useCallback((updates: Partial<MLDataState>) => {
    setState(prev => ({ ...prev, ...updates }));
  }, []);

  // Initialize connection and load data
  useEffect(() => {
    let unsubscribe: (() => void) | null = null;

    const initializeML = async () => {
      try {
        // Connect to WebSocket for real-time updates
        await mlPredictionService.connectWebSocket();
        
        // Subscribe to real-time updates
        unsubscribe = mlPredictionService.subscribe((data) => {
          if (data.type === 'initial_data' || data.type === 'update' || data.type === 'live_update') {
            updateState({
              predictions: data.predictions || [],
              marketSummary: data.summary || null,
              lastUpdate: new Date(),
              isLoading: false,
              isConnected: true
            });
          }
        });

        // Load initial data via REST API
        const [predictions, summary, headlines] = await Promise.all([
          mlPredictionService.getPredictions(),
          mlPredictionService.getMarketSummary(),
          mlPredictionService.getSentimentHeadlines(10)
        ]);

        updateState({
          predictions,
          marketSummary: summary,
          sentimentHeadlines: headlines,
          isLoading: false,
          isConnected: true,
          error: null
        });

      } catch (err) {
        console.error('Error initializing ML connection:', err);
        updateState({
          error: 'Failed to connect to ML system',
          isLoading: false,
          isConnected: false
        });
      }
    };

    initializeML();

    // Cleanup on unmount
    return () => {
      if (unsubscribe) {
        unsubscribe();
      }
      mlPredictionService.disconnect();
    };
  }, [updateState]);

  // Manual refresh function
  const refreshData = useCallback(async () => {
    updateState({ isLoading: true });
    try {
      await mlPredictionService.refreshData();
      
      const [predictions, summary, headlines] = await Promise.all([
        mlPredictionService.getPredictions(),
        mlPredictionService.getMarketSummary(),
        mlPredictionService.getSentimentHeadlines(10)
      ]);

      updateState({
        predictions,
        marketSummary: summary,
        sentimentHeadlines: headlines,
        lastUpdate: new Date(),
        isLoading: false,
        error: null
      });
    } catch (err) {
      updateState({
        error: 'Failed to refresh data',
        isLoading: false
      });
    }
  }, [updateState]);

  // Get prediction for specific bank
  const getBankPrediction = useCallback(async (symbol: string): Promise<BankPrediction | null> => {
    try {
      return await mlPredictionService.getBankPrediction(symbol);
    } catch (err) {
      console.error(`Error fetching prediction for ${symbol}:`, err);
      return null;
    }
  }, []);

  return {
    ...state,
    refreshData,
    getBankPrediction
  };
};
