#!/usr/bin/env python3
"""
ML Model Backtester
Tests ML predictions against historical data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple
import sqlite3
import joblib
import json
import os

logger = logging.getLogger(__name__)

class MLBacktester:
    """Backtest ML model predictions"""
    
    def __init__(self, ml_pipeline, data_feed):
        self.ml_pipeline = ml_pipeline
        self.data_feed = data_feed
    
    def backtest_predictions(self, symbol: str, start_date: str, end_date: str) -> Dict:
        """
        Backtest ML predictions against actual price movements
        """
        # Get historical sentiment data
        conn = sqlite3.connect(self.ml_pipeline.db_path)
        query = '''
            SELECT * FROM sentiment_features 
            WHERE symbol = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp
        '''
        
        sentiment_df = pd.read_sql_query(query, conn, params=[symbol, start_date, end_date])
        conn.close()
        
        if sentiment_df.empty:
            return {'error': 'No historical data found'}
        
        # Get price data
        price_data = self.data_feed.get_historical_data(
            symbol, 
            period='1y'  # Adjust as needed
        )
        
        # Simulate trades based on ML predictions
        trades = []
        capital = 10000  # Starting capital
        position = 0
        
        for idx, row in sentiment_df.iterrows():
            # Prepare features for ML prediction
            features = {
                'sentiment_score': row['sentiment_score'],
                'confidence': row['confidence'],
                'news_count': row['news_count'],
                'reddit_sentiment': row['reddit_sentiment'],
                'event_score': row['event_score']
            }
            
            # Get ML prediction
            if self.ml_pipeline.get_latest_model_version():
                prediction = self._get_ml_prediction(features, row['timestamp'])
                
                # Find matching price data
                trade_date = pd.to_datetime(row['timestamp']).date()
                price_row = price_data[price_data.index.date == trade_date]
                
                if not price_row.empty:
                    current_price = price_row['Close'].iloc[0]
                    
                    # Simple trading logic
                    if prediction['prediction'] == 'PROFITABLE' and position == 0:
                        # Buy signal
                        position = capital / current_price
                        capital = 0
                        entry_price = current_price
                        entry_date = trade_date
                        
                    elif prediction['prediction'] == 'UNPROFITABLE' and position > 0:
                        # Sell signal
                        capital = position * current_price
                        trade_return = (current_price - entry_price) / entry_price
                        
                        trades.append({
                            'entry_date': entry_date,
                            'exit_date': trade_date,
                            'entry_price': entry_price,
                            'exit_price': current_price,
                            'return': trade_return,
                            'prediction': prediction
                        })
                        
                        position = 0
        
        # Calculate performance metrics
        metrics = self._calculate_backtest_metrics(trades, capital)
        
        return {
            'trades': trades,
            'metrics': metrics,
            'final_capital': capital,
            'total_return': (capital - 10000) / 10000
        }
    
    def _get_ml_prediction(self, features: Dict, timestamp: str) -> Dict:
        """Get ML prediction for given features"""
        try:
            # Load current model
            model_path = os.path.join(self.ml_pipeline.models_dir, 'current_model.pkl')
            metadata_path = os.path.join(self.ml_pipeline.models_dir, 'current_metadata.json')
            
            if not os.path.exists(model_path) or not os.path.exists(metadata_path):
                return {'prediction': 'UNKNOWN', 'probability': 0.5}
            
            model = joblib.load(model_path)
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            # Prepare features
            feature_df = pd.DataFrame([features])
            
            # Add engineered features
            feature_df['sentiment_confidence_interaction'] = (
                feature_df['sentiment_score'] * feature_df['confidence']
            )
            feature_df['news_volume_category'] = pd.cut(
                feature_df['news_count'], 
                bins=[0, 5, 10, 20, 100], 
                labels=[0, 1, 2, 3]
            ).astype(int)
            
            # Add time features
            ts = pd.to_datetime(timestamp)
            feature_df['hour'] = ts.hour
            feature_df['day_of_week'] = ts.dayofweek
            feature_df['is_market_hours'] = 1 if 10 <= ts.hour <= 16 else 0
            
            # Reorder columns to match training
            feature_df = feature_df[metadata['feature_columns']]
            
            # Make prediction
            probability = model.predict_proba(feature_df)[0, 1]
            prediction = 'PROFITABLE' if probability > 0.5 else 'UNPROFITABLE'
            
            return {
                'prediction': prediction,
                'probability': probability
            }
            
        except Exception as e:
            logger.error(f"Error making ML prediction: {e}")
            return {'prediction': 'UNKNOWN', 'probability': 0.5}
    
    def _calculate_backtest_metrics(self, trades: List[Dict], final_capital: float) -> Dict:
        """Calculate backtesting performance metrics"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'avg_return_per_trade': 0,
                'best_trade': 0,
                'worst_trade': 0
            }
        
        # Extract returns
        returns = [t.get('return', 0) for t in trades if 'return' in t]
        
        # Win rate
        winning_trades = sum(1 for r in returns if r > 0)
        win_rate = winning_trades / len(returns) if returns else 0
        
        # Sharpe ratio (simplified)
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Max drawdown
        cumulative_returns = np.cumprod(1 + np.array(returns))
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        return {
            'total_trades': len(trades),
            'win_rate': win_rate,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'avg_return_per_trade': np.mean(returns) if returns else 0,
            'best_trade': max(returns) if returns else 0,
            'worst_trade': min(returns) if returns else 0
        }
