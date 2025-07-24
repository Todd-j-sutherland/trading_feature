"""
ML Progression Tracker - Historical Performance Analysis
Tracks machine learning model performance over time for dashboard visualization
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MLProgressionTracker:
    """Tracks and analyzes ML model performance progression over time"""
    
    def __init__(self, data_dir: str = "data/ml_performance"):
        """
        Initialize the ML progression tracker
        
        Args:
            data_dir: Directory to store ML performance data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.performance_file = self.data_dir / "ml_performance_history.json"
        self.predictions_file = self.data_dir / "prediction_history.json"
        self.model_metrics_file = self.data_dir / "model_metrics_history.json"
        
        # Load existing data
        self.performance_history = self._load_performance_history()
        self.prediction_history = self._load_prediction_history()
        self.model_metrics_history = self._load_model_metrics_history()
    
    def _load_performance_history(self) -> List[Dict]:
        """Load historical performance data"""
        if self.performance_file.exists():
            try:
                with open(self.performance_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load performance history: {e}")
        return []
    
    def _load_prediction_history(self) -> List[Dict]:
        """Load historical prediction data"""
        if self.predictions_file.exists():
            try:
                with open(self.predictions_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load prediction history: {e}")
        return []
    
    def _load_model_metrics_history(self) -> List[Dict]:
        """Load historical model metrics data"""
        if self.model_metrics_file.exists():
            try:
                with open(self.model_metrics_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load model metrics history: {e}")
        return []
    
    def record_prediction(self, symbol: str, prediction: Dict, actual_outcome: Dict = None) -> str:
        """
        Record a new ML prediction with enhanced deduplication
        
        Args:
            symbol: Stock symbol
            prediction: Prediction details from ML model
            actual_outcome: Actual market outcome (if available)
            
        Returns:
            Prediction ID for tracking
        """
        now = datetime.now()
        
        # Enhanced deduplication - check for duplicates within 30 minutes
        cutoff_time = now - timedelta(minutes=30)
        
        for existing in reversed(self.prediction_history):
            if existing['symbol'] == symbol:
                existing_time = datetime.fromisoformat(existing['timestamp'])
                if existing_time > cutoff_time:
                    existing_pred = existing['prediction']
                    
                    # Check for exact signal match
                    same_signal = existing_pred.get('signal') == prediction.get('signal')
                    
                    # Check confidence similarity (within 10%)
                    existing_conf = existing_pred.get('confidence', 0)
                    new_conf = prediction.get('confidence', 0)
                    confidence_diff = abs(existing_conf - new_conf)
                    similar_confidence = confidence_diff < 0.1
                    
                    # Check sentiment score similarity (within 0.05)
                    existing_sentiment = existing_pred.get('sentiment_score', 0)
                    new_sentiment = prediction.get('sentiment_score', 0)
                    sentiment_diff = abs(existing_sentiment - new_sentiment)
                    similar_sentiment = sentiment_diff < 0.05
                    
                    # If signal and confidence are similar, consider it a duplicate
                    if same_signal and (similar_confidence or similar_sentiment):
                        logger.info(f"🚫 Skipping duplicate prediction for {symbol}")
                        logger.info(f"   Existing: {existing_pred.get('signal')} @ {existing_conf:.1%} confidence")
                        logger.info(f"   New: {prediction.get('signal')} @ {new_conf:.1%} confidence")
                        logger.info(f"   Time difference: {(now - existing_time).total_seconds()/60:.1f} minutes")
                        return existing['id']
                break  # Only check the most recent prediction for this symbol
        
        # Generate unique prediction ID with microseconds to avoid collisions
        prediction_id = f"{symbol}_{now.strftime('%Y%m%d_%H%M%S_%f')}"
        
        prediction_record = {
            'id': prediction_id,
            'timestamp': now.isoformat(),
            'symbol': symbol,
            'prediction': prediction,
            'actual_outcome': actual_outcome,
            'status': 'pending' if actual_outcome is None else 'completed'
        }
        
        self.prediction_history.append(prediction_record)
        self._save_prediction_history()
        
        logger.info(f"✅ Recorded prediction {prediction_id} for {symbol}")
        logger.info(f"   Signal: {prediction.get('signal', 'N/A')}")
        logger.info(f"   Confidence: {prediction.get('confidence', 0):.1%}")
        return prediction_id
    
    def cleanup_duplicate_predictions(self, dry_run: bool = True) -> int:
        """
        Remove duplicate predictions from history
        
        Args:
            dry_run: If True, only report what would be removed
            
        Returns:
            Number of duplicates found/removed
        """
        if not self.prediction_history:
            return 0
        
        seen_predictions = {}
        duplicates_to_remove = []
        
        for i, pred in enumerate(self.prediction_history):
            symbol = pred['symbol']
            timestamp = pred['timestamp']
            prediction_data = pred['prediction']
            
            # Create a key based on symbol, day, signal, and rounded confidence
            try:
                pred_time = datetime.fromisoformat(timestamp)
                day_key = pred_time.strftime('%Y-%m-%d')
                signal = prediction_data.get('signal', 'UNKNOWN')
                confidence = round(prediction_data.get('confidence', 0), 1)  # Round to 1 decimal
                
                key = f"{symbol}_{day_key}_{signal}_{confidence}"
                
                if key in seen_predictions:
                    # This is a duplicate
                    duplicates_to_remove.append(i)
                    if not dry_run:
                        logger.info(f"🗑️ Removing duplicate: {pred['id']}")
                    else:
                        logger.info(f"🔍 Found duplicate: {pred['id']}")
                else:
                    seen_predictions[key] = i
                    
            except Exception as e:
                logger.warning(f"Error processing prediction {pred.get('id', 'unknown')}: {e}")
        
        if duplicates_to_remove:
            if not dry_run:
                # Remove duplicates (in reverse order to maintain indices)
                for i in reversed(duplicates_to_remove):
                    del self.prediction_history[i]
                self._save_prediction_history()
                logger.info(f"✅ Removed {len(duplicates_to_remove)} duplicate predictions")
            else:
                logger.info(f"🔍 Found {len(duplicates_to_remove)} duplicate predictions (dry run)")
        
        return len(duplicates_to_remove)
    
    def update_prediction_outcome(self, prediction_id: str, actual_outcome: Dict):
        """
        Update a prediction with actual market outcome
        
        Args:
            prediction_id: ID of the prediction to update
            actual_outcome: Actual market outcome data
        """
        for record in self.prediction_history:
            if record['id'] == prediction_id:
                record['actual_outcome'] = actual_outcome
                record['status'] = 'completed'
                record['outcome_timestamp'] = datetime.now().isoformat()
                break
        
        self._save_prediction_history()
        self._calculate_prediction_accuracy()
        logger.info(f"Updated prediction outcome for {prediction_id}")
    
    def record_model_metrics(self, model_type: str, metrics: Dict):
        """
        Record model training metrics
        
        Args:
            model_type: Type of model (sentiment, pattern, etc.)
            metrics: Model performance metrics
        """
        metrics_record = {
            'timestamp': datetime.now().isoformat(),
            'model_type': model_type,
            'metrics': metrics,
            'training_samples': metrics.get('training_samples', 0),
            'validation_accuracy': metrics.get('validation_accuracy', 0),
            'cross_validation_score': metrics.get('cross_validation_score', 0),
            'feature_importance': metrics.get('feature_importance', {}),
            'model_version': metrics.get('model_version', '1.0')
        }
        
        self.model_metrics_history.append(metrics_record)
        self._save_model_metrics_history()
        logger.info(f"Recorded metrics for {model_type} model")
    
    def record_daily_performance(self, performance_data: Dict):
        """
        Record daily ML system performance
        
        Args:
            performance_data: Daily performance metrics
        """
        daily_record = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'timestamp': datetime.now().isoformat(),
            'performance': performance_data,
            'predictions_made': len([p for p in self.prediction_history 
                                  if p['timestamp'].startswith(datetime.now().strftime('%Y-%m-%d'))]),
            'accuracy_metrics': self._calculate_recent_accuracy(days=1),
            'model_confidence': performance_data.get('average_confidence', 0),
            'successful_trades': performance_data.get('successful_trades', 0),
            'total_trades': performance_data.get('total_trades', 0)
        }
        
        self.performance_history.append(daily_record)
        self._save_performance_history()
        logger.info(f"Recorded daily performance for {daily_record['date']}")
    
    def get_progression_summary(self, days: int = 30) -> Dict:
        """
        Get ML progression summary for specified period
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with progression metrics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter recent data
        recent_performance = [
            p for p in self.performance_history 
            if datetime.fromisoformat(p['timestamp']) >= cutoff_date
        ]
        
        recent_predictions = [
            p for p in self.prediction_history 
            if datetime.fromisoformat(p['timestamp']) >= cutoff_date
        ]
        
        recent_metrics = [
            m for m in self.model_metrics_history 
            if datetime.fromisoformat(m['timestamp']) >= cutoff_date
        ]
        
        # Calculate progression metrics
        summary = {
            'period_days': days,
            'total_predictions': len(recent_predictions),
            'completed_predictions': len([p for p in recent_predictions if p['status'] == 'completed']),
            'accuracy_progression': self._calculate_accuracy_progression(recent_predictions),
            'confidence_progression': self._calculate_confidence_progression(recent_predictions),
            'model_improvement': self._calculate_model_improvement(recent_metrics),
            'trading_performance': self._calculate_trading_performance(recent_performance),
            'daily_metrics': self._get_daily_metrics(recent_performance),
            'trend_analysis': self._analyze_trends(recent_performance)
        }
        
        return summary
    
    def get_detailed_progression_data(self, days: int = 30) -> pd.DataFrame:
        """
        Get detailed progression data for visualization
        
        Args:
            days: Number of days of data to return
            
        Returns:
            DataFrame with daily progression metrics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Create daily progression dataframe
        daily_data = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # Get predictions for this day
            day_predictions = [
                p for p in self.prediction_history 
                if p['timestamp'].startswith(date_str)
            ]
            
            # Get performance for this day
            day_performance = [
                p for p in self.performance_history 
                if p.get('date') == date_str
            ]
            
            # Calculate daily metrics
            accuracy = self._calculate_daily_accuracy(day_predictions)
            confidence = self._calculate_daily_confidence(day_predictions)
            trade_count = len(day_predictions)
            
            daily_data.append({
                'date': date,
                'predictions_made': trade_count,
                'accuracy': accuracy,
                'confidence': confidence,
                'successful_trades': len([p for p in day_predictions 
                                        if self._is_successful_prediction(p)]),
                'model_confidence': day_performance[0]['model_confidence'] if day_performance else 0,
                'training_samples': self._get_training_samples_for_date(date_str)
            })
        
        df = pd.DataFrame(daily_data)
        df = df.sort_values('date')
        return df
    
    def _calculate_prediction_accuracy(self):
        """Calculate overall prediction accuracy"""
        completed_predictions = [p for p in self.prediction_history if p['status'] == 'completed']
        
        if not completed_predictions:
            return 0
        
        successful = sum(1 for p in completed_predictions if self._is_successful_prediction(p))
        return successful / len(completed_predictions)
    
    def _calculate_recent_accuracy(self, days: int = 7) -> Dict:
        """Calculate accuracy metrics for recent period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_predictions = [
            p for p in self.prediction_history 
            if datetime.fromisoformat(p['timestamp']) >= cutoff_date and p['status'] == 'completed'
        ]
        
        if not recent_predictions:
            return {'accuracy': 0, 'total_predictions': 0, 'successful_predictions': 0}
        
        successful = sum(1 for p in recent_predictions if self._is_successful_prediction(p))
        
        return {
            'accuracy': successful / len(recent_predictions),
            'total_predictions': len(recent_predictions),
            'successful_predictions': successful,
            'period_days': days
        }
    
    def _is_successful_prediction(self, prediction: Dict) -> bool:
        """Determine if a prediction was successful"""
        if prediction['status'] != 'completed' or not prediction.get('actual_outcome'):
            return False
        
        # Safely get predicted signal from prediction dict or top level
        predicted_signal = 'HOLD'
        if isinstance(prediction.get('prediction'), dict):
            predicted_signal = prediction['prediction'].get('signal', 'HOLD')
        elif 'signal' in prediction:
            predicted_signal = prediction.get('signal', 'HOLD')
        
        actual_outcome = prediction['actual_outcome']
        
        # Handle both dict and float formats for actual_outcome
        if isinstance(actual_outcome, dict):
            # New format: nested dictionary
            price_change_percent = actual_outcome.get('price_change_percent', 0)
        elif isinstance(actual_outcome, (int, float)):
            # Old format: direct float value (convert to percentage)
            price_change_percent = actual_outcome * 100
        else:
            # No valid outcome data
            return False
        
        # Simple success criteria - can be made more sophisticated
        if predicted_signal == 'BUY':
            return price_change_percent > 0
        elif predicted_signal == 'SELL':
            return price_change_percent < 0
        else:  # HOLD
            return abs(price_change_percent) < 2  # Less than 2% movement
    
    def _calculate_accuracy_progression(self, predictions: List[Dict]) -> List[float]:
        """Calculate accuracy progression over time"""
        if not predictions:
            return []
        
        # Sort by timestamp
        sorted_predictions = sorted(predictions, key=lambda x: x['timestamp'])
        
        accuracy_progression = []
        for i in range(1, len(sorted_predictions) + 1):
            subset = sorted_predictions[:i]
            completed = [p for p in subset if p['status'] == 'completed']
            
            if completed:
                successful = sum(1 for p in completed if self._is_successful_prediction(p))
                accuracy = successful / len(completed)
                accuracy_progression.append(accuracy)
            else:
                accuracy_progression.append(0)
        
        return accuracy_progression
    
    def _calculate_confidence_progression(self, predictions: List[Dict]) -> List[float]:
        """Calculate confidence progression over time"""
        if not predictions:
            return []
        
        sorted_predictions = sorted(predictions, key=lambda x: x['timestamp'])
        
        confidence_progression = []
        for i in range(1, len(sorted_predictions) + 1):
            subset = sorted_predictions[:i]
            avg_confidence = np.mean([p['prediction'].get('confidence', 0) for p in subset])
            confidence_progression.append(avg_confidence)
        
        return confidence_progression
    
    def _calculate_model_improvement(self, metrics: List[Dict]) -> Dict:
        """Calculate model improvement metrics"""
        if len(metrics) < 2:
            return {
                'improvement': 0, 
                'trend': 'insufficient_data',
                'first_accuracy': 0,
                'last_accuracy': 0,
                'total_training_sessions': len(metrics)
            }
        
        sorted_metrics = sorted(metrics, key=lambda x: x['timestamp'])
        
        first_accuracy = sorted_metrics[0].get('validation_accuracy', 0)
        last_accuracy = sorted_metrics[-1].get('validation_accuracy', 0)
        
        improvement = last_accuracy - first_accuracy
        trend = 'improving' if improvement > 0.01 else 'declining' if improvement < -0.01 else 'stable'
        
        return {
            'improvement': improvement,
            'trend': trend,
            'first_accuracy': first_accuracy,
            'last_accuracy': last_accuracy,
            'total_training_sessions': len(sorted_metrics)
        }
    
    def _calculate_trading_performance(self, performance: List[Dict]) -> Dict:
        """Calculate trading performance metrics"""
        if not performance:
            return {'total_trades': 0, 'success_rate': 0, 'average_confidence': 0}
        
        total_trades = sum(p['total_trades'] for p in performance)
        successful_trades = sum(p['successful_trades'] for p in performance)
        
        success_rate = successful_trades / total_trades if total_trades > 0 else 0
        avg_confidence = np.mean([p['model_confidence'] for p in performance])
        
        return {
            'total_trades': total_trades,
            'successful_trades': successful_trades,
            'success_rate': success_rate,
            'average_confidence': avg_confidence
        }
    
    def _get_daily_metrics(self, performance: List[Dict]) -> List[Dict]:
        """Get daily metrics for trend analysis"""
        return sorted(performance, key=lambda x: x['timestamp'])
    
    def _analyze_trends(self, performance: List[Dict]) -> Dict:
        """Analyze performance trends"""
        if len(performance) < 7:
            return {'trend': 'insufficient_data'}
        
        sorted_performance = sorted(performance, key=lambda x: x['timestamp'])
        
        # Calculate 7-day moving average of success rate
        success_rates = []
        for p in sorted_performance:
            if p['total_trades'] > 0:
                success_rates.append(p['successful_trades'] / p['total_trades'])
            else:
                success_rates.append(0)
        
        if len(success_rates) >= 7:
            recent_avg = np.mean(success_rates[-7:])
            earlier_avg = np.mean(success_rates[-14:-7]) if len(success_rates) >= 14 else np.mean(success_rates[:-7])
            
            trend = 'improving' if recent_avg > earlier_avg + 0.05 else 'declining' if recent_avg < earlier_avg - 0.05 else 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'trend': trend,
            'recent_success_rate': recent_avg if 'recent_avg' in locals() else 0,
            'earlier_success_rate': earlier_avg if 'earlier_avg' in locals() else 0
        }
    
    def _calculate_daily_accuracy(self, predictions: List[Dict]) -> float:
        """Calculate accuracy for a specific day"""
        completed = [p for p in predictions if p['status'] == 'completed']
        if not completed:
            return 0
        
        successful = sum(1 for p in completed if self._is_successful_prediction(p))
        return successful / len(completed)
    
    def _calculate_daily_confidence(self, predictions: List[Dict]) -> float:
        """Calculate average confidence for a specific day"""
        if not predictions:
            return 0
        
        return np.mean([p['prediction'].get('confidence', 0) for p in predictions])
    
    def _get_training_samples_for_date(self, date_str: str) -> int:
        """Get number of training samples for a specific date"""
        day_metrics = [
            m for m in self.model_metrics_history 
            if m['timestamp'].startswith(date_str)
        ]
        
        if day_metrics:
            return day_metrics[-1]['training_samples']
        return 0
    
    def _save_performance_history(self):
        """Save performance history to file"""
        try:
            with open(self.performance_file, 'w') as f:
                json.dump(self.performance_history, f, indent=2)
        except IOError as e:
            logger.error(f"Could not save performance history: {e}")
    
    def _save_prediction_history(self):
        """Save prediction history to file"""
        try:
            with open(self.predictions_file, 'w') as f:
                json.dump(self.prediction_history, f, indent=2)
        except IOError as e:
            logger.error(f"Could not save prediction history: {e}")
    
    def _save_model_metrics_history(self):
        """Save model metrics history to file"""
        try:
            with open(self.model_metrics_file, 'w') as f:
                json.dump(self.model_metrics_history, f, indent=2)
        except IOError as e:
            logger.error(f"Could not save model metrics history: {e}")
    
    def generate_sample_data(self, days: int = 30):
        """Generate sample data for testing (development use only)"""
        logger.info(f"Generating sample ML progression data for {days} days")
        
        # Clear existing data
        self.performance_history = []
        self.prediction_history = []
        self.model_metrics_history = []
        
        # Generate sample data
        for i in range(days):
            date = datetime.now() - timedelta(days=days-i-1)
            
            # Generate sample predictions
            for j in range(np.random.randint(3, 8)):  # 3-7 predictions per day
                prediction_id = f"SAMPLE_{date.strftime('%Y%m%d')}_{j}"
                
                # Random prediction data
                confidence = np.random.beta(2, 2)  # Beta distribution for realistic confidence
                signal = np.random.choice(['BUY', 'SELL', 'HOLD'], p=[0.4, 0.3, 0.3])
                
                prediction = {
                    'signal': signal,
                    'confidence': confidence,
                    'sentiment_score': np.random.uniform(-1, 1),
                    'pattern_strength': np.random.uniform(0, 1)
                }
                
                # Simulate outcome based on prediction quality (higher confidence = higher success rate)
                success_prob = 0.4 + (confidence * 0.4)  # 40-80% success rate based on confidence
                is_successful = np.random.random() < success_prob
                
                if signal == 'BUY':
                    price_change = np.random.uniform(0.5, 3.0) if is_successful else np.random.uniform(-2.0, 0.5)
                elif signal == 'SELL':
                    price_change = np.random.uniform(-3.0, -0.5) if is_successful else np.random.uniform(-0.5, 2.0)
                else:  # HOLD
                    price_change = np.random.uniform(-0.5, 0.5) if is_successful else np.random.uniform(-3.0, 3.0)
                
                actual_outcome = {
                    'price_change_percent': price_change,
                    'outcome_timestamp': (date + timedelta(hours=np.random.randint(1, 24))).isoformat()
                }
                
                prediction_record = {
                    'id': prediction_id,
                    'timestamp': (date + timedelta(hours=np.random.randint(9, 16))).isoformat(),
                    'symbol': np.random.choice(['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX']),
                    'prediction': prediction,
                    'actual_outcome': actual_outcome,
                    'status': 'completed'
                }
                
                self.prediction_history.append(prediction_record)
            
            # Generate daily performance
            day_predictions = [p for p in self.prediction_history if p['timestamp'].startswith(date.strftime('%Y-%m-%d'))]
            successful_trades = sum(1 for p in day_predictions if self._is_successful_prediction(p))
            
            daily_performance = {
                'date': date.strftime('%Y-%m-%d'),
                'timestamp': date.isoformat(),
                'performance': {
                    'successful_trades': successful_trades,
                    'total_trades': len(day_predictions),
                    'average_confidence': np.mean([p['prediction']['confidence'] for p in day_predictions]) if day_predictions else 0
                },
                'predictions_made': len(day_predictions),
                'accuracy_metrics': {
                    'accuracy': successful_trades / len(day_predictions) if day_predictions else 0,
                    'total_predictions': len(day_predictions),
                    'successful_predictions': successful_trades
                },
                'model_confidence': np.random.uniform(0.7, 0.9),
                'successful_trades': successful_trades,
                'total_trades': len(day_predictions)
            }
            
            self.performance_history.append(daily_performance)
            
            # Generate model metrics (every few days)
            if i % 3 == 0:  # Every 3 days
                model_metrics = {
                    'timestamp': date.isoformat(),
                    'model_type': 'ensemble',
                    'metrics': {
                        'validation_accuracy': min(0.95, 0.5 + (i / days) * 0.3 + np.random.normal(0, 0.05)),
                        'cross_validation_score': np.random.uniform(0.6, 0.85),
                        'training_samples': 50 + i * 2 + np.random.randint(-5, 5)
                    },
                    'training_samples': 50 + i * 2,
                    'validation_accuracy': min(0.95, 0.5 + (i / days) * 0.3 + np.random.normal(0, 0.05)),
                    'cross_validation_score': np.random.uniform(0.6, 0.85),
                    'feature_importance': {},
                    'model_version': f"1.{i//7}"
                }
                
                self.model_metrics_history.append(model_metrics)
        
        # Save all generated data
        self._save_performance_history()
        self._save_prediction_history()
        self._save_model_metrics_history()
        
        logger.info(f"Generated {len(self.prediction_history)} predictions, {len(self.performance_history)} daily records, and {len(self.model_metrics_history)} model metrics")

    def create_progression_chart(self, days: int = 30):
        """
        Create a Plotly chart showing ML model progression over time
        
        Args:
            days: Number of days to include in the chart
            
        Returns:
            plotly.graph_objects.Figure: The progression chart
        """
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # Get progression data
            progression_data = self.get_progression_summary(days=days)
            
            if not progression_data or not progression_data.get('daily_metrics'):
                # Return empty chart if no data
                fig = go.Figure()
                fig.add_annotation(
                    text="No ML progression data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, xanchor='center', yanchor='middle',
                    showarrow=False, font=dict(size=16, color="gray")
                )
                fig.update_layout(
                    title="ML Model Performance Progression",
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    height=400
                )
                return fig
            
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('Model Accuracy Over Time', 'Prediction Confidence', 
                               'Daily Predictions Count', 'Success Rate'),
                vertical_spacing=0.12,
                horizontal_spacing=0.1
            )
            
            daily_metrics = progression_data['daily_metrics']
            dates = [metric['date'] for metric in daily_metrics]
            
            # Extract metrics with correct key paths
            accuracies = [metric.get('accuracy_metrics', {}).get('accuracy', 0) for metric in daily_metrics]
            confidences = [metric.get('model_confidence', 0) for metric in daily_metrics]
            prediction_counts = [metric.get('predictions_made', 0) for metric in daily_metrics]
            success_rates = [
                metric['successful_trades'] / metric['total_trades'] if metric.get('total_trades', 0) > 0 else 0 
                for metric in daily_metrics
            ]
            
            # Add accuracy trend
            fig.add_trace(
                go.Scatter(
                    x=dates, y=accuracies,
                    mode='lines+markers',
                    name='Accuracy',
                    line=dict(color='#2E8B57', width=2),
                    marker=dict(size=4)
                ),
                row=1, col=1
            )
            
            # Add confidence trend
            fig.add_trace(
                go.Scatter(
                    x=dates, y=confidences,
                    mode='lines+markers',
                    name='Confidence',
                    line=dict(color='#4169E1', width=2),
                    marker=dict(size=4)
                ),
                row=1, col=2
            )
            
            # Add prediction count bars
            fig.add_trace(
                go.Bar(
                    x=dates, y=prediction_counts,
                    name='Predictions',
                    marker_color='#FFB347',
                    opacity=0.8
                ),
                row=2, col=1
            )
            
            # Add success rate
            fig.add_trace(
                go.Scatter(
                    x=dates, y=success_rates,
                    mode='lines+markers',
                    name='Success Rate',
                    line=dict(color='#32CD32', width=2),
                    marker=dict(size=4)
                ),
                row=2, col=2
            )
            
            # Update layout
            fig.update_layout(
                title={
                    'text': f'ML Model Performance Progression ({days} days)',
                    'x': 0.5,
                    'xanchor': 'center',
                    'font': {'size': 20, 'color': '#2c3e50'}
                },
                height=600,
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            # Update axes
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
            
            # Format y-axes
            fig.update_yaxes(title_text="Accuracy %", row=1, col=1, range=[0, 1])
            fig.update_yaxes(title_text="Confidence %", row=1, col=2, range=[0, 1])
            fig.update_yaxes(title_text="Count", row=2, col=1)
            fig.update_yaxes(title_text="Success Rate %", row=2, col=2, range=[0, 1])
            
            return fig
            
        except ImportError:
            logger.warning("Plotly not available for ML progression chart")
            # Return a simple text-based chart or None
            return None
        except Exception as e:
            logger.error(f"Error creating ML progression chart: {e}")
            return None
