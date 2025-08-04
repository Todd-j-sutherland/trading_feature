"""
Confidence Calibration System
Dynamically adjusts ML confidence based on market conditions and historical performance
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConfidenceCalibrator:
    """
    Advanced confidence calibration system that adjusts ML predictions based on:
    - Recent accuracy performance
    - Market volatility conditions
    - Time-of-day factors
    - News sentiment strength
    - Technical indicator alignment
    """
    
    def __init__(self, database_path: str = "morning_analysis.db"):
        self.database_path = database_path
        self.calibration_window = 30  # Days to look back for accuracy calculation
        
        # Base calibration factors
        self.time_factors = {
            'market_open': 1.15,    # 10:00-11:00 AM (higher confidence)
            'mid_morning': 1.05,    # 11:00-12:00 PM  
            'lunch_hour': 0.85,     # 12:00-2:00 PM (lower confidence)
            'afternoon': 0.95,      # 2:00-4:00 PM
            'market_close': 1.10,   # 4:00-4:30 PM (higher confidence)
            'after_hours': 0.75     # After 4:30 PM (much lower confidence)
        }
        
        self.volatility_factors = {
            'low': 1.20,      # VIX < 15 or low volatility
            'normal': 1.00,   # VIX 15-25
            'high': 0.80,     # VIX 25-35
            'extreme': 0.50   # VIX > 35
        }
        
        self.sentiment_strength_factors = {
            'very_strong': 1.25,  # |sentiment| > 0.5
            'strong': 1.10,       # |sentiment| > 0.3
            'moderate': 1.00,     # |sentiment| > 0.1
            'weak': 0.85,         # |sentiment| > 0.05
            'very_weak': 0.70     # |sentiment| <= 0.05
        }
    
    def get_recent_accuracy(self, symbol: str = None, days: int = None) -> Dict:
        """
        Calculate recent prediction accuracy for confidence calibration
        """
        if days is None:
            days = self.calibration_window
            
        try:
            conn = sqlite3.connect(self.database_path)
            
            # Query recent predictions with outcomes
            if symbol:
                query = """
                SELECT 
                    ef.symbol,
                    ef.confidence,
                    ef.sentiment_score,
                    ef.technical_score,
                    eo.actual_price_change,
                    ef.prediction_signal,
                    ef.timestamp,
                    CASE 
                        WHEN (ef.prediction_signal = 'BUY' AND eo.actual_price_change > 0) OR
                             (ef.prediction_signal = 'SELL' AND eo.actual_price_change < 0) 
                        THEN 1 ELSE 0 
                    END as correct_prediction
                FROM enhanced_features ef
                JOIN enhanced_outcomes eo ON ef.symbol = eo.symbol 
                    AND date(ef.timestamp) = date(eo.timestamp)
                WHERE ef.symbol = ? 
                    AND ef.timestamp > datetime('now', '-{} days')
                    AND eo.actual_price_change IS NOT NULL
                ORDER BY ef.timestamp DESC
                """.format(days)
                params = (symbol,)
            else:
                query = """
                SELECT 
                    ef.symbol,
                    ef.confidence,
                    ef.sentiment_score,
                    ef.technical_score,
                    eo.actual_price_change,
                    ef.prediction_signal,
                    ef.timestamp,
                    CASE 
                        WHEN (ef.prediction_signal = 'BUY' AND eo.actual_price_change > 0) OR
                             (ef.prediction_signal = 'SELL' AND eo.actual_price_change < 0) 
                        THEN 1 ELSE 0 
                    END as correct_prediction
                FROM enhanced_features ef
                JOIN enhanced_outcomes eo ON ef.symbol = eo.symbol 
                    AND date(ef.timestamp) = date(eo.timestamp)
                WHERE ef.timestamp > datetime('now', '-{} days')
                    AND eo.actual_price_change IS NOT NULL
                ORDER BY ef.timestamp DESC
                """.format(days)
                params = ()
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            if df.empty:
                return {
                    'total_predictions': 0,
                    'correct_predictions': 0,
                    'accuracy_rate': 0.0,
                    'confidence_accuracy_correlation': 0.0,
                    'high_confidence_accuracy': 0.0,
                    'calibration_factor': 1.0
                }
            
            # Calculate accuracy metrics
            total_predictions = len(df)
            correct_predictions = df['correct_prediction'].sum()
            accuracy_rate = correct_predictions / total_predictions if total_predictions > 0 else 0.0
            
            # Confidence-accuracy correlation
            confidence_accuracy_corr = df['confidence'].corr(df['correct_prediction'])
            if pd.isna(confidence_accuracy_corr):
                confidence_accuracy_corr = 0.0
            
            # High confidence accuracy (confidence > 0.7)
            high_conf_df = df[df['confidence'] > 0.7]
            high_conf_accuracy = (
                high_conf_df['correct_prediction'].mean() 
                if len(high_conf_df) > 0 else 0.0
            )
            
            # Calculate calibration factor based on recent performance
            if accuracy_rate > 0.7:
                calibration_factor = 1.2  # Boost confidence for high performers
            elif accuracy_rate > 0.6:
                calibration_factor = 1.1
            elif accuracy_rate > 0.5:
                calibration_factor = 1.0
            elif accuracy_rate > 0.4:
                calibration_factor = 0.9
            else:
                calibration_factor = 0.8  # Reduce confidence for poor performers
            
            return {
                'total_predictions': total_predictions,
                'correct_predictions': correct_predictions,
                'accuracy_rate': accuracy_rate,
                'confidence_accuracy_correlation': confidence_accuracy_corr,
                'high_confidence_accuracy': high_conf_accuracy,
                'calibration_factor': calibration_factor,
                'data_available': True
            }
            
        except Exception as e:
            logger.error(f"Error calculating recent accuracy: {e}")
            return {
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy_rate': 0.0,
                'confidence_accuracy_correlation': 0.0,
                'high_confidence_accuracy': 0.0,
                'calibration_factor': 1.0,
                'data_available': False,
                'error': str(e)
            }
    
    def get_time_factor(self) -> float:
        """
        Get confidence adjustment factor based on current time
        """
        current_time = datetime.now().time()
        hour = current_time.hour
        
        if 10 <= hour < 11:
            return self.time_factors['market_open']
        elif 11 <= hour < 12:
            return self.time_factors['mid_morning']
        elif 12 <= hour < 14:
            return self.time_factors['lunch_hour']
        elif 14 <= hour < 16:
            return self.time_factors['afternoon']
        elif 16 <= hour < 16.5:
            return self.time_factors['market_close']
        else:
            return self.time_factors['after_hours']
    
    def get_volatility_factor(self, technical_score: float) -> float:
        """
        Estimate volatility factor from technical score and market conditions
        """
        # Use technical score as a proxy for volatility
        abs_tech_score = abs(technical_score)
        
        if abs_tech_score < 0.2:
            return self.volatility_factors['low']
        elif abs_tech_score < 0.5:
            return self.volatility_factors['normal']
        elif abs_tech_score < 0.8:
            return self.volatility_factors['high']
        else:
            return self.volatility_factors['extreme']
    
    def get_sentiment_strength_factor(self, sentiment_score: float) -> float:
        """
        Get confidence factor based on sentiment strength
        """
        abs_sentiment = abs(sentiment_score)
        
        if abs_sentiment > 0.5:
            return self.sentiment_strength_factors['very_strong']
        elif abs_sentiment > 0.3:
            return self.sentiment_strength_factors['strong']
        elif abs_sentiment > 0.1:
            return self.sentiment_strength_factors['moderate']
        elif abs_sentiment > 0.05:
            return self.sentiment_strength_factors['weak']
        else:
            return self.sentiment_strength_factors['very_weak']
    
    def calibrate_confidence(self, 
                           original_confidence: float,
                           symbol: str,
                           sentiment_score: float,
                           technical_score: float) -> Dict:
        """
        Apply comprehensive confidence calibration
        """
        try:
            # Get recent accuracy for this symbol
            accuracy_data = self.get_recent_accuracy(symbol)
            
            # Get adjustment factors
            time_factor = self.get_time_factor()
            volatility_factor = self.get_volatility_factor(technical_score)
            sentiment_factor = self.get_sentiment_strength_factor(sentiment_score)
            accuracy_factor = accuracy_data['calibration_factor']
            
            # Calculate calibrated confidence
            calibrated_confidence = original_confidence * time_factor * volatility_factor * sentiment_factor * accuracy_factor
            
            # Ensure confidence stays within [0, 1] bounds
            calibrated_confidence = max(0.0, min(1.0, calibrated_confidence))
            
            # Calculate confidence adjustment
            adjustment = calibrated_confidence - original_confidence
            
            return {
                'original_confidence': original_confidence,
                'calibrated_confidence': calibrated_confidence,
                'adjustment': adjustment,
                'adjustment_percent': (adjustment / original_confidence * 100) if original_confidence > 0 else 0,
                'factors': {
                    'time_factor': time_factor,
                    'volatility_factor': volatility_factor, 
                    'sentiment_factor': sentiment_factor,
                    'accuracy_factor': accuracy_factor
                },
                'accuracy_data': accuracy_data,
                'calibration_applied': True
            }
            
        except Exception as e:
            logger.error(f"Error in confidence calibration: {e}")
            return {
                'original_confidence': original_confidence,
                'calibrated_confidence': original_confidence,
                'adjustment': 0.0,
                'adjustment_percent': 0.0,
                'factors': {},
                'accuracy_data': {},
                'calibration_applied': False,
                'error': str(e)
            }
    
    def get_calibration_summary(self) -> Dict:
        """
        Get overall calibration system performance summary
        """
        try:
            # Get accuracy for all symbols
            overall_accuracy = self.get_recent_accuracy()
            
            # Get per-symbol accuracy
            symbols = ['CBA', 'WBC', 'ANZ', 'NAB']  # ASX Big 4 banks
            symbol_accuracy = {}
            
            for symbol in symbols:
                symbol_accuracy[symbol] = self.get_recent_accuracy(symbol)
            
            # Current time factors
            current_time_factor = self.get_time_factor()
            current_hour = datetime.now().hour
            
            return {
                'overall_accuracy': overall_accuracy,
                'symbol_accuracy': symbol_accuracy,
                'current_time_factor': current_time_factor,
                'current_hour': current_hour,
                'calibration_window_days': self.calibration_window,
                'system_status': 'active',
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting calibration summary: {e}")
            return {
                'system_status': 'error',
                'error': str(e),
                'last_updated': datetime.now().isoformat()
            }

def test_confidence_calibration():
    """
    Test the confidence calibration system
    """
    print("🎯 Testing Confidence Calibration System")
    print("=" * 50)
    
    calibrator = ConfidenceCalibrator()
    
    # Test with sample data
    test_cases = [
        {
            'symbol': 'CBA',
            'original_confidence': 0.75,
            'sentiment_score': 0.25,
            'technical_score': 0.15
        },
        {
            'symbol': 'WBC', 
            'original_confidence': 0.60,
            'sentiment_score': -0.10,
            'technical_score': 0.30
        },
        {
            'symbol': 'ANZ',
            'original_confidence': 0.85,
            'sentiment_score': 0.40,
            'technical_score': -0.05
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test_case['symbol']}")
        result = calibrator.calibrate_confidence(**test_case)
        
        print(f"Original Confidence: {result['original_confidence']:.3f}")
        print(f"Calibrated Confidence: {result['calibrated_confidence']:.3f}")
        print(f"Adjustment: {result['adjustment']:+.3f} ({result['adjustment_percent']:+.1f}%)")
        
        if result['calibration_applied']:
            factors = result['factors']
            print(f"Factors: Time={factors['time_factor']:.2f}, Vol={factors['volatility_factor']:.2f}, "
                  f"Sent={factors['sentiment_factor']:.2f}, Acc={factors['accuracy_factor']:.2f}")
    
    # Test calibration summary
    print(f"\n📊 Calibration System Summary")
    summary = calibrator.get_calibration_summary()
    
    print(f"System Status: {summary['system_status']}")
    print(f"Current Time Factor: {summary['current_time_factor']:.2f}")
    print(f"Calibration Window: {summary['calibration_window_days']} days")
    
    if summary['overall_accuracy']['data_available']:
        acc = summary['overall_accuracy']
        print(f"Overall Accuracy: {acc['accuracy_rate']:.1%} ({acc['correct_predictions']}/{acc['total_predictions']})")
    
    print("\n✅ Confidence Calibration Test Complete!")

if __name__ == "__main__":
    test_confidence_calibration()
