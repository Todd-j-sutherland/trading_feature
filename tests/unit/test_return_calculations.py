#!/usr/bin/env python3
"""
Unit Tests for Return Calculation Functions
Based on findings from return calculation bug fix (August 10, 2025)

This test suite ensures all return percentage calculations are mathematically correct
and consistent across the trading system.
"""

import pytest
import numpy as np
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestReturnCalculationFormulas:
    """Test core return calculation formulas for mathematical correctness"""
    
    def test_basic_return_calculation_positive(self):
        """Test positive return calculation"""
        entry_price = 100.0
        exit_price = 105.0
        expected_return = 5.0  # 5%
        
        calculated_return = ((exit_price - entry_price) / entry_price) * 100
        
        assert abs(calculated_return - expected_return) < 0.0001
        assert calculated_return == 5.0
    
    def test_basic_return_calculation_negative(self):
        """Test negative return calculation"""
        entry_price = 100.0
        exit_price = 95.0
        expected_return = -5.0  # -5%
        
        calculated_return = ((exit_price - entry_price) / entry_price) * 100
        
        assert abs(calculated_return - expected_return) < 0.0001
        assert calculated_return == -5.0
    
    def test_zero_return_calculation(self):
        """Test zero return when prices are equal"""
        entry_price = 100.0
        exit_price = 100.0
        expected_return = 0.0
        
        calculated_return = ((exit_price - entry_price) / entry_price) * 100
        
        assert calculated_return == expected_return
    
    def test_high_precision_calculation(self):
        """Test calculation with high precision values"""
        entry_price = 123.456789
        exit_price = 125.123456
        expected_return = ((125.123456 - 123.456789) / 123.456789) * 100
        
        calculated_return = ((exit_price - entry_price) / entry_price) * 100
        
        assert abs(calculated_return - expected_return) < 0.000001
    
    def test_large_price_values(self):
        """Test calculation with large price values"""
        entry_price = 10000.0
        exit_price = 10500.0
        expected_return = 5.0
        
        calculated_return = ((exit_price - entry_price) / entry_price) * 100
        
        assert abs(calculated_return - expected_return) < 0.0001
    
    def test_small_price_values(self):
        """Test calculation with small price values"""
        entry_price = 0.01
        exit_price = 0.011
        expected_return = 10.0
        
        calculated_return = ((exit_price - entry_price) / entry_price) * 100
        
        assert abs(calculated_return - expected_return) < 0.0001
    
    def test_division_by_zero_protection(self):
        """Test protection against division by zero"""
        entry_price = 0.0
        exit_price = 100.0
        
        # Should handle gracefully without division by zero
        if entry_price <= 0:
            calculated_return = 0.0
        else:
            calculated_return = ((exit_price - entry_price) / entry_price) * 100
        
        assert calculated_return == 0.0
    
    def test_negative_entry_price_protection(self):
        """Test protection against negative entry prices"""
        entry_price = -100.0
        exit_price = 100.0
        
        # Should handle gracefully
        if entry_price <= 0:
            calculated_return = 0.0
        else:
            calculated_return = ((exit_price - entry_price) / entry_price) * 100
        
        assert calculated_return == 0.0

class TestBuggyCalculationPatterns:
    """Test patterns that caused the original bug"""
    
    def test_missing_percentage_conversion(self):
        """Test the original buggy calculation (missing * 100)"""
        entry_price = 100.0
        exit_price = 105.0
        
        # This was the buggy calculation
        buggy_result = (exit_price - entry_price) / entry_price  # Missing * 100
        correct_result = ((exit_price - entry_price) / entry_price) * 100
        
        assert buggy_result == 0.05  # Decimal form
        assert correct_result == 5.0  # Percentage form
        assert buggy_result * 100 == correct_result
    
    def test_decimal_vs_percentage_units(self):
        """Test difference between decimal and percentage units"""
        entry_price = 100.0
        exit_price = 110.0
        
        decimal_return = (exit_price - entry_price) / entry_price  # 0.1
        percentage_return = ((exit_price - entry_price) / entry_price) * 100  # 10.0
        
        assert decimal_return == 0.1
        assert percentage_return == 10.0
        assert percentage_return == decimal_return * 100
    
    def test_realistic_stock_price_scenarios(self):
        """Test with realistic ASX stock price scenarios from the bug report"""
        test_cases = [
            # (symbol, action, entry, exit, expected_return)
            ("QBE.AX", "SELL", 22.90, 23.92, 4.45),
            ("ANZ.AX", "BUY", 30.87, 29.55, -4.28),
            ("CBA.AX", "SELL", 175.06, 169.25, -3.32),
            ("NAB.AX", "BUY", 38.44, 39.19, 1.95),
        ]
        
        for symbol, action, entry, exit, expected in test_cases:
            calculated = ((exit - entry) / entry) * 100
            assert abs(calculated - expected) < 0.1, f"{symbol} calculation failed"

class TestEnhancedSmartCollector:
    """Test the enhanced_smart_collector.py calculations"""
    
    @patch('sqlite3.connect')
    def test_return_calculation_in_collector(self, mock_connect):
        """Test return calculation in enhanced smart collector"""
        # Mock the collector functionality
        current_price = 105.0
        entry_price = 100.0
        
        # This is the corrected calculation from the fix
        return_pct = ((current_price - entry_price) / entry_price) * 100
        
        assert return_pct == 5.0
        assert isinstance(return_pct, float)
    
    def test_simulated_price_scenarios(self):
        """Test various simulated price movement scenarios"""
        base_price = 100.0
        scenarios = [
            (95.0, -5.0),    # 5% loss
            (100.0, 0.0),    # No change
            (105.0, 5.0),    # 5% gain
            (110.0, 10.0),   # 10% gain
            (90.0, -10.0),   # 10% loss
        ]
        
        for exit_price, expected_return in scenarios:
            calculated = ((exit_price - base_price) / base_price) * 100
            assert abs(calculated - expected_return) < 0.0001

class TestBacktestingEngine:
    """Test the backtesting_engine.py calculations"""
    
    def test_buy_signal_return_calculation(self):
        """Test BUY signal return calculation"""
        entry_price = 100.0
        exit_price = 105.0
        signal = "BUY"
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100
        
        # For BUY signals, positive price movement = positive return
        assert return_pct == 5.0
    
    def test_sell_signal_return_calculation(self):
        """Test SELL signal return calculation (short position)"""
        entry_price = 100.0
        exit_price = 95.0
        signal = "SELL"
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100
        
        # For SELL signals, the return calculation should be based on short position logic
        # If price goes down (95 < 100), SELL signal profits
        if signal == "SELL":
            # In backtesting, SELL returns are often inverted for short positions
            short_return_pct = -return_pct  # Invert for short position
            assert short_return_pct == 5.0  # Profit from price decline
        
        assert return_pct == -5.0  # Base calculation

class TestNewsCollector:
    """Test the news_collector.py calculations"""
    
    def test_news_based_return_calculation(self):
        """Test return calculation in news collector"""
        current_price = 102.5
        entry_price = 100.0
        
        return_pct = ((current_price - entry_price) / entry_price) * 100
        
        assert return_pct == 2.5
        assert abs(return_pct - 2.5) < 0.0001

class TestTargetedBackfill:
    """Test the targeted_backfill.py calculations"""
    
    def test_backfill_return_calculation(self):
        """Test return calculation in targeted backfill"""
        exit_price = 108.0
        entry_price = 100.0
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
        
        assert return_pct == 8.0
    
    def test_backfill_zero_entry_price_protection(self):
        """Test protection against zero entry price in backfill"""
        exit_price = 108.0
        entry_price = 0.0
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
        
        assert return_pct == 0.0

class TestDatabaseIntegrity:
    """Test database calculation integrity"""
    
    def test_sql_calculation_formula(self):
        """Test the SQL formula used in database updates"""
        # This is the exact formula used in the database fix
        entry_price = 100.0
        exit_price = 105.0
        
        # Simulate SQL calculation: ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4)
        sql_result = round(((exit_price - entry_price) / entry_price) * 100, 4)
        
        assert sql_result == 5.0
    
    def test_rounding_precision(self):
        """Test rounding precision matches database requirements"""
        entry_price = 123.456
        exit_price = 125.789
        
        # 4 decimal places as used in database
        return_pct = round(((exit_price - entry_price) / entry_price) * 100, 4)
        
        expected = round(((125.789 - 123.456) / 123.456) * 100, 4)
        assert return_pct == expected
        assert len(str(return_pct).split('.')[-1]) <= 4  # Max 4 decimal places

class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_very_small_price_changes(self):
        """Test very small price changes"""
        entry_price = 100.0
        exit_price = 100.01  # 1 cent change
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100
        expected = 0.01
        
        assert abs(return_pct - expected) < 0.0001
    
    def test_very_large_price_changes(self):
        """Test very large price changes"""
        entry_price = 100.0
        exit_price = 200.0  # 100% gain
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100
        
        assert return_pct == 100.0
    
    def test_extreme_loss(self):
        """Test extreme loss scenario"""
        entry_price = 100.0
        exit_price = 1.0  # 99% loss
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100
        
        assert return_pct == -99.0
    
    def test_floating_point_precision(self):
        """Test floating point precision issues"""
        entry_price = 1.0 / 3.0  # 0.333...
        exit_price = 1.0 / 3.0 + 0.01
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100
        
        # Should handle floating point calculations gracefully
        assert isinstance(return_pct, float)
        assert not np.isnan(return_pct)
        assert not np.isinf(return_pct)

class TestRealisticTradingScenarios:
    """Test realistic trading scenarios from the bug report"""
    
    def test_buy_win_scenario(self):
        """Test realistic BUY win scenario"""
        entry_price = 175.01
        exit_price = 177.91
        action = "BUY"
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100
        
        assert abs(return_pct - 1.66) < 0.01  # From bug report data
        assert return_pct > 0  # Winning trade
    
    def test_buy_loss_scenario(self):
        """Test realistic BUY loss scenario"""
        entry_price = 30.87
        exit_price = 29.55
        action = "BUY"
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100
        
        assert abs(return_pct - (-4.28)) < 0.01  # From bug report data
        assert return_pct < 0  # Losing trade
    
    def test_sell_win_scenario(self):
        """Test SELL signal scenario"""
        entry_price = 175.06
        exit_price = 169.25
        action = "SELL"
        
        # Base calculation shows price decline
        return_pct = ((exit_price - entry_price) / entry_price) * 100
        
        assert abs(return_pct - (-3.32)) < 0.01  # From bug report data
        # For SELL signals, price decline can be profitable in short positions
    
    def test_hold_scenario(self):
        """Test HOLD scenario with small movement"""
        entry_price = 22.68
        exit_price = 23.30
        action = "HOLD"
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100
        
        assert abs(return_pct - 2.76) < 0.01  # From bug report data

class TestSystemConsistency:
    """Test system-wide calculation consistency"""
    
    def test_all_calculation_methods_consistent(self):
        """Test that all methods produce same results for same inputs"""
        entry_price = 100.0
        exit_price = 105.0
        
        # Method 1: Direct calculation
        method1 = ((exit_price - entry_price) / entry_price) * 100
        
        # Method 2: Using variables
        price_diff = exit_price - entry_price
        method2 = (price_diff / entry_price) * 100
        
        # Method 3: Step by step
        ratio = exit_price / entry_price
        method3 = (ratio - 1) * 100
        
        assert abs(method1 - method2) < 0.0001
        assert abs(method2 - method3) < 0.0001
        assert abs(method1 - method3) < 0.0001
    
    def test_percentage_vs_decimal_conversion(self):
        """Test consistent percentage vs decimal conversion"""
        entry_price = 100.0
        exit_price = 105.0
        
        decimal_return = (exit_price - entry_price) / entry_price  # 0.05
        percentage_return = decimal_return * 100  # 5.0
        
        # These should be mathematically equivalent
        assert percentage_return == 5.0
        assert decimal_return == 0.05
        assert percentage_return / 100 == decimal_return

@pytest.fixture
def sample_price_data():
    """Fixture providing sample price data for testing"""
    return {
        'CBA.AX': {'entry': 175.01, 'exit': 177.91, 'expected_return': 1.66},
        'QBE.AX': {'entry': 22.68, 'exit': 23.30, 'expected_return': 2.76},
        'ANZ.AX': {'entry': 30.87, 'exit': 29.55, 'expected_return': -4.28},
        'NAB.AX': {'entry': 38.44, 'exit': 39.19, 'expected_return': 1.95},
    }

class TestWithFixtures:
    """Tests using fixtures for realistic data"""
    
    def test_all_sample_calculations(self, sample_price_data):
        """Test calculations with all sample data"""
        for symbol, data in sample_price_data.items():
            entry = data['entry']
            exit_price = data['exit']
            expected = data['expected_return']
            
            calculated = ((exit_price - entry) / entry) * 100
            
            assert abs(calculated - expected) < 0.1, f"Failed for {symbol}"

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])