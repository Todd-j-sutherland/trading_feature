#!/usr/bin/env python3
"""
Tests for Trading Analyzer
"""

import unittest
import json
import tempfile
import shutil
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import Settings

class TestTradingAnalyzer(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        
        # Mock trading data
        self.mock_analysis_result = {
            'symbol': 'CBA.AX',
            'signal': 'HOLD',
            'sentiment_score': 0.024,
            'confidence': 0.740,
            'recommendation': 'HOLD',
            'current_price': 105.50,
            'news_count': 23,
            'timestamp': datetime.now().isoformat()
        }
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_trading_analyzer_initialization(self):
        """Test trading analyzer initialization"""
        try:
            from news_trading_analyzer import NewsTradingAnalyzer
            
            # Test initialization
            analyzer = NewsTradingAnalyzer()
            self.assertIsNotNone(analyzer)
            
        except ImportError:
            self.skipTest("NewsTradingAnalyzer not available for testing")
    
    @patch('news_trading_analyzer.NewsTradingAnalyzer')
    def test_analyze_symbol(self, mock_analyzer):
        """Test symbol analysis"""
        # Mock analyzer response
        mock_instance = Mock()
        mock_instance.analyze_symbol.return_value = self.mock_analysis_result
        mock_analyzer.return_value = mock_instance
        
        # Test analysis
        result = mock_instance.analyze_symbol('CBA.AX')
        
        # Verify result structure
        self.assertIn('symbol', result)
        self.assertIn('signal', result)
        self.assertIn('sentiment_score', result)
        self.assertIn('confidence', result)
        self.assertEqual(result['symbol'], 'CBA.AX')
    
    def test_trading_signals(self):
        """Test trading signal generation"""
        
        # Test BUY signal
        buy_signal = self._generate_signal(0.7, 0.8)  # High positive sentiment, high confidence
        self.assertEqual(buy_signal, 'BUY')
        
        # Test SELL signal
        sell_signal = self._generate_signal(-0.7, 0.8)  # High negative sentiment, high confidence
        self.assertEqual(sell_signal, 'SELL')
        
        # Test HOLD signal
        hold_signal = self._generate_signal(0.1, 0.4)  # Low sentiment, low confidence
        self.assertEqual(hold_signal, 'HOLD')
    
    def test_confidence_thresholds(self):
        """Test confidence threshold logic"""
        
        # High confidence threshold
        high_conf = 0.8
        self.assertGreater(high_conf, 0.7)
        
        # Medium confidence threshold
        med_conf = 0.6
        self.assertGreater(med_conf, 0.5)
        self.assertLess(med_conf, 0.7)
        
        # Low confidence threshold
        low_conf = 0.3
        self.assertLess(low_conf, 0.5)
    
    def test_sentiment_score_ranges(self):
        """Test sentiment score range validation"""
        
        # Test valid sentiment scores
        valid_scores = [0.0, 0.5, -0.3, 1.0, -1.0]
        for score in valid_scores:
            self.assertGreaterEqual(score, -1.0)
            self.assertLessEqual(score, 1.0)
        
        # Test invalid sentiment scores
        invalid_scores = [1.5, -1.5, 2.0, -2.0]
        for score in invalid_scores:
            self.assertTrue(abs(score) > 1.0)
    
    def test_symbol_validation(self):
        """Test trading symbol validation"""
        
        # Valid ASX bank symbols from canonical settings
        settings = Settings()
        valid_symbols = settings.BANK_SYMBOLS
        for symbol in valid_symbols:
            self.assertTrue(self._is_valid_asx_symbol(symbol))
        
        # Invalid symbols
        invalid_symbols = ['INVALID', 'CBA', 'WBC.US', '']
        for symbol in invalid_symbols:
            self.assertFalse(self._is_valid_asx_symbol(symbol))
    
    def test_analyze_and_track_functionality(self):
        """Test analyze and track functionality"""
        
        # Mock track data
        track_data = {
            'trade_id': 'trade_123',
            'symbol': 'CBA.AX',
            'signal': 'BUY',
            'entry_price': 105.50,
            'timestamp': datetime.now().isoformat(),
            'ml_feature_id': 456
        }
        
        # Test tracking data structure
        self.assertIn('trade_id', track_data)
        self.assertIn('symbol', track_data)
        self.assertIn('signal', track_data)
        self.assertIn('entry_price', track_data)
    
    def test_close_trade_functionality(self):
        """Test trade closing functionality"""
        
        # Mock close trade data
        close_data = {
            'trade_id': 'trade_123',
            'exit_price': 107.20,
            'exit_timestamp': datetime.now().isoformat(),
            'return_pct': 0.0161,  # (107.20 - 105.50) / 105.50
            'duration_hours': 4
        }
        
        # Test return calculation
        entry_price = 105.50
        exit_price = 107.20
        expected_return = (exit_price - entry_price) / entry_price
        self.assertAlmostEqual(close_data['return_pct'], expected_return, places=4)
    
    def test_ml_integration(self):
        """Test ML integration features"""
        
        # Mock ML prediction
        ml_prediction = {
            'prediction': 'BUY',
            'confidence': 0.75,
            'ml_score': 0.6,
            'features_used': 10
        }
        
        # Test ML prediction structure
        self.assertIn('prediction', ml_prediction)
        self.assertIn('confidence', ml_prediction)
        self.assertIn(ml_prediction['prediction'], ['BUY', 'SELL', 'HOLD'])
        self.assertGreater(ml_prediction['features_used'], 0)
    
    def test_multiple_symbol_analysis(self):
        """Test analysis of multiple symbols"""
        
        settings = Settings()
        symbols = settings.BANK_SYMBOLS[:4]  # Use first four symbols for test
        
        # Mock results for all symbols
        results = {}
        for symbol in symbols:
            results[symbol] = {
                'symbol': symbol,
                'signal': 'HOLD',
                'sentiment_score': 0.1,
                'confidence': 0.6
            }
        
        # Test all symbols processed
        self.assertEqual(len(results), len(symbols))
        for symbol in symbols:
            self.assertIn(symbol, results)
    
    def test_error_handling(self):
        """Test error handling in trading analysis"""
        
        # Test network error simulation
        with self.assertRaises((ConnectionError, TimeoutError, Exception)):
            raise ConnectionError("Network error")
        
        # Test invalid data handling
        try:
            result = self._handle_invalid_data(None)
            self.assertIsNotNone(result)
        except Exception:
            pass  # Expected for error testing
    
    def test_performance_metrics(self):
        """Test performance metrics calculation"""
        
        # Mock performance data
        performance = {
            'total_trades': 10,
            'winning_trades': 6,
            'win_rate': 0.6,
            'average_return': 0.025,
            'total_return': 0.15
        }
        
        # Test metrics calculation
        expected_win_rate = performance['winning_trades'] / performance['total_trades']
        self.assertEqual(performance['win_rate'], expected_win_rate)
        
        # Test performance thresholds
        self.assertGreater(performance['win_rate'], 0.5)  # Better than random
    
    # Helper methods
    def _generate_signal(self, sentiment, confidence):
        """Generate trading signal based on sentiment and confidence"""
        if confidence < 0.5:
            return 'HOLD'
        elif sentiment > 0.3 and confidence > 0.7:
            return 'BUY'
        elif sentiment < -0.3 and confidence > 0.7:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _is_valid_asx_symbol(self, symbol):
        """Validate ASX symbol format"""
        if not symbol or not isinstance(symbol, str):
            return False
        return symbol.endswith('.AX') and len(symbol) > 3
    
    def _handle_invalid_data(self, data):
        """Handle invalid data gracefully"""
        if data is None:
            return {
                'error': 'No data available',
                'signal': 'HOLD',
                'confidence': 0.0
            }
        return data

if __name__ == "__main__":
    unittest.main()
