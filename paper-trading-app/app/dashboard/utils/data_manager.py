"""
Data management utilities for the dashboard
Handles loading, caching, and processing of sentiment and market data
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from ..utils.logging_config import setup_dashboard_logger, log_data_loading_stats, log_error_with_context

logger = setup_dashboard_logger(__name__)

class DataManager:
    """Manages data loading and caching for the dashboard"""
    
    def __init__(self, data_path: str = "data/sentiment_history"):
        self.data_path = data_path
        self.cache = {}
        self.cache_timeout = 300  # 5 minutes
        self.cache_timestamps = {}
        
        logger.info(f"DataManager initialized with path: {data_path}")
    
    def load_sentiment_data(self, symbols: List[str]) -> Dict[str, List[Dict]]:
        """
        Load sentiment history data for specified symbols
        
        Args:
            symbols: List of stock symbols to load data for
        
        Returns:
            Dictionary mapping symbols to their sentiment data
        """
        all_data = {}
        total_records = 0
        
        logger.info(f"Loading sentiment data for {len(symbols)} symbols from: {self.data_path}")
        
        for symbol in symbols:
            try:
                # Check cache first
                if self._is_cache_valid(symbol):
                    all_data[symbol] = self.cache[symbol]
                    logger.debug(f"Using cached data for {symbol}")
                    continue
                
                file_path = os.path.join(self.data_path, f"{symbol}_history.json")
                
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        data_list = data if isinstance(data, list) else [data]
                        
                        # Cache the data
                        self.cache[symbol] = data_list
                        self.cache_timestamps[symbol] = datetime.now()
                        
                        all_data[symbol] = data_list
                        record_count = len(data_list)
                        total_records += record_count
                        
                        log_data_loading_stats(logger, symbol, record_count, file_path)
                        
                else:
                    logger.warning(f"File not found: {file_path}")
                    all_data[symbol] = []
                    
            except Exception as e:
                log_error_with_context(logger, e, f"loading sentiment data for {symbol}", file_path=file_path)
                all_data[symbol] = []
        
        logger.info(f"Sentiment data loading complete - Total records: {total_records}")
        return all_data
    
    def get_latest_analysis(self, data: List[Dict]) -> Dict:
        """
        Get the most recent analysis from sentiment data
        
        Args:
            data: List of sentiment analysis records
        
        Returns:
            Most recent analysis record or empty dict
        """
        if not data:
            logger.debug("No data provided for latest analysis")
            return {}
        
        try:
            # Sort by timestamp and get the latest
            sorted_data = sorted(data, key=lambda x: x.get('timestamp', ''), reverse=True)
            latest = sorted_data[0] if sorted_data else {}
            
            if latest:
                timestamp = latest.get('timestamp', 'Unknown')
                logger.debug(f"Latest analysis found with timestamp: {timestamp}")
            else:
                logger.warning("No valid analysis found in data")
            
            return latest
            
        except Exception as e:
            log_error_with_context(logger, e, "getting latest analysis", data_length=len(data))
            return data[-1] if data else {}
    
    def calculate_performance_metrics(self, symbol: str, data: List[Dict], days: int = 30) -> Dict:
        """
        Calculate performance metrics for the specified period
        
        Args:
            symbol: Stock symbol
            data: Historical sentiment data
            days: Number of days to analyze
        
        Returns:
            Dictionary of performance metrics
        """
        if len(data) < 2:
            logger.warning(f"Insufficient data for performance metrics - Symbol: {symbol}, Records: {len(data)}")
            return {}
        
        try:
            # Get recent data
            recent_data = data[-days:] if len(data) >= days else data
            
            # Extract metrics
            sentiments = [entry.get('overall_sentiment', 0) for entry in recent_data]
            confidences = [entry.get('confidence', 0) for entry in recent_data]
            
            if not sentiments:
                logger.warning(f"No sentiment values found for {symbol}")
                return {}
            
            # Calculate statistics
            avg_sentiment = np.mean(sentiments)
            avg_confidence = np.mean(confidences)
            sentiment_volatility = np.std(sentiments) if len(sentiments) > 1 else 0
            
            # Calculate trend
            if len(sentiments) >= 7:
                recent_trend = sentiments[-1] - sentiments[-7]
            elif len(sentiments) >= 2:
                recent_trend = sentiments[-1] - sentiments[0]
            else:
                recent_trend = 0
            
            metrics = {
                'avg_sentiment': avg_sentiment,
                'avg_confidence': avg_confidence,
                'sentiment_volatility': sentiment_volatility,
                'recent_trend': recent_trend,
                'data_points': len(recent_data),
                'period_days': days
            }
            
            logger.debug(f"Performance metrics calculated for {symbol}: {metrics}")
            return metrics
            
        except Exception as e:
            log_error_with_context(logger, e, f"calculating performance metrics for {symbol}", 
                                 data_length=len(data), days=days)
            return {}
    
    def get_correlation_data(self, symbol: str, data: List[Dict], limit: int = 20) -> List[Dict]:
        """
        Get correlation data between sentiment and price movements
        
        Args:
            symbol: Stock symbol
            data: Historical sentiment data
            limit: Maximum number of data points to return
        
        Returns:
            List of correlation data points
        """
        correlation_points = []
        
        try:
            # Get recent entries
            recent_data = data[-limit:] if len(data) > limit else data
            
            for entry in recent_data:
                try:
                    sentiment = entry.get('overall_sentiment', 0)
                    confidence = entry.get('confidence', 0)
                    timestamp = entry.get('timestamp', '')
                    
                    if not timestamp:
                        continue
                    
                    # Parse timestamp
                    try:
                        if 'T' in timestamp:
                            date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        else:
                            date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    except:
                        continue
                    
                    # For now, we'll use a placeholder for price change
                    # In a real implementation, this would fetch actual price data
                    price_change = sentiment * 2.5 + np.random.normal(0, 0.5)  # Simulated correlation
                    
                    correlation_points.append({
                        'sentiment': sentiment,
                        'price_change': price_change,
                        'confidence': confidence,
                        'date': date
                    })
                    
                except Exception as e:
                    logger.debug(f"Error processing correlation point: {e}")
                    continue
            
            logger.debug(f"Generated {len(correlation_points)} correlation points for {symbol}")
            return correlation_points
            
        except Exception as e:
            log_error_with_context(logger, e, f"getting correlation data for {symbol}", 
                                 data_length=len(data), limit=limit)
            return []
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Check if cached data is still valid"""
        if symbol not in self.cache or symbol not in self.cache_timestamps:
            return False
        
        cache_age = datetime.now() - self.cache_timestamps[symbol]
        return cache_age.seconds < self.cache_timeout
    
    def clear_cache(self):
        """Clear all cached data"""
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.info("Data cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        stats = {
            'cached_symbols': len(self.cache),
            'cache_timeout': self.cache_timeout,
            'total_records': sum(len(data) for data in self.cache.values())
        }
        logger.debug(f"Cache stats: {stats}")
        return stats
