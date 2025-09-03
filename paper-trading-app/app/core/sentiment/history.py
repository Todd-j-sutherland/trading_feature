"""Sentiment history management"""
import os
import json
from datetime import datetime
import pandas as pd
from app.config.settings import Settings


class SentimentHistoryManager:
    """Manages sentiment history data"""

    def __init__(self, settings: Settings):
        """
        Initialize the SentimentHistoryManager.

        Args:
            settings: The application settings object.
        """
        self.settings = settings
        self.history_file = os.path.join(self.settings.DATA_DIR, 'sentiment_history.json')
        self.history = self.load_sentiment_history()

    def load_sentiment_history(self) -> list:
        """Load sentiment history from file."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading sentiment history: {e}")
                return []
        return []

    def store_sentiment(self, symbol: str, sentiment_score: float, confidence: float):
        """Store a new sentiment record."""
        record = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'sentiment_score': sentiment_score,
            'confidence': confidence
        }
        self.history.append(record)
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except IOError as e:
            print(f"Error saving sentiment history: {e}")

    def get_sentiment_trend(self, symbol: str, days: int = 7) -> dict:
        """
        Calculate the sentiment trend for a symbol over a number of days.

        Args:
            symbol: The stock symbol.
            days: The number of days to look back.

        Returns:
            A dictionary with trend information.
        """
        if not self.history:
            return {'trend': 0, 'confidence': 0, 'records_analyzed': 0}

        df = pd.DataFrame(self.history)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter for the given symbol and time period
        cutoff_date = datetime.now() - pd.Timedelta(days=days)
        symbol_df = df[(df['symbol'] == symbol) & (df['timestamp'] >= cutoff_date)]

        if len(symbol_df) < 2:
            return {'trend': 0, 'confidence': 0, 'records_analyzed': len(symbol_df)}

        # Sort by timestamp
        symbol_df = symbol_df.sort_values(by='timestamp')

        # Linear regression to find the trend
        symbol_df['time_delta'] = (symbol_df['timestamp'] - symbol_df['timestamp'].min()).dt.total_seconds()
        
        # Handle the case where all timestamps are the same
        if symbol_df['time_delta'].max() == 0:
            return {'trend': 0, 'confidence': 0, 'records_analyzed': len(symbol_df)}
            
        # Fit a simple linear regression model
        # Note: This is a simplified approach. For a more robust solution, consider using scikit-learn.
        X = symbol_df['time_delta']
        y = symbol_df['sentiment_score']
        
        # Using numpy for basic linear regression
        try:
            import numpy as np
            coeffs = np.polyfit(X, y, 1)
            trend = coeffs[0] # The slope of the line
        except ImportError:
            trend = 0 # Fallback if numpy is not available

        # Confidence can be based on the number of data points
        confidence = min(len(symbol_df) / 10.0, 1.0)

        return {
            'trend': trend,
            'confidence': confidence,
            'records_analyzed': len(symbol_df)
        }
