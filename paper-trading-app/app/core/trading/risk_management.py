#!/usr/bin/env python3
"""
Position Risk Assessor - ML-Based Recovery Prediction System
Predicts the likelihood and timeline of position recovery when trades go against you
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import sqlite3
import joblib
import json
import os
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class PositionRiskAssessor:
    """
    ML-powered position risk assessment and recovery prediction system
    
    Features:
    - Predicts recovery probability for losing positions
    - Estimates recovery timeframe
    - Calculates maximum adverse excursion (MAE)
    - Provides position sizing recommendations
    - Risk-adjusted exit strategies
    """
    
    def __init__(self, data_feed=None, ml_pipeline=None):
        self.data_feed = data_feed
        self.ml_pipeline = ml_pipeline
        self.models = {}
        self.scalers = {}
        self.model_metadata = {}
        
        # Initialize models directory
        self.models_dir = 'data/ml_models/position_risk'
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Recovery prediction parameters
        self.recovery_thresholds = {
            'quick_recovery': 0.5,    # 50% position recovery
            'full_recovery': 1.0,     # Break-even
            'profit_recovery': 1.02   # 2% profit
        }
        
        # Timeframe windows for analysis
        self.timeframes = {
            'immediate': 1,    # 1 day
            'short': 5,        # 5 days (1 week)
            'medium': 20,      # 20 days (1 month)
            'long': 60         # 60 days (3 months)
        }
        
        logger.info("Position Risk Assessor initialized")
    
    def assess_position_risk(self, symbol: str, entry_price: float, 
                           current_price: float, position_type: str = 'long',
                           entry_date: datetime = None) -> Dict:
        """
        Assess risk and predict recovery scenarios for a position
        
        Args:
            symbol: Stock symbol (e.g., 'CBA.AX')
            entry_price: Original entry price
            current_price: Current market price
            position_type: 'long' or 'short'
            entry_date: When position was entered
            
        Returns:
            Comprehensive risk assessment with recovery predictions
        """
        try:
            # Calculate current position metrics
            current_return = self._calculate_return(entry_price, current_price, position_type)
            
            # Get market context
            market_features = self._extract_market_features(symbol, current_price)
            
            # Get sentiment context
            sentiment_features = self._extract_sentiment_features(symbol)
            
            # Get technical analysis context
            technical_features = self._extract_technical_features(symbol, current_price)
            
            # Predict recovery scenarios
            recovery_predictions = self._predict_recovery_scenarios(
                symbol, entry_price, current_price, position_type,
                market_features, sentiment_features, technical_features
            )
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(
                entry_price, current_price, position_type, recovery_predictions
            )
            
            # Generate recommendations
            recommendations = self._generate_risk_recommendations(
                current_return, recovery_predictions, risk_metrics
            )
            
            return {
                'symbol': symbol,
                'entry_price': entry_price,
                'current_price': current_price,
                'position_type': position_type,
                'current_return_pct': round(current_return * 100, 2),
                'position_status': 'profitable' if current_return > 0 else 'underwater',
                'recovery_predictions': recovery_predictions,
                'risk_metrics': risk_metrics,
                'recommendations': recommendations,
                'market_context': market_features,
                'sentiment_context': sentiment_features,
                'technical_context': technical_features,
                'assessment_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in position risk assessment: {e}")
            return {'error': str(e)}
    
    def _calculate_return(self, entry_price: float, current_price: float, 
                         position_type: str) -> float:
        """Calculate position return based on position type"""
        if position_type.lower() == 'long':
            return (current_price - entry_price) / entry_price
        else:  # short position
            return (entry_price - current_price) / entry_price
    
    def _extract_market_features(self, symbol: str, current_price: float) -> Dict:
        """Extract market-based features for prediction"""
        try:
            # Get recent price data
            price_data = self.data_feed.get_historical_data(symbol, period='3mo')
            
            if price_data.empty:
                return self._get_default_market_features()
            
            # Calculate volatility features
            returns = price_data['Close'].pct_change().dropna()
            volatility_5d = returns.tail(5).std() * np.sqrt(252)
            volatility_20d = returns.tail(20).std() * np.sqrt(252)
            
            # Calculate support/resistance levels
            high_20d = price_data['High'].tail(20).max()
            low_20d = price_data['Low'].tail(20).min()
            
            # Volume analysis
            avg_volume_20d = price_data['Volume'].tail(20).mean()
            current_volume = price_data['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume_20d
            
            # Price position analysis
            price_range_20d = high_20d - low_20d
            price_position = (current_price - low_20d) / price_range_20d if price_range_20d > 0 else 0.5
            
            # RSI calculation
            rsi = self._calculate_rsi(price_data['Close'])
            
            return {
                'volatility_5d': volatility_5d,
                'volatility_20d': volatility_20d,
                'volatility_ratio': volatility_5d / volatility_20d if volatility_20d > 0 else 1.0,
                'resistance_distance': (high_20d - current_price) / current_price,
                'support_distance': (current_price - low_20d) / current_price,
                'price_position_in_range': price_position,
                'volume_ratio': volume_ratio,
                'rsi': rsi,
                'price_momentum_5d': returns.tail(5).mean(),
                'price_momentum_20d': returns.tail(20).mean()
            }
            
        except Exception as e:
            logger.warning(f"Error extracting market features: {e}")
            return self._get_default_market_features()
    
    def _extract_sentiment_features(self, symbol: str) -> Dict:
        """Extract sentiment-based features"""
        try:
            # Get recent sentiment data
            conn = sqlite3.connect(self.ml_pipeline.db_path if self.ml_pipeline else 'data/sentiment_history/sentiment_analysis.db')
            
            query = '''
                SELECT sentiment_score, confidence, news_count, event_score
                FROM sentiment_features 
                WHERE symbol = ? AND timestamp >= datetime('now', '-7 days')
                ORDER BY timestamp DESC
                LIMIT 20
            '''
            
            sentiment_df = pd.read_sql_query(query, conn, params=[symbol])
            conn.close()
            
            if sentiment_df.empty:
                return self._get_default_sentiment_features()
            
            # Calculate sentiment trends
            sentiment_mean = sentiment_df['sentiment_score'].mean()
            sentiment_trend = sentiment_df['sentiment_score'].diff().mean()
            confidence_mean = sentiment_df['confidence'].mean()
            news_volume = sentiment_df['news_count'].sum()
            
            return {
                'sentiment_score': sentiment_mean,
                'sentiment_trend': sentiment_trend,
                'confidence_level': confidence_mean,
                'news_volume_7d': news_volume,
                'sentiment_volatility': sentiment_df['sentiment_score'].std()
            }
            
        except Exception as e:
            logger.warning(f"Error extracting sentiment features: {e}")
            return self._get_default_sentiment_features()
    
    def _extract_technical_features(self, symbol: str, current_price: float) -> Dict:
        """Extract technical analysis features"""
        try:
            # Get price data for technical analysis
            price_data = self.data_feed.get_historical_data(symbol, period='6mo')
            
            if price_data.empty:
                return self._get_default_technical_features()
            
            # Moving averages
            ma_5 = price_data['Close'].rolling(5).mean().iloc[-1]
            ma_20 = price_data['Close'].rolling(20).mean().iloc[-1]
            ma_50 = price_data['Close'].rolling(50).mean().iloc[-1]
            
            # MACD
            macd_line, macd_signal = self._calculate_macd(price_data['Close'])
            
            # Bollinger Bands
            bb_upper, bb_lower = self._calculate_bollinger_bands(price_data['Close'])
            
            # ADX (trend strength)
            adx = self._calculate_adx(price_data)
            
            return {
                'ma5_distance': (current_price - ma_5) / current_price if ma_5 else 0,
                'ma20_distance': (current_price - ma_20) / current_price if ma_20 else 0,
                'ma50_distance': (current_price - ma_50) / current_price if ma_50 else 0,
                'macd_signal': 1 if macd_line > macd_signal else -1,
                'bb_position': (current_price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5,
                'trend_strength': adx,
                'price_trend': 1 if current_price > ma_20 else -1
            }
            
        except Exception as e:
            logger.warning(f"Error extracting technical features: {e}")
            return self._get_default_technical_features()
    
    def _predict_recovery_scenarios(self, symbol: str, entry_price: float, 
                                  current_price: float, position_type: str,
                                  market_features: Dict, sentiment_features: Dict,
                                  technical_features: Dict) -> Dict:
        """Predict recovery scenarios using ML models"""
        
        # Prepare feature vector
        features = {
            **market_features,
            **sentiment_features,
            **technical_features,
            'current_loss_pct': abs(self._calculate_return(entry_price, current_price, position_type)) * 100,
            'position_type': 1 if position_type.lower() == 'long' else -1
        }
        
        # Convert to DataFrame
        feature_df = pd.DataFrame([features])
        
        predictions = {}
        
        # Predict for each recovery threshold and timeframe
        for threshold_name, threshold_value in self.recovery_thresholds.items():
            predictions[threshold_name] = {}
            
            for timeframe_name, days in self.timeframes.items():
                try:
                    # Load or train model for this scenario
                    model_key = f"{threshold_name}_{timeframe_name}"
                    
                    if model_key not in self.models:
                        # Use default prediction if model not available
                        probability = self._estimate_recovery_probability(
                            features, threshold_value, days
                        )
                    else:
                        # Use trained model
                        probability = self.models[model_key].predict_proba(feature_df)[0, 1]
                    
                    predictions[threshold_name][timeframe_name] = {
                        'probability': round(probability, 3),
                        'confidence': 'medium',  # TODO: Calculate confidence intervals
                        'days': days
                    }
                    
                except Exception as e:
                    logger.warning(f"Error predicting {model_key}: {e}")
                    predictions[threshold_name][timeframe_name] = {
                        'probability': 0.5,
                        'confidence': 'low',
                        'days': days
                    }
        
        # Add maximum adverse excursion prediction
        predictions['max_adverse_excursion'] = self._predict_max_adverse_excursion(features)
        
        return predictions
    
    def _estimate_recovery_probability(self, features: Dict, threshold: float, days: int) -> float:
        """Estimate recovery probability using heuristic approach when ML model not available"""
        
        # Base probability based on market conditions
        base_prob = 0.4
        
        # Adjust based on volatility (higher volatility = higher recovery chance)
        vol_adjustment = min(0.2, features.get('volatility_20d', 0.2) * 0.5)
        
        # Adjust based on sentiment
        sentiment_adjustment = features.get('sentiment_score', 0) * 0.1
        
        # Adjust based on support/resistance
        support_adjustment = min(0.1, features.get('support_distance', 0) * 0.5)
        
        # Adjust based on timeframe (more time = higher probability)
        time_adjustment = min(0.2, days / 60 * 0.2)
        
        # Adjust based on current loss (smaller losses easier to recover)
        loss_pct = features.get('current_loss_pct', 5)
        loss_adjustment = max(-0.3, -loss_pct / 20 * 0.3)
        
        probability = base_prob + vol_adjustment + sentiment_adjustment + support_adjustment + time_adjustment + loss_adjustment
        
        return max(0.05, min(0.95, probability))
    
    def _predict_max_adverse_excursion(self, features: Dict) -> Dict:
        """Predict maximum adverse excursion (worst case scenario)"""
        
        # Base MAE as percentage of current loss
        current_loss = features.get('current_loss_pct', 5)
        base_mae = current_loss * 1.5  # Expect 50% worse than current
        
        # Adjust based on volatility
        volatility = features.get('volatility_20d', 0.2)
        volatility_mae = volatility * 30  # High vol can add significant MAE
        
        # Adjust based on support levels
        support_distance = features.get('support_distance', 0.05) * 100
        
        # Calculate confidence intervals
        mae_estimate = base_mae + volatility_mae
        mae_conservative = mae_estimate * 1.5
        mae_optimistic = mae_estimate * 0.7
        
        return {
            'estimated_mae_pct': round(mae_estimate, 2),
            'conservative_mae_pct': round(mae_conservative, 2),
            'optimistic_mae_pct': round(mae_optimistic, 2),
            'next_support_level': round(support_distance, 2),
            'confidence': 'medium'
        }
    
    def _calculate_risk_metrics(self, entry_price: float, current_price: float,
                              position_type: str, recovery_predictions: Dict) -> Dict:
        """Calculate comprehensive risk metrics"""
        
        current_return = self._calculate_return(entry_price, current_price, position_type)
        current_loss_pct = abs(current_return) * 100 if current_return < 0 else 0
        
        # Calculate expected recovery value
        recovery_5d = recovery_predictions.get('full_recovery', {}).get('short', {}).get('probability', 0.5)
        recovery_20d = recovery_predictions.get('full_recovery', {}).get('medium', {}).get('probability', 0.5)
        
        # Expected value calculation
        expected_recovery = (recovery_5d * 0.3 + recovery_20d * 0.7)
        
        # Risk-adjusted position size recommendation
        if current_loss_pct > 0:
            recommended_reduction = min(0.8, current_loss_pct / 10 * 0.2)  # Reduce position by 20% for every 10% loss
        else:
            recommended_reduction = 0
        
        # Time to recovery estimate
        if recovery_20d > 0.6:
            estimated_recovery_days = 15
        elif recovery_20d > 0.4:
            estimated_recovery_days = 30
        else:
            estimated_recovery_days = 60
        
        return {
            'current_loss_pct': round(current_loss_pct, 2),
            'expected_recovery_probability': round(expected_recovery, 3),
            'recommended_position_reduction': round(recommended_reduction, 2),
            'estimated_recovery_days': estimated_recovery_days,
            'risk_score': round(current_loss_pct * (1 - expected_recovery) * 10, 1),
            'max_acceptable_loss': round(current_loss_pct * 2, 1),  # 2x current loss as stop loss
            'breakeven_probability_30d': recovery_predictions.get('full_recovery', {}).get('medium', {}).get('probability', 0.5)
        }
    
    def _generate_risk_recommendations(self, current_return: float, 
                                     recovery_predictions: Dict, 
                                     risk_metrics: Dict) -> Dict:
        """Generate actionable risk management recommendations"""
        
        recommendations = {
            'primary_action': '',
            'position_management': [],
            'exit_strategy': [],
            'monitoring': [],
            'confidence_level': 'medium'
        }
        
        current_loss_pct = abs(current_return) * 100 if current_return < 0 else 0
        recovery_prob = risk_metrics.get('expected_recovery_probability', 0.5)
        
        # Primary action recommendation
        if current_loss_pct == 0:
            recommendations['primary_action'] = 'MONITOR'
        elif current_loss_pct < 3 and recovery_prob > 0.6:
            recommendations['primary_action'] = 'HOLD'
        elif current_loss_pct < 5 and recovery_prob > 0.4:
            recommendations['primary_action'] = 'REDUCE_POSITION'
        elif current_loss_pct < 10 and recovery_prob > 0.3:
            recommendations['primary_action'] = 'CONSIDER_EXIT'
        else:
            recommendations['primary_action'] = 'EXIT_RECOMMENDED'
        
        # Position management recommendations
        if current_loss_pct > 2:
            # Ensure we have a numeric value for position reduction
            position_reduction = risk_metrics.get('recommended_position_reduction', 0)
            try:
                position_reduction = float(position_reduction) if position_reduction else 0
                reduction_pct = position_reduction * 100
                recommendations['position_management'].append(
                    f"Consider reducing position by {reduction_pct:.0f}%"
                )
            except (ValueError, TypeError):
                recommendations['position_management'].append("Consider reducing position size")
        
        if recovery_prob < 0.3:
            recommendations['position_management'].append("Position shows low recovery probability")
        
        # Exit strategy recommendations
        max_loss = risk_metrics.get('max_acceptable_loss', 10)
        try:
            max_loss = float(max_loss) if max_loss else 10
            recommendations['exit_strategy'].append(f"Set stop loss at {max_loss:.1f}% total loss")
        except (ValueError, TypeError):
            recommendations['exit_strategy'].append("Set stop loss at 10.0% total loss")
        
        if current_loss_pct > 5:
            recommendations['exit_strategy'].append("Consider staged exit over multiple days")
        
        # Monitoring recommendations
        recovery_days = risk_metrics.get('estimated_recovery_days', 30)
        try:
            recovery_days = int(float(recovery_days)) if recovery_days else 30
            recommendations['monitoring'].append(f"Monitor position for {recovery_days} days for recovery signs")
        except (ValueError, TypeError):
            recommendations['monitoring'].append("Monitor position for 30 days for recovery signs")
        recommendations['monitoring'].append("Watch for sentiment changes and technical breakouts")
        
        # Confidence level
        if recovery_prob > 0.6:
            recommendations['confidence_level'] = 'high'
        elif recovery_prob < 0.3:
            recommendations['confidence_level'] = 'low'
        
        return recommendations
    
    def train_recovery_models(self, symbol_list: List[str] = None, 
                            min_samples: int = 50) -> Dict:
        """
        Train ML models for recovery prediction using historical data
        
        This would analyze historical positions and their outcomes to train
        predictive models for recovery scenarios.
        """
        logger.info("Training recovery prediction models...")
        
        try:
            # Get historical trade data for training
            training_data = self._prepare_training_data(symbol_list)
            
            if len(training_data) < min_samples:
                logger.warning(f"Insufficient training data: {len(training_data)} samples (need {min_samples})")
                return {'error': 'Insufficient training data'}
            
            results = {}
            
            # Train models for each recovery scenario
            for threshold_name in self.recovery_thresholds.keys():
                for timeframe_name in self.timeframes.keys():
                    model_key = f"{threshold_name}_{timeframe_name}"
                    
                    # Prepare target variable
                    y = self._create_recovery_labels(
                        training_data, threshold_name, timeframe_name
                    )
                    
                    if len(y.unique()) < 2:
                        logger.warning(f"Skipping {model_key}: insufficient label variation")
                        continue
                    
                    # Train model
                    model_result = self._train_single_model(training_data, y, model_key)
                    results[model_key] = model_result
            
            logger.info(f"Successfully trained {len(results)} models")
            return {'success': True, 'models_trained': len(results), 'details': results}
            
        except Exception as e:
            logger.error(f"Error training recovery models: {e}")
            return {'error': str(e)}
    
    def _prepare_training_data(self, symbol_list: List[str]) -> pd.DataFrame:
        """Prepare historical data for model training"""
        # This would collect historical trade data and outcomes
        # For now, return empty DataFrame as placeholder
        logger.info("Preparing training data for recovery models...")
        return pd.DataFrame()
    
    def _create_recovery_labels(self, data: pd.DataFrame, threshold_name: str, 
                              timeframe_name: str) -> pd.Series:
        """Create target labels for recovery prediction"""
        # This would analyze historical outcomes to create labels
        # For now, return empty Series as placeholder
        return pd.Series(dtype='int64')
    
    def _train_single_model(self, X: pd.DataFrame, y: pd.Series, model_key: str) -> Dict:
        """Train a single recovery prediction model"""
        # Implementation placeholder
        return {'accuracy': 0.0, 'features': 0}
    
    # Utility functions for technical analysis
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50
    
    def _calculate_macd(self, prices: pd.Series) -> Tuple[float, float]:
        """Calculate MACD indicator"""
        ema12 = prices.ewm(span=12).mean()
        ema26 = prices.ewm(span=26).mean()
        macd_line = ema12 - ema26
        macd_signal = macd_line.ewm(span=9).mean()
        return macd_line.iloc[-1], macd_signal.iloc[-1]
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> Tuple[float, float]:
        """Calculate Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        return upper_band.iloc[-1], lower_band.iloc[-1]
    
    def _calculate_adx(self, price_data: pd.DataFrame, period: int = 14) -> float:
        """Calculate ADX (trend strength)"""
        try:
            high = price_data['High']
            low = price_data['Low']
            close = price_data['Close']
            
            plus_dm = high.diff()
            minus_dm = low.diff()
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm > 0] = 0
            
            tr = pd.concat([high - low, 
                           abs(high - close.shift(1)), 
                           abs(low - close.shift(1))], axis=1).max(axis=1)
            
            atr = tr.rolling(window=period).mean()
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.abs().rolling(window=period).mean() / atr)
            
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=period).mean()
            
            return adx.iloc[-1] if not adx.empty else 25
        except:
            return 25  # Default moderate trend strength
    
    # Default feature methods
    def _get_default_market_features(self) -> Dict:
        """Return default market features when data unavailable"""
        return {
            'volatility_5d': 0.2,
            'volatility_20d': 0.25,
            'volatility_ratio': 0.8,
            'resistance_distance': 0.05,
            'support_distance': 0.05,
            'price_position_in_range': 0.5,
            'volume_ratio': 1.0,
            'rsi': 50,
            'price_momentum_5d': 0.0,
            'price_momentum_20d': 0.0
        }
    
    def _get_default_sentiment_features(self) -> Dict:
        """Return default sentiment features when data unavailable"""
        return {
            'sentiment_score': 0.0,
            'sentiment_trend': 0.0,
            'confidence_level': 0.5,
            'news_volume_7d': 5,
            'sentiment_volatility': 0.1
        }
    
    def _get_default_technical_features(self) -> Dict:
        """Return default technical features when data unavailable"""
        return {
            'ma5_distance': 0.0,
            'ma20_distance': 0.0,
            'ma50_distance': 0.0,
            'macd_signal': 0,
            'bb_position': 0.5,
            'trend_strength': 25,
            'price_trend': 0
        }


# Example usage and testing
if __name__ == "__main__":
    # Example assessment
    assessor = PositionRiskAssessor()
    
    # Test scenario: Long position at $100, now at $99 (1% loss)
    result = assessor.assess_position_risk(
        symbol='CBA.AX',
        entry_price=100.00,
        current_price=99.00,
        position_type='long',
        entry_date=datetime.now() - timedelta(days=2)
    )
    
    print("Position Risk Assessment Example:")
    print("=" * 50)
    print(f"Symbol: {result.get('symbol')}")
    print(f"Current Return: {result.get('current_return_pct')}%")
    print(f"Position Status: {result.get('position_status')}")
    print(f"Risk Score: {result.get('risk_metrics', {}).get('risk_score')}")
    print(f"Primary Action: {result.get('recommendations', {}).get('primary_action')}")
    print(f"Recovery Probability (20d): {result.get('risk_metrics', {}).get('breakeven_probability_30d')}")
