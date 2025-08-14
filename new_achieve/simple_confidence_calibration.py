"""
Simplified Confidence Calibration System
Works with the current sentiment_scores database structure
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

class SimpleConfidenceCalibrator:
    """
    Simplified confidence calibration that works with available sentiment_scores data
    """
    
    def __init__(self, database_path: str = "morning_analysis.db"):
        self.database_path = database_path
        
        # Time-based confidence factors
        self.time_factors = {
            'market_open': 1.15,    # 10:00-11:00 AM (higher confidence)
            'mid_morning': 1.05,    # 11:00-12:00 PM  
            'lunch_hour': 0.85,     # 12:00-2:00 PM (lower confidence)
            'afternoon': 0.95,      # 2:00-4:00 PM
            'market_close': 1.10,   # 4:00-4:30 PM (higher confidence)
            'after_hours': 0.75     # After 4:30 PM (much lower confidence)
        }
        
        self.volatility_factors = {
            'low': 1.20,      # Low volatility
            'normal': 1.00,   # Normal volatility
            'high': 0.80,     # High volatility
            'extreme': 0.50   # Extreme volatility
        }
        
        self.sentiment_strength_factors = {
            'very_strong': 1.25,  # |sentiment| > 0.3
            'strong': 1.10,       # |sentiment| > 0.2
            'moderate': 1.00,     # |sentiment| > 0.1
            'weak': 0.85,         # |sentiment| > 0.05
            'very_weak': 0.70     # |sentiment| <= 0.05
        }
    
    def get_time_factor(self) -> Tuple[float, str]:
        """Get confidence adjustment factor based on current time"""
        current_time = datetime.now().time()
        hour = current_time.hour
        
        if 10 <= hour < 11:
            return self.time_factors['market_open'], 'market_open'
        elif 11 <= hour < 12:
            return self.time_factors['mid_morning'], 'mid_morning'
        elif 12 <= hour < 14:
            return self.time_factors['lunch_hour'], 'lunch_hour'
        elif 14 <= hour < 16:
            return self.time_factors['afternoon'], 'afternoon'
        elif 16 <= hour < 16.5:
            return self.time_factors['market_close'], 'market_close'
        else:
            return self.time_factors['after_hours'], 'after_hours'
    
    def get_volatility_factor(self, technical_score: float) -> Tuple[float, str]:
        """Estimate volatility factor from technical score"""
        abs_tech_score = abs(technical_score)
        
        if abs_tech_score < 0.1:
            return self.volatility_factors['low'], 'low'
        elif abs_tech_score < 0.3:
            return self.volatility_factors['normal'], 'normal'
        elif abs_tech_score < 0.5:
            return self.volatility_factors['high'], 'high'
        else:
            return self.volatility_factors['extreme'], 'extreme'
    
    def get_sentiment_strength_factor(self, sentiment_score: float) -> Tuple[float, str]:
        """Get confidence factor based on sentiment strength"""
        abs_sentiment = abs(sentiment_score)
        
        if abs_sentiment > 0.3:
            return self.sentiment_strength_factors['very_strong'], 'very_strong'
        elif abs_sentiment > 0.2:
            return self.sentiment_strength_factors['strong'], 'strong'
        elif abs_sentiment > 0.1:
            return self.sentiment_strength_factors['moderate'], 'moderate'
        elif abs_sentiment > 0.05:
            return self.sentiment_strength_factors['weak'], 'weak'
        else:
            return self.sentiment_strength_factors['very_weak'], 'very_weak'
    
    def get_historical_baseline(self, symbol: str = None) -> Dict:
        """Get historical sentiment baseline for calibration"""
        try:
            conn = sqlite3.connect(self.database_path)
            
            if symbol:
                query = "SELECT * FROM sentiment_scores WHERE symbol = ? ORDER BY timestamp DESC"
                params = (symbol,)
            else:
                query = "SELECT * FROM sentiment_scores ORDER BY timestamp DESC"
                params = ()
            
            df = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            if df.empty:
                return {'data_available': False}
            
            # Calculate baseline statistics
            baseline = {
                'data_available': True,
                'total_records': len(df),
                'avg_confidence': df['confidence'].mean(),
                'avg_sentiment': df['sentiment_score'].mean(),
                'sentiment_std': df['sentiment_score'].std(),
                'avg_technical': df['technical_score'].mean(),
                'last_updated': df['timestamp'].max()
            }
            
            return baseline
            
        except Exception as e:
            logger.error(f"Error getting historical baseline: {e}")
            return {'data_available': False, 'error': str(e)}
    
    def calibrate_confidence(self, 
                           original_confidence: float,
                           symbol: str,
                           sentiment_score: float,
                           technical_score: float) -> Dict:
        """Apply simplified confidence calibration"""
        try:
            # Get adjustment factors
            time_factor, time_status = self.get_time_factor()
            volatility_factor, vol_status = self.get_volatility_factor(technical_score)
            sentiment_factor, sentiment_status = self.get_sentiment_strength_factor(sentiment_score)
            
            # Get historical baseline for context
            baseline = self.get_historical_baseline(symbol)
            
            # Simple trend factor based on recent average if data available
            trend_factor = 1.0
            if baseline.get('data_available', False):
                if baseline['avg_sentiment'] > 0.1:
                    trend_factor = 1.05  # Slight boost in positive trend
                elif baseline['avg_sentiment'] < -0.1:
                    trend_factor = 0.95  # Slight reduction in negative trend
            
            # Calculate calibrated confidence
            calibrated_confidence = original_confidence * time_factor * volatility_factor * sentiment_factor * trend_factor
            
            # Ensure confidence stays within [0, 1] bounds
            calibrated_confidence = max(0.0, min(1.0, calibrated_confidence))
            
            # Calculate adjustment
            adjustment = calibrated_confidence - original_confidence
            
            return {
                'original_confidence': original_confidence,
                'calibrated_confidence': calibrated_confidence,
                'adjustment': adjustment,
                'adjustment_percent': (adjustment / original_confidence * 100) if original_confidence > 0 else 0,
                'factors': {
                    'time_factor': time_factor,
                    'time_status': time_status,
                    'volatility_factor': volatility_factor,
                    'volatility_status': vol_status,
                    'sentiment_factor': sentiment_factor,
                    'sentiment_status': sentiment_status,
                    'trend_factor': trend_factor
                },
                'baseline': baseline,
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
                'baseline': {},
                'calibration_applied': False,
                'error': str(e)
            }
    
    def get_current_market_conditions(self) -> Dict:
        """Get current market conditions for calibration display"""
        try:
            time_factor, time_status = self.get_time_factor()
            current_hour = datetime.now().hour
            
            # Get latest sentiment data
            conn = sqlite3.connect(self.database_path)
            df = pd.read_sql_query("SELECT * FROM sentiment_scores ORDER BY timestamp DESC LIMIT 10", conn)
            conn.close()
            
            conditions = {
                'current_time_factor': time_factor,
                'time_status': time_status,
                'current_hour': current_hour,
                'market_status': self._get_market_status(current_hour),
                'data_available': not df.empty
            }
            
            if not df.empty:
                conditions.update({
                    'avg_sentiment': df['sentiment_score'].mean(),
                    'avg_confidence': df['confidence'].mean(),
                    'avg_technical': df['technical_score'].mean(),
                    'sentiment_volatility': df['sentiment_score'].std(),
                    'last_update': df['timestamp'].iloc[0]
                })
            
            return conditions
            
        except Exception as e:
            logger.error(f"Error getting market conditions: {e}")
            return {'error': str(e), 'data_available': False}
    
    def _get_market_status(self, hour: int) -> str:
        """Get human-readable market status"""
        if 10 <= hour < 16:
            return "🟢 Market Hours"
        elif 16 <= hour < 17:
            return "🟡 Close Period"
        else:
            return "🔴 After Hours"

def test_simple_confidence_calibration():
    """Test the simplified confidence calibration system"""
    print("🎯 Testing Simplified Confidence Calibration System")
    print("=" * 60)
    
    calibrator = SimpleConfidenceCalibrator()
    
    # Test market conditions
    print("📊 Current Market Conditions:")
    conditions = calibrator.get_current_market_conditions()
    
    if conditions.get('data_available', False):
        print(f"Time Factor: {conditions['current_time_factor']:.2f} ({conditions['time_status']})")
        print(f"Market Status: {conditions['market_status']}")
        print(f"Average Sentiment: {conditions['avg_sentiment']:.3f}")
        print(f"Average Confidence: {conditions['avg_confidence']:.3f}")
        print(f"Sentiment Volatility: {conditions['sentiment_volatility']:.3f}")
    else:
        print("Limited data available - using time-based factors only")
        print(f"Time Factor: {conditions['current_time_factor']:.2f} ({conditions['time_status']})")
        print(f"Market Status: {conditions['market_status']}")
    
    # Test calibration examples
    print(f"\n🧪 Calibration Examples:")
    test_cases = [
        {'symbol': 'CBA.AX', 'confidence': 0.75, 'sentiment': 0.20, 'technical': 0.15},
        {'symbol': 'WBC.AX', 'confidence': 0.60, 'sentiment': -0.10, 'technical': 0.05},
        {'symbol': 'ANZ.AX', 'confidence': 0.85, 'sentiment': 0.35, 'technical': -0.05}
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = calibrator.calibrate_confidence(
            case['confidence'], case['symbol'], case['sentiment'], case['technical']
        )
        
        print(f"\n  {i}. {case['symbol']}")
        print(f"     Original: {result['original_confidence']:.3f}")
        print(f"     Calibrated: {result['calibrated_confidence']:.3f}")
        print(f"     Adjustment: {result['adjustment_percent']:+.1f}%")
        
        if result['calibration_applied']:
            factors = result['factors']
            print(f"     Factors: Time={factors['time_factor']:.2f}, Vol={factors['volatility_factor']:.2f}, Sent={factors['sentiment_factor']:.2f}")
    
    print("\n✅ Simplified Confidence Calibration Test Complete!")

if __name__ == "__main__":
    test_simple_confidence_calibration()
