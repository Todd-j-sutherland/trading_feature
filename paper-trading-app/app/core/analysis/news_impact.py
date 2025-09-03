"""
News Impact Correlation Analysis
Analyzes the relationship between news sentiment and stock price movements
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from scipy.stats import pearsonr, spearmanr
import json
import os

# Import existing modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.data.collectors.market_data import ASXDataFeed
from app.core.sentiment.history import SentimentHistoryManager

logger = logging.getLogger(__name__)

class NewsImpactAnalyzer:
    """Analyzes correlation between news sentiment and price movements"""
    
    def __init__(self, settings):
        self.settings = settings
        self.data_feed = ASXDataFeed()
        self.sentiment_history = SentimentHistoryManager(settings)
        self.results_dir = "data/impact_analysis"
        self.ensure_results_dir()
    
    def ensure_results_dir(self):
        """Create results directory if it doesn't exist"""
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
    
    def analyze_sentiment_price_correlation(self, symbol: str, days: int = 30) -> Dict:
        """Analyze correlation between sentiment and price movements"""
        try:
            # Get historical sentiment data
            # Get all sentiment history and filter by symbol later
            all_history = self.sentiment_history.load_sentiment_history()
            sentiment_history = [h for h in all_history if h.get("symbol") == symbol]
            
            if not sentiment_history:
                return self._empty_correlation_result(symbol)
            
            # Get historical price data
            price_data = self.data_feed.get_historical_data(symbol, period=f"{days}d")
            
            if price_data.empty:
                return self._empty_correlation_result(symbol)
            
            # Align sentiment and price data
            aligned_data = self._align_sentiment_and_price_data(sentiment_history, price_data)
            
            if not aligned_data:
                return self._empty_correlation_result(symbol)
            
            # Calculate correlations
            correlations = self._calculate_correlations(aligned_data)
            
            # Analyze event impact
            event_impact = self._analyze_event_impact(aligned_data)
            
            # Calculate predictive metrics
            predictive_metrics = self._calculate_predictive_metrics(aligned_data)
            
            result = {
                'symbol': symbol,
                'analysis_period_days': days,
                'data_points': len(aligned_data),
                'correlations': correlations,
                'event_impact': event_impact,
                'predictive_metrics': predictive_metrics,
                'summary': self._generate_correlation_summary(correlations, event_impact),
                'recommendations': self._generate_recommendations(correlations, event_impact)
            }
            
            # Save results
            self._save_correlation_results(symbol, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment-price correlation for {symbol}: {e}")
            return self._empty_correlation_result(symbol)
    
    def _align_sentiment_and_price_data(self, sentiment_history: List[Dict], price_data: pd.DataFrame) -> List[Dict]:
        """Align sentiment data with price data by date"""
        try:
            aligned_data = []
            
            # Ensure we have a proper date index/column
            price_data = price_data.copy()  # Avoid modifying original data
            
            if isinstance(price_data.index, pd.DatetimeIndex):
                # Data has datetime index (common with yfinance)
                price_data['Date'] = price_data.index.date
            else:
                # Try to find or create a date column
                date_col = None
                for col in ['Date', 'date', 'Datetime', 'datetime', 'timestamp']:
                    if col in price_data.columns:
                        date_col = col
                        break
                
                if date_col:
                    price_data['Date'] = pd.to_datetime(price_data[date_col]).dt.date
                elif price_data.index.name in ['Date', 'date', 'Datetime', 'datetime']:
                    # Index might be named but not datetime
                    price_data = price_data.reset_index()
                    price_data['Date'] = pd.to_datetime(price_data[price_data.index.name]).dt.date
                else:
                    logger.error("No date information found in price data columns or index")
                    return []
            
            for sentiment_entry in sentiment_history:
                sentiment_date = datetime.fromisoformat(sentiment_entry['timestamp']).date()
                
                # Find matching price data
                matching_price = price_data[price_data['Date'] == sentiment_date]
                
                if not matching_price.empty:
                    price_row = matching_price.iloc[0]
                    
                    # Calculate price changes
                    try:
                        # Get previous day's close for comparison
                        prev_close = None
                        if len(price_data) > 1:
                            # Get the index position in the DataFrame
                            current_indices = price_data[price_data['Date'] == sentiment_date].index
                            if len(current_indices) > 0:
                                current_idx = current_indices[0]
                                # Find the position of this index in the DataFrame
                                idx_position = price_data.index.get_loc(current_idx)
                                if idx_position > 0:
                                    # Get the previous row by position
                                    prev_close = price_data.iloc[idx_position - 1]['Close']
                        
                        if prev_close is not None:
                            price_change_pct = ((price_row['Close'] - prev_close) / prev_close) * 100
                            price_change_abs = price_row['Close'] - prev_close
                        else:
                            price_change_pct = 0
                            price_change_abs = 0
                        
                        # Calculate intraday volatility
                        intraday_volatility = ((price_row['High'] - price_row['Low']) / price_row['Close']) * 100
                        
                        aligned_data.append({
                            'date': sentiment_date,
                            'sentiment': sentiment_entry.get('overall_sentiment', sentiment_entry.get('sentiment_score', 0)),
                            'news_count': sentiment_entry.get('news_count', 0),
                            'price_open': price_row['Open'],
                            'price_high': price_row['High'],
                            'price_low': price_row['Low'],
                            'price_close': price_row['Close'],
                            'volume': price_row['Volume'],
                            'price_change_pct': price_change_pct,
                            'price_change_abs': price_change_abs,
                            'intraday_volatility': intraday_volatility,
                            'events': sentiment_entry.get('significant_events', {}).get('events_detected', [])
                        })
                    except Exception as e:
                        logger.warning(f"Error calculating price changes for {sentiment_date}: {e}")
                        continue
            
            return aligned_data
            
        except Exception as e:
            logger.error(f"Error aligning sentiment and price data: {e}")
            return []
    
    def _calculate_correlations(self, aligned_data: List[Dict]) -> Dict:
        """Calculate various correlation metrics"""
        try:
            sentiments = [d['sentiment'] for d in aligned_data]
            price_changes = [d['price_change_pct'] for d in aligned_data]
            volatilities = [d['intraday_volatility'] for d in aligned_data]
            volumes = [d['volume'] for d in aligned_data]
            
            # Remove any NaN values
            valid_indices = [i for i in range(len(sentiments)) 
                           if not (pd.isna(sentiments[i]) or pd.isna(price_changes[i]))]
            
            if len(valid_indices) < 3:
                return {'error': 'Insufficient data for correlation analysis'}
            
            clean_sentiments = [sentiments[i] for i in valid_indices]
            clean_price_changes = [price_changes[i] for i in valid_indices]
            clean_volatilities = [volatilities[i] for i in valid_indices]
            clean_volumes = [volumes[i] for i in valid_indices]
            
            # Calculate correlations
            pearson_sentiment_price, pearson_p_value = pearsonr(clean_sentiments, clean_price_changes)
            spearman_sentiment_price, spearman_p_value = spearmanr(clean_sentiments, clean_price_changes)
            
            # Sentiment vs volatility
            pearson_sentiment_vol, _ = pearsonr(clean_sentiments, clean_volatilities)
            
            # Sentiment vs volume
            pearson_sentiment_volume, _ = pearsonr(clean_sentiments, clean_volumes)
            
            # Lagged correlations (next day price change)
            if len(clean_sentiments) > 1:
                lagged_price_changes = clean_price_changes[1:] + [0]  # Shift by one day
                lagged_correlations = {}
                for lag in range(1, min(4, len(clean_sentiments))):  # Up to 3 day lag
                    if lag < len(clean_sentiments):
                        lagged_prices = clean_price_changes[lag:] + [0] * lag
                        lagged_corr, _ = pearsonr(clean_sentiments[:-lag], lagged_prices[:-lag])
                        lagged_correlations[f'{lag}_day'] = lagged_corr
            else:
                lagged_correlations = {}
            
            return {
                'sentiment_vs_price': {
                    'pearson': pearson_sentiment_price,
                    'pearson_p_value': pearson_p_value,
                    'spearman': spearman_sentiment_price,
                    'spearman_p_value': spearman_p_value,
                    'significance': 'significant' if pearson_p_value < 0.05 else 'not_significant'
                },
                'sentiment_vs_volatility': {
                    'pearson': pearson_sentiment_vol,
                    'interpretation': self._interpret_correlation(pearson_sentiment_vol)
                },
                'sentiment_vs_volume': {
                    'pearson': pearson_sentiment_volume,
                    'interpretation': self._interpret_correlation(pearson_sentiment_volume)
                },
                'lagged_correlations': lagged_correlations,
                'data_quality': {
                    'total_points': len(aligned_data),
                    'valid_points': len(valid_indices),
                    'data_completeness': len(valid_indices) / len(aligned_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating correlations: {e}")
            return {'error': str(e)}
    
    def _analyze_event_impact(self, aligned_data: List[Dict]) -> Dict:
        """Analyze the impact of different event types on price movements"""
        try:
            event_impacts = {}
            
            # Group by event types
            event_types = set()
            for data_point in aligned_data:
                for event in data_point['events']:
                    event_types.add(event['type'])
            
            for event_type in event_types:
                event_days = []
                non_event_days = []
                
                for data_point in aligned_data:
                    has_event = any(event['type'] == event_type for event in data_point['events'])
                    
                    if has_event:
                        event_days.append(data_point['price_change_pct'])
                    else:
                        non_event_days.append(data_point['price_change_pct'])
                
                if event_days and non_event_days:
                    event_impacts[event_type] = {
                        'avg_price_change_event_days': np.mean(event_days),
                        'avg_price_change_non_event_days': np.mean(non_event_days),
                        'difference': np.mean(event_days) - np.mean(non_event_days),
                        'event_count': len(event_days),
                        'volatility_event_days': np.std(event_days),
                        'volatility_non_event_days': np.std(non_event_days)
                    }
            
            return {
                'event_type_impacts': event_impacts,
                'summary': self._summarize_event_impacts(event_impacts)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing event impact: {e}")
            return {'error': str(e)}
    
    def _calculate_predictive_metrics(self, aligned_data: List[Dict]) -> Dict:
        """Calculate metrics for predicting price movements from sentiment"""
        try:
            # Categorize sentiment and price movements
            sentiment_categories = []
            price_categories = []
            
            for data_point in aligned_data:
                # Categorize sentiment
                if data_point['sentiment'] > 0.2:
                    sentiment_cat = 'positive'
                elif data_point['sentiment'] < -0.2:
                    sentiment_cat = 'negative'
                else:
                    sentiment_cat = 'neutral'
                
                # Categorize price change
                if data_point['price_change_pct'] > 1:
                    price_cat = 'up'
                elif data_point['price_change_pct'] < -1:
                    price_cat = 'down'
                else:
                    price_cat = 'flat'
                
                sentiment_categories.append(sentiment_cat)
                price_categories.append(price_cat)
            
            # Calculate accuracy metrics
            correct_predictions = 0
            total_predictions = len(sentiment_categories)
            
            confusion_matrix = {
                'positive_sentiment': {'up': 0, 'down': 0, 'flat': 0},
                'negative_sentiment': {'up': 0, 'down': 0, 'flat': 0},
                'neutral_sentiment': {'up': 0, 'down': 0, 'flat': 0}
            }
            
            for sent_cat, price_cat in zip(sentiment_categories, price_categories):
                confusion_matrix[f'{sent_cat}_sentiment'][price_cat] += 1
                
                # Count correct predictions
                if (sent_cat == 'positive' and price_cat == 'up') or \
                   (sent_cat == 'negative' and price_cat == 'down') or \
                   (sent_cat == 'neutral' and price_cat == 'flat'):
                    correct_predictions += 1
            
            accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
            
            return {
                'prediction_accuracy': accuracy,
                'confusion_matrix': confusion_matrix,
                'total_predictions': total_predictions,
                'correct_predictions': correct_predictions,
                'sentiment_distribution': {
                    'positive': sentiment_categories.count('positive'),
                    'negative': sentiment_categories.count('negative'),
                    'neutral': sentiment_categories.count('neutral')
                },
                'price_distribution': {
                    'up': price_categories.count('up'),
                    'down': price_categories.count('down'),
                    'flat': price_categories.count('flat')
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating predictive metrics: {e}")
            return {'error': str(e)}
    
    def _interpret_correlation(self, correlation: float) -> str:
        """Interpret correlation coefficient"""
        abs_corr = abs(correlation)
        
        if abs_corr > 0.8:
            strength = 'very_strong'
        elif abs_corr > 0.6:
            strength = 'strong'
        elif abs_corr > 0.4:
            strength = 'moderate'
        elif abs_corr > 0.2:
            strength = 'weak'
        else:
            strength = 'very_weak'
        
        direction = 'positive' if correlation > 0 else 'negative'
        
        return f'{strength}_{direction}'
    
    def _generate_correlation_summary(self, correlations: Dict, event_impact: Dict) -> str:
        """Generate a summary of correlation analysis"""
        try:
            if 'error' in correlations:
                return "Insufficient data for correlation analysis"
            
            sentiment_price_corr = correlations['sentiment_vs_price']['pearson']
            significance = correlations['sentiment_vs_price']['significance']
            
            summary = f"Sentiment-price correlation: {sentiment_price_corr:.3f} ({significance}). "
            
            if abs(sentiment_price_corr) > 0.3:
                summary += "Strong correlation suggests news sentiment is a good predictor. "
            else:
                summary += "Weak correlation suggests other factors dominate price movements. "
            
            # Add event impact summary
            if 'event_type_impacts' in event_impact:
                high_impact_events = [
                    event_type for event_type, impact in event_impact['event_type_impacts'].items()
                    if abs(impact['difference']) > 1.0
                ]
                if high_impact_events:
                    summary += f"High-impact events: {', '.join(high_impact_events)}. "
            
            return summary
            
        except Exception as e:
            return f"Error generating summary: {e}"
    
    def _generate_recommendations(self, correlations: Dict, event_impact: Dict) -> List[str]:
        """Generate trading recommendations based on correlation analysis"""
        recommendations = []
        
        try:
            if 'error' in correlations:
                return ["Insufficient data for recommendations"]
            
            sentiment_price_corr = correlations['sentiment_vs_price']['pearson']
            significance = correlations['sentiment_vs_price']['significance']
            
            if significance == 'significant':
                if abs(sentiment_price_corr) > 0.5:
                    recommendations.append("Strong sentiment-price correlation detected. Consider sentiment-based trading strategies.")
                    
                    if sentiment_price_corr > 0:
                        recommendations.append("Positive correlation: Consider buying on positive sentiment spikes.")
                    else:
                        recommendations.append("Negative correlation: Consider contrarian strategy - sell on positive sentiment.")
                
                # Check lagged correlations
                lagged_corrs = correlations.get('lagged_correlations', {})
                for lag, corr in lagged_corrs.items():
                    if abs(corr) > 0.4:
                        recommendations.append(f"Strong {lag} lagged correlation ({corr:.3f}). Sentiment may predict future price movements.")
            
            else:
                recommendations.append("No significant sentiment-price correlation. Focus on technical/fundamental analysis.")
            
            # Event-based recommendations
            if 'event_type_impacts' in event_impact:
                for event_type, impact in event_impact['event_type_impacts'].items():
                    if abs(impact['difference']) > 1.5:
                        direction = "positive" if impact['difference'] > 0 else "negative"
                        recommendations.append(f"{event_type} events show strong {direction} impact ({impact['difference']:.2f}% avg).")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]
    
    def _summarize_event_impacts(self, event_impacts: Dict) -> Dict:
        """Summarize event impact analysis"""
        try:
            summary = {
                'highest_impact_positive': None,
                'highest_impact_negative': None,
                'most_frequent_event': None,
                'average_impact': 0
            }
            
            if not event_impacts:
                return summary
            
            impacts = [(event_type, impact['difference']) for event_type, impact in event_impacts.items()]
            
            # Find highest positive and negative impacts
            positive_impacts = [(event, impact) for event, impact in impacts if impact > 0]
            negative_impacts = [(event, impact) for event, impact in impacts if impact < 0]
            
            if positive_impacts:
                summary['highest_impact_positive'] = max(positive_impacts, key=lambda x: x[1])
            
            if negative_impacts:
                summary['highest_impact_negative'] = min(negative_impacts, key=lambda x: x[1])
            
            # Find most frequent event
            event_counts = [(event_type, impact['event_count']) for event_type, impact in event_impacts.items()]
            if event_counts:
                summary['most_frequent_event'] = max(event_counts, key=lambda x: x[1])
            
            # Calculate average impact
            all_impacts = [impact for _, impact in impacts]
            if all_impacts:
                summary['average_impact'] = sum(all_impacts) / len(all_impacts)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing event impacts: {e}")
            return {}
    
    def _empty_correlation_result(self, symbol: str) -> Dict:
        """Return empty correlation result"""
        return {
            'symbol': symbol,
            'analysis_period_days': 0,
            'data_points': 0,
            'correlations': {'error': 'No data available'},
            'event_impact': {'error': 'No data available'},
            'predictive_metrics': {'error': 'No data available'},
            'summary': 'No data available for correlation analysis',
            'recommendations': ['Insufficient data for analysis']
        }
    
    def _save_correlation_results(self, symbol: str, result: Dict):
        """Save correlation analysis results"""
        try:
            filename = os.path.join(self.results_dir, f"{symbol}_correlation_analysis.json")
            
            # Add analysis metadata
            result['analysis_timestamp'] = datetime.now().isoformat()
            result['analysis_version'] = '1.0'
            
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            logger.info(f"Saved correlation analysis for {symbol}")
            
        except Exception as e:
            logger.error(f"Error saving correlation results for {symbol}: {e}")
    
    def get_multi_symbol_analysis(self, symbols: List[str], days: int = 30) -> Dict:
        """Perform correlation analysis across multiple symbols"""
        try:
            results = {}
            
            for symbol in symbols:
                results[symbol] = self.analyze_sentiment_price_correlation(symbol, days)
            
            # Calculate comparative metrics
            comparative_analysis = self._calculate_comparative_metrics(results)
            
            return {
                'individual_analysis': results,
                'comparative_analysis': comparative_analysis,
                'summary': self._generate_multi_symbol_summary(results, comparative_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error in multi-symbol analysis: {e}")
            return {'error': str(e)}
    
    def _calculate_comparative_metrics(self, results: Dict) -> Dict:
        """Calculate comparative metrics across symbols"""
        try:
            # Extract correlations for comparison
            correlations = {}
            accuracies = {}
            
            for symbol, result in results.items():
                if 'error' not in result['correlations']:
                    correlations[symbol] = result['correlations']['sentiment_vs_price']['pearson']
                    
                if 'error' not in result['predictive_metrics']:
                    accuracies[symbol] = result['predictive_metrics']['prediction_accuracy']
            
            # Calculate statistics
            if correlations:
                avg_correlation = sum(correlations.values()) / len(correlations)
                max_correlation = max(correlations.items(), key=lambda x: x[1])
                min_correlation = min(correlations.items(), key=lambda x: x[1])
            else:
                avg_correlation = 0
                max_correlation = None
                min_correlation = None
            
            if accuracies:
                avg_accuracy = sum(accuracies.values()) / len(accuracies)
                max_accuracy = max(accuracies.items(), key=lambda x: x[1])
                min_accuracy = min(accuracies.items(), key=lambda x: x[1])
            else:
                avg_accuracy = 0
                max_accuracy = None
                min_accuracy = None
            
            return {
                'correlation_stats': {
                    'average': avg_correlation,
                    'highest': max_correlation,
                    'lowest': min_correlation,
                    'symbols_analyzed': len(correlations)
                },
                'accuracy_stats': {
                    'average': avg_accuracy,
                    'highest': max_accuracy,
                    'lowest': min_accuracy,
                    'symbols_analyzed': len(accuracies)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating comparative metrics: {e}")
            return {}
    
    def _generate_multi_symbol_summary(self, results: Dict, comparative_analysis: Dict) -> str:
        """Generate summary for multi-symbol analysis"""
        try:
            summary = f"Analyzed {len(results)} symbols. "
            
            if comparative_analysis and 'correlation_stats' in comparative_analysis:
                avg_corr = comparative_analysis['correlation_stats']['average']
                summary += f"Average sentiment-price correlation: {avg_corr:.3f}. "
                
                if avg_corr > 0.3:
                    summary += "Strong overall correlation suggests sentiment is valuable for this sector. "
                else:
                    summary += "Weak overall correlation suggests fundamental factors dominate. "
                
                highest = comparative_analysis['correlation_stats']['highest']
                if highest:
                    summary += f"Strongest correlation: {highest[0]} ({highest[1]:.3f}). "
            
            return summary
            
        except Exception as e:
            return f"Error generating multi-symbol summary: {e}"
    
    def _calculate_time_decay_weight(self, published_date: str) -> float:
        """Calculate time decay weight for news items"""
        try:
            # Handle different date formats
            if published_date.endswith('Z'):
                pub_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
            else:
                pub_date = datetime.fromisoformat(published_date)
            
            # Remove timezone info for comparison if present
            if pub_date.tzinfo:
                pub_date = pub_date.replace(tzinfo=None)
            
            hours_old = (datetime.now() - pub_date).total_seconds() / 3600
            
            # Exponential decay: half-life of 24 hours
            # Fresh news (< 6 hours) gets full weight
            # 24-hour old news gets 50% weight
            # 48-hour old news gets 25% weight
            if hours_old <= 6:
                return 1.0
            else:
                decay_rate = 0.5 ** ((hours_old - 6) / 24)
                return max(decay_rate, 0.1)  # Minimum 10% weight
        except Exception as e:
            logger.warning(f"Error calculating time decay for date {published_date}: {e}")
            return 0.5  # Default weight if date parsing fails

    def _detect_sentiment_divergence(self, source_sentiments: Dict[str, float]) -> Dict:
        """Detect significant divergence between different sentiment sources"""
        try:
            if len(source_sentiments) < 2:
                return {'divergence_detected': False}
            
            sentiment_values = list(source_sentiments.values())
            max_sentiment = max(sentiment_values)
            min_sentiment = min(sentiment_values)
            divergence = abs(max_sentiment - min_sentiment)
            
            # Calculate standard deviation for multiple sources
            mean_sentiment = sum(sentiment_values) / len(sentiment_values)
            variance = sum((x - mean_sentiment) ** 2 for x in sentiment_values) / len(sentiment_values)
            std_dev = variance ** 0.5
            
            if divergence > 0.5 or std_dev > 0.3:
                return {
                    'divergence_detected': True,
                    'magnitude': divergence,
                    'std_deviation': std_dev,
                    'source_agreement': 'low',
                    'interpretation': 'Major disagreement between sentiment sources',
                    'trading_implication': 'Higher volatility expected - conflicting signals'
                }
            elif divergence > 0.3 or std_dev > 0.2:
                return {
                    'divergence_detected': True,
                    'magnitude': divergence,
                    'std_deviation': std_dev,
                    'source_agreement': 'moderate',
                    'interpretation': 'Moderate disagreement between sentiment sources',
                    'trading_implication': 'Some uncertainty in sentiment signal'
                }
            else:
                return {
                    'divergence_detected': False,
                    'magnitude': divergence,
                    'std_deviation': std_dev,
                    'source_agreement': 'high',
                    'interpretation': 'Strong agreement between sentiment sources',
                    'trading_implication': 'High confidence in sentiment signal'
                }
                
        except Exception as e:
            logger.error(f"Error detecting sentiment divergence: {e}")
            return {'divergence_detected': False, 'error': str(e)}
    
    def _get_cached_ml_features(self, text_hash: str) -> Optional[Dict]:
        """Get cached ML features for text"""
        try:
            cache_key = f"ml_features_{text_hash}"
            # This would integrate with a caching system like Redis or simple file cache
            # For now, return None to indicate no cache
            return None
        except Exception as e:
            logger.warning(f"Error accessing ML features cache: {e}")
            return None

    def _cache_ml_features(self, text_hash: str, features: Dict, expiry_minutes: int = 1440):
        """Cache ML features for text"""
        try:
            cache_key = f"ml_features_{text_hash}"
            # This would integrate with a caching system
            # For now, just log that we would cache
            logger.debug(f"Would cache ML features for hash {text_hash[:8]}...")
        except Exception as e:
            logger.warning(f"Error caching ML features: {e}")
