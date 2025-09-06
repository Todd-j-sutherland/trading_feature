#!/usr/bin/env python3
"""
Exit Strategy Engine Test Suite

Comprehensive testing for the exit strategy engine in an isolated environment.
Tests all exit conditions safely without affecting production.
"""

import unittest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the exit strategy module to path
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from exit_strategy_engine import (
    ExitStrategyEngine, Position, ExitSignal, ExitReason,
    TimeBasedExit, ProfitTargetExit, StopLossExit, 
    SentimentReversalExit, TechnicalBreakdownExit
)

class TestExitStrategyEngine(unittest.TestCase):
    """Test the complete exit strategy engine"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.engine = ExitStrategyEngine(db_path=":memory:")  # In-memory database for testing
        self.base_position = Position(
            symbol="CBA.AX",
            entry_price=120.00,
            current_price=120.00,
            entry_time=datetime.now() - timedelta(days=1),
            confidence=0.70,
            position_type='BUY',
            shares=100,
            market_context='NEUTRAL',
            original_prediction_id='test_123'
        )
        self.current_data = {
            'current_time': datetime.now(),
            'rsi': 50.0,
            'macd_signal': 'neutral',
            'price_trend': 'sideways'
        }
    
    def test_engine_initialization(self):
        """Test engine initializes correctly"""
        self.assertIsInstance(self.engine, ExitStrategyEngine)
        self.assertEqual(len(self.engine.exit_conditions), 5)
        
        # Check all exit condition types are present
        condition_types = [type(c).__name__ for c in self.engine.exit_conditions]
        expected_types = ['StopLossExit', 'TechnicalBreakdownExit', 'ProfitTargetExit', 
                         'SentimentReversalExit', 'TimeBasedExit']
        
        for expected_type in expected_types:
            self.assertIn(expected_type, condition_types)
    
    def test_no_exit_conditions_triggered(self):
        """Test when no exit conditions are triggered"""
        result = self.engine.evaluate_position_exit(self.base_position, self.current_data)
        
        self.assertFalse(result.should_exit)
        self.assertEqual(result.reason, ExitReason.MANUAL)
        self.assertEqual(result.urgency, 1)

class TestTimeBasedExit(unittest.TestCase):
    """Test time-based exit conditions"""
    
    def setUp(self):
        self.time_exit = TimeBasedExit(max_hold_days=5)
        self.current_data = {'current_time': datetime.now()}
    
    def test_time_limit_not_reached(self):
        """Test position within time limit"""
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=121.00,
            entry_time=datetime.now() - timedelta(days=2),  # 2 days old
            confidence=0.70, position_type='BUY', shares=100, market_context='NEUTRAL'
        )
        
        result = self.time_exit.evaluate(position, self.current_data)
        self.assertFalse(result.should_exit)
    
    def test_time_limit_reached(self):
        """Test position exceeds time limit"""
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=121.00,
            entry_time=datetime.now() - timedelta(days=6),  # 6 days old (exceeds 5-day limit)
            confidence=0.70, position_type='BUY', shares=100, market_context='NEUTRAL'
        )
        
        result = self.time_exit.evaluate(position, self.current_data)
        self.assertTrue(result.should_exit)
        self.assertEqual(result.reason, ExitReason.TIME_LIMIT)
        self.assertEqual(result.urgency, 4)
    
    def test_time_warning(self):
        """Test warning when approaching time limit"""
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=121.00,
            entry_time=datetime.now() - timedelta(days=4),  # 4 days old (80% of 5-day limit)
            confidence=0.70, position_type='BUY', shares=100, market_context='NEUTRAL'
        )
        
        result = self.time_exit.evaluate(position, self.current_data)
        self.assertFalse(result.should_exit)
        self.assertEqual(result.urgency, 2)

class TestProfitTargetExit(unittest.TestCase):
    """Test profit target exit conditions"""
    
    def setUp(self):
        self.profit_exit = ProfitTargetExit()
        self.current_data = {}
    
    def test_profit_target_calculation(self):
        """Test profit target calculation based on confidence"""
        # High confidence position (80%) should have higher profit target
        high_conf_position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=120.00,
            entry_time=datetime.now(), confidence=0.80, position_type='BUY', 
            shares=100, market_context='NEUTRAL'
        )
        
        # Calculate profit target
        target = self.profit_exit._calculate_profit_target(high_conf_position)
        self.assertGreater(target, 3.0)  # Should be > 3% for high confidence
        
        # Low confidence position (60%) should have lower profit target
        low_conf_position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=120.00,
            entry_time=datetime.now(), confidence=0.60, position_type='BUY',
            shares=100, market_context='NEUTRAL'
        )
        
        low_target = self.profit_exit._calculate_profit_target(low_conf_position)
        self.assertLess(low_target, target)  # Should be lower than high confidence
    
    def test_profit_target_reached_buy_position(self):
        """Test profit target exit for BUY position"""
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=125.50,  # 4.58% profit
            entry_time=datetime.now(), confidence=0.70, position_type='BUY',
            shares=100, market_context='NEUTRAL'
        )
        
        result = self.profit_exit.evaluate(position, self.current_data)
        self.assertTrue(result.should_exit)
        self.assertEqual(result.reason, ExitReason.PROFIT_TARGET)
        self.assertEqual(result.urgency, 5)
    
    def test_profit_target_reached_sell_position(self):
        """Test profit target exit for SELL position"""
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=116.50,  # 2.92% profit on short
            entry_time=datetime.now(), confidence=0.70, position_type='SELL',
            shares=100, market_context='NEUTRAL'
        )
        
        result = self.profit_exit.evaluate(position, self.current_data)
        self.assertFalse(result.should_exit)  # Profit not quite at target yet
        
        # Test with larger profit
        position.current_price = 115.50  # 3.75% profit
        result = self.profit_exit.evaluate(position, self.current_data)
        self.assertTrue(result.should_exit)

class TestStopLossExit(unittest.TestCase):
    """Test stop-loss exit conditions"""
    
    def setUp(self):
        self.stop_loss_exit = StopLossExit()
        self.current_data = {}
    
    def test_stop_loss_calculation(self):
        """Test stop-loss calculation based on confidence and market context"""
        # High confidence in bullish market should have wider stop
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=120.00,
            entry_time=datetime.now(), confidence=0.85, position_type='BUY',
            shares=100, market_context='BULLISH'
        )
        
        wide_stop = self.stop_loss_exit._calculate_stop_loss(position)
        
        # Low confidence in bearish market should have tighter stop
        position.confidence = 0.55
        position.market_context = 'BEARISH'
        
        tight_stop = self.stop_loss_exit._calculate_stop_loss(position)
        
        self.assertGreater(wide_stop, tight_stop)
    
    def test_stop_loss_triggered_buy_position(self):
        """Test stop-loss exit for BUY position"""
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=116.50,  # -2.92% loss
            entry_time=datetime.now(), confidence=0.70, position_type='BUY',
            shares=100, market_context='NEUTRAL'
        )
        
        result = self.stop_loss_exit.evaluate(position, self.current_data)
        self.assertTrue(result.should_exit)
        self.assertEqual(result.reason, ExitReason.STOP_LOSS)
        self.assertEqual(result.urgency, 5)
    
    def test_stop_loss_warning(self):
        """Test stop-loss warning when approaching limit"""
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=118.00,  # -1.67% loss
            entry_time=datetime.now(), confidence=0.70, position_type='BUY',
            shares=100, market_context='NEUTRAL'
        )
        
        result = self.stop_loss_exit.evaluate(position, self.current_data)
        self.assertFalse(result.should_exit)  # Warning, not exit yet
        self.assertEqual(result.urgency, 3)

class TestTechnicalBreakdownExit(unittest.TestCase):
    """Test technical breakdown exit conditions"""
    
    def setUp(self):
        self.technical_exit = TechnicalBreakdownExit()
    
    def test_technical_breakdown_buy_position(self):
        """Test technical breakdown for BUY position"""
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=119.00,
            entry_time=datetime.now(), confidence=0.70, position_type='BUY',
            shares=100, market_context='NEUTRAL'
        )
        
        # Strong breakdown signals
        current_data = {
            'rsi': 85.0,  # Extremely overbought
            'macd_signal': 'bearish',
            'price_trend': 'strongly_bearish'
        }
        
        result = self.technical_exit.evaluate(position, current_data)
        self.assertTrue(result.should_exit)
        self.assertEqual(result.reason, ExitReason.TECHNICAL_BREAKDOWN)
        self.assertEqual(result.urgency, 4)
    
    def test_technical_warning(self):
        """Test technical warning with single signal"""
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=119.00,
            entry_time=datetime.now(), confidence=0.70, position_type='BUY',
            shares=100, market_context='NEUTRAL'
        )
        
        # Single warning signal
        current_data = {
            'rsi': 75.0,  # Overbought but not extreme
            'macd_signal': 'bearish',
            'price_trend': 'sideways'
        }
        
        result = self.technical_exit.evaluate(position, current_data)
        self.assertFalse(result.should_exit)  # Warning only
        self.assertEqual(result.urgency, 3)

class TestIntegrationScenarios(unittest.TestCase):
    """Test complete integration scenarios"""
    
    def setUp(self):
        self.engine = ExitStrategyEngine(db_path=":memory:")
    
    def test_multiple_exit_conditions_priority(self):
        """Test that highest priority exit condition wins"""
        # Position with both stop-loss AND time limit triggered
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=115.00,  # -4.17% loss (stop-loss)
            entry_time=datetime.now() - timedelta(days=6),  # 6 days old (time limit)
            confidence=0.70, position_type='BUY', shares=100, market_context='NEUTRAL'
        )
        
        current_data = {
            'current_time': datetime.now(),
            'rsi': 50.0,
            'macd_signal': 'neutral',
            'price_trend': 'sideways'
        }
        
        result = self.engine.evaluate_position_exit(position, current_data)
        
        # Stop-loss should win (priority 5 vs time limit priority 2)
        self.assertTrue(result.should_exit)
        self.assertEqual(result.reason, ExitReason.STOP_LOSS)
        self.assertEqual(result.urgency, 5)
    
    def test_profitable_position_exit(self):
        """Test exit of profitable position at profit target"""
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=125.50,  # 4.58% profit
            entry_time=datetime.now() - timedelta(days=2),
            confidence=0.75, position_type='BUY', shares=100, market_context='BULLISH'
        )
        
        current_data = {
            'current_time': datetime.now(),
            'rsi': 60.0,
            'macd_signal': 'bullish',
            'price_trend': 'bullish'
        }
        
        result = self.engine.evaluate_position_exit(position, current_data)
        
        self.assertTrue(result.should_exit)
        self.assertEqual(result.reason, ExitReason.PROFIT_TARGET)
    
    def test_multiple_positions_evaluation(self):
        """Test evaluation of multiple positions"""
        positions = [
            # Profitable position
            Position("CBA.AX", 120.00, 125.00, datetime.now() - timedelta(days=1),
                    0.75, 'BUY', 100, 'BULLISH'),
            
            # Loss position
            Position("WBC.AX", 25.00, 23.50, datetime.now() - timedelta(days=2),
                    0.65, 'BUY', 200, 'NEUTRAL'),
            
            # Old position
            Position("ANZ.AX", 28.00, 28.20, datetime.now() - timedelta(days=6),
                    0.70, 'BUY', 150, 'NEUTRAL')
        ]
        
        current_data = {
            'current_time': datetime.now(),
            'rsi': 55.0,
            'macd_signal': 'neutral',
            'price_trend': 'sideways'
        }
        
        results = self.engine.evaluate_all_positions(positions, current_data)
        
        self.assertEqual(len(results), 3)
        
        # Check that at least one position should exit
        exit_signals = [signal for _, signal in results if signal.should_exit]
        self.assertGreater(len(exit_signals), 0)

class TestExitScenarios(unittest.TestCase):
    """Test realistic exit scenarios"""
    
    def setUp(self):
        self.engine = ExitStrategyEngine(db_path=":memory:")
    
    def test_scenario_quick_profit_exit(self):
        """Scenario: Quick profit on high-confidence trade"""
        position = Position(
            symbol="CBA.AX", entry_price=120.00, current_price=125.50,  # 4.58% profit
            entry_time=datetime.now() - timedelta(hours=6),  # Same day
            confidence=0.85, position_type='BUY', shares=100, market_context='BULLISH'
        )
        
        current_data = {
            'current_time': datetime.now(),
            'rsi': 70.0,
            'macd_signal': 'bullish',
            'price_trend': 'bullish'
        }
        
        result = self.engine.evaluate_position_exit(position, current_data)
        
        self.assertTrue(result.should_exit)
        self.assertEqual(result.reason, ExitReason.PROFIT_TARGET)
        print(f"✅ Quick profit scenario: {result.details}")
    
    def test_scenario_stop_loss_protection(self):
        """Scenario: Stop-loss protection in bearish market"""
        position = Position(
            symbol="WBC.AX", entry_price=25.00, current_price=24.25,  # -3% loss
            entry_time=datetime.now() - timedelta(days=1),
            confidence=0.60, position_type='BUY', shares=200, market_context='BEARISH'
        )
        
        current_data = {
            'current_time': datetime.now(),
            'rsi': 45.0,
            'macd_signal': 'bearish',
            'price_trend': 'bearish'
        }
        
        result = self.engine.evaluate_position_exit(position, current_data)
        
        self.assertTrue(result.should_exit)
        self.assertEqual(result.reason, ExitReason.STOP_LOSS)
        print(f"✅ Stop-loss protection scenario: {result.details}")
    
    def test_scenario_time_limit_cleanup(self):
        """Scenario: Time limit cleanup of stagnant position"""
        position = Position(
            symbol="ANZ.AX", entry_price=28.00, current_price=28.10,  # Small profit
            entry_time=datetime.now() - timedelta(days=5, hours=1),  # Just over 5 days
            confidence=0.65, position_type='BUY', shares=150, market_context='NEUTRAL'
        )
        
        current_data = {
            'current_time': datetime.now(),
            'rsi': 55.0,
            'macd_signal': 'neutral',
            'price_trend': 'sideways'
        }
        
        result = self.engine.evaluate_position_exit(position, current_data)
        
        self.assertTrue(result.should_exit)
        self.assertEqual(result.reason, ExitReason.TIME_LIMIT)
        print(f"✅ Time limit cleanup scenario: {result.details}")

def run_test_suite():
    """Run the complete test suite"""
    print("🧪 Running Exit Strategy Engine Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_classes = [
        TestExitStrategyEngine,
        TestTimeBasedExit,
        TestProfitTargetExit,
        TestStopLossExit,
        TestTechnicalBreakdownExit,
        TestIntegrationScenarios,
        TestExitScenarios
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n📊 Test Results:")
    print(f"   Tests Run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    if not result.failures and not result.errors:
        print(f"\n✅ All tests passed! Exit Strategy Engine is ready for integration.")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_test_suite()
    exit(0 if success else 1)
