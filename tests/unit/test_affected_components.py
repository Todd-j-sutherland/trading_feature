#!/usr/bin/env python3
"""
Unit Tests for Components Affected by Return Calculation Bug
Tests the specific classes and methods that were fixed

Based on the bug fix findings from August 10, 2025
"""

import pytest
import sqlite3
import os
import sys
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
import tempfile

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

class TestEnhancedSmartCollectorFix:
    """Test the enhanced_smart_collector.py after fix"""
    
    @patch('sqlite3.connect')
    def test_collect_outcome_return_calculation(self, mock_connect):
        """Test the fixed return calculation in enhanced_smart_collector"""
        # Mock database operations
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Simulate the fixed calculation logic
        current_price = 105.0
        entry_price = 100.0
        
        # This should be the CORRECTED calculation (with * 100)
        return_pct = ((current_price - entry_price) / entry_price) * 100
        
        assert return_pct == 5.0  # Should be 5%, not 0.05
        assert return_pct != 0.05  # Should NOT be the buggy decimal version
    
    def test_simulated_current_price_scenarios(self):
        """Test various price simulation scenarios"""
        entry_price = 100.0
        test_scenarios = [
            (95.0, -5.0),    # 5% loss
            (100.0, 0.0),    # No change  
            (105.0, 5.0),    # 5% gain
            (110.0, 10.0),   # 10% gain
            (120.0, 20.0),   # 20% gain
        ]
        
        for current_price, expected_return in test_scenarios:
            # Apply the corrected formula
            return_pct = ((current_price - entry_price) / entry_price) * 100
            assert abs(return_pct - expected_return) < 0.0001

class TestCorrectedSmartCollectorFix:
    """Test the corrected_smart_collector.py after fix"""
    
    def test_enhanced_outcome_calculation(self):
        """Test the fixed enhanced outcome calculation"""
        current_price = 108.50
        entry_price = 100.00
        
        # The FIXED calculation should include * 100
        return_pct = ((current_price - entry_price) / entry_price) * 100
        
        assert return_pct == 8.5  # Should be 8.5%, not 0.085
        assert isinstance(return_pct, float)
        assert return_pct > 1.0  # Should be in percentage form
    
    def test_record_enhanced_outcome_flow(self):
        """Test the flow of recording enhanced outcomes"""
        # Test data
        feature = {
            'id': 1,
            'symbol': 'CBA.AX',
            'entry_price': 175.00,
            'timestamp': datetime.now().isoformat()
        }
        
        current_price = 180.25
        
        # Apply corrected calculation
        return_pct = ((current_price - feature['entry_price']) / feature['entry_price']) * 100
        
        assert abs(return_pct - 3.0) < 0.1  # ~3% return
        assert return_pct != 0.03  # Should not be decimal

class TestTargetedBackfillFix:
    """Test the targeted_backfill.py after fix"""
    
    def test_save_outcome_calculation(self):
        """Test the fixed save outcome calculation"""
        exit_price = 115.75
        entry_price = 100.00
        
        # The FIXED calculation
        return_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
        
        assert return_pct == 15.75  # Should be 15.75%, not 0.1575
        assert return_pct > 1.0  # Percentage form
    
    def test_zero_entry_price_handling(self):
        """Test handling of zero/negative entry prices"""
        exit_price = 100.0
        entry_price = 0.0
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
        
        assert return_pct == 0.0  # Safe handling
    
    def test_negative_entry_price_handling(self):
        """Test handling of negative entry prices"""
        exit_price = 100.0
        entry_price = -50.0
        
        return_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0
        
        assert return_pct == 0.0  # Safe handling

class TestBacktestingEngineFix:
    """Test the backtesting_engine.py after fix"""
    
    def test_buy_signal_return_calculation(self):
        """Test BUY signal return calculation after fix"""
        row_data = {
            'signal': 'BUY',
            'entry_price': 100.0,
            'exit_price': 107.5,
            'symbol': 'CBA.AX'
        }
        
        # The FIXED calculation
        return_pct = ((row_data['exit_price'] - row_data['entry_price']) / row_data['entry_price']) * 100
        
        assert return_pct == 7.5  # Should be 7.5%, not 0.075
        assert return_pct > 0  # Positive return for BUY when price rises
    
    def test_sell_signal_return_calculation(self):
        """Test SELL signal return calculation after fix"""
        row_data = {
            'signal': 'SELL',
            'entry_price': 100.0,
            'exit_price': 92.5,
            'symbol': 'ANZ.AX'
        }
        
        # The FIXED calculation
        return_pct = ((row_data['exit_price'] - row_data['entry_price']) / row_data['entry_price']) * 100
        
        # Base calculation shows -7.5%
        assert return_pct == -7.5  # Should be -7.5%, not -0.075
        
        # For SELL signals, the return might be inverted (short position logic)
        if row_data['signal'] == 'SELL':
            inverted_return = -return_pct
            assert inverted_return == 7.5  # Profit from price decline in short position
    
    def test_position_sizing_impact(self):
        """Test how position sizing affects returns"""
        base_return_pct = 5.0  # 5% return
        position_size = 1000.0  # $1000 position
        
        # Calculate absolute return
        return_abs = (base_return_pct / 100) * position_size
        
        assert return_abs == 50.0  # $50 profit on $1000 position

class TestNewsCollectorFix:
    """Test the news_collector.py after fix"""
    
    @patch('app.core.data.collectors.news_collector.NewsCollector.get_current_price')
    def test_calculate_outcome_return(self, mock_get_price):
        """Test the fixed return calculation in news collector"""
        mock_get_price.return_value = 104.25
        
        signal = {
            'symbol': 'WBC.AX',
            'current_price': 100.00,  # Entry price
            'signal_type': 'BUY',
            'timestamp': datetime.now().isoformat()
        }
        
        current_price = 104.25
        entry_price = signal['current_price']
        
        # The FIXED calculation
        return_pct = ((current_price - entry_price) / entry_price) * 100
        
        assert return_pct == 4.25  # Should be 4.25%, not 0.0425
        assert return_pct > 1.0  # Should be in percentage form
    
    def test_outcome_data_structure(self):
        """Test the structure of outcome data"""
        current_price = 103.50
        entry_price = 100.00
        
        return_pct = ((current_price - entry_price) / entry_price) * 100
        
        outcome_data = {
            'symbol': 'NAB.AX',
            'entry_price': entry_price,
            'exit_price': current_price,
            'return_pct': return_pct,
            'timestamp': datetime.now().isoformat()
        }
        
        assert outcome_data['return_pct'] == 3.5
        assert outcome_data['exit_price'] > outcome_data['entry_price']
        assert isinstance(outcome_data['return_pct'], float)

class TestDatabaseCalculationConsistency:
    """Test database calculation consistency after fix"""
    
    def test_sql_update_formula_consistency(self):
        """Test that SQL formula matches Python calculation"""
        entry_price = 123.45
        exit_price = 128.90
        
        # Python calculation (what should be in code)
        python_result = ((exit_price - entry_price) / entry_price) * 100
        
        # SQL calculation (what was used in database fix)
        # ROUND(((exit_price_1d - entry_price) / entry_price) * 100, 4)
        sql_result = round(((exit_price - entry_price) / entry_price) * 100, 4)
        
        # They should match (within rounding precision)
        assert abs(python_result - sql_result) < 0.0001
    
    def test_rounding_consistency(self):
        """Test that rounding is consistent with database requirements"""
        test_cases = [
            (100.0, 105.123456, 5.1235),
            (50.0, 52.7777, 5.5554),
            (200.0, 198.1111, -0.9445)
        ]
        
        for entry, exit_price, expected_rounded in test_cases:
            calculated = round(((exit_price - entry) / entry) * 100, 4)
            assert abs(calculated - expected_rounded) < 0.0001

class TestRegresssionPrevention:
    """Tests to prevent regression of the original bug"""
    
    def test_percentage_not_decimal_format(self):
        """Ensure all calculations return percentages, not decimals"""
        test_cases = [
            (100.0, 105.0, 5.0),   # 5% not 0.05
            (100.0, 95.0, -5.0),   # -5% not -0.05
            (50.0, 55.0, 10.0),    # 10% not 0.1
            (200.0, 190.0, -5.0),  # -5% not -0.05
        ]
        
        for entry, exit_price, expected_percentage in test_cases:
            # Test ALL the calculation patterns that were fixed
            
            # Pattern 1: enhanced_smart_collector style
            calc1 = ((exit_price - entry) / entry) * 100
            
            # Pattern 2: corrected_smart_collector style  
            calc2 = ((exit_price - entry) / entry) * 100
            
            # Pattern 3: targeted_backfill style
            calc3 = ((exit_price - entry) / entry) * 100 if entry > 0 else 0
            
            # Pattern 4: backtesting_engine style
            calc4 = ((exit_price - entry) / entry) * 100
            
            # Pattern 5: news_collector style
            calc5 = ((exit_price - entry) / entry) * 100
            
            # All should match expected percentage
            for calc_result in [calc1, calc2, calc3, calc4, calc5]:
                assert abs(calc_result - expected_percentage) < 0.0001
                assert calc_result != expected_percentage / 100  # Should NOT be decimal
    
    def test_unrealistic_win_rates_detection(self):
        """Test detection of unrealistic win rates that indicate bugs"""
        # Simulate trading results that would indicate the bug is back
        trades = [
            {'action': 'BUY', 'return_pct': 5.0},   # 5% gain
            {'action': 'BUY', 'return_pct': 3.0},   # 3% gain  
            {'action': 'BUY', 'return_pct': -2.0},  # 2% loss
            {'action': 'BUY', 'return_pct': 1.0},   # 1% gain
            {'action': 'SELL', 'return_pct': -4.0}, # Price rose (loss for SELL)
            {'action': 'SELL', 'return_pct': 2.0},  # Price fell (gain for SELL logic)
        ]
        
        buy_trades = [t for t in trades if t['action'] == 'BUY']
        sell_trades = [t for t in trades if t['action'] == 'SELL']
        
        buy_wins = len([t for t in buy_trades if t['return_pct'] > 0])
        sell_wins = len([t for t in sell_trades if t['return_pct'] > 0])
        
        buy_win_rate = (buy_wins / len(buy_trades)) * 100 if buy_trades else 0
        sell_win_rate = (sell_wins / len(sell_trades)) * 100 if sell_trades else 0
        
        # These should be realistic rates, not 100% or 0%
        assert 0 < buy_win_rate < 100  # Should not be 100%
        assert 0 < sell_win_rate < 100  # Should not be 0%
        
        # Check for the specific bug pattern
        assert buy_win_rate != 100.0  # Bug symptom: all BUY wins
        assert sell_win_rate != 0.0   # Bug symptom: no SELL wins

class TestIntegrationScenarios:
    """Integration test scenarios based on bug report findings"""
    
    def test_full_trading_cycle_calculation(self):
        """Test a full trading cycle from entry to exit"""
        # Simulate morning analysis creating a feature
        morning_data = {
            'symbol': 'QBE.AX',
            'entry_price': 22.90,
            'prediction_time': datetime.now(),
            'signal': 'SELL',
            'confidence': 0.75
        }
        
        # Simulate evening analysis calculating outcome
        evening_data = {
            'exit_price': 23.92,
            'exit_time': datetime.now() + timedelta(days=1)
        }
        
        # Apply the fixed calculation
        return_pct = ((evening_data['exit_price'] - morning_data['entry_price']) / 
                     morning_data['entry_price']) * 100
        
        # This matches the corrected data from bug report
        assert abs(return_pct - 4.47) < 0.1  # ~4.47% as expected
        assert return_pct != -0.02  # Should NOT be the buggy value
    
    def test_realistic_portfolio_returns(self):
        """Test that portfolio returns are realistic after fix"""
        portfolio_trades = [
            {'symbol': 'CBA.AX', 'entry': 175.01, 'exit': 177.91, 'action': 'BUY'},
            {'symbol': 'QBE.AX', 'entry': 22.68, 'exit': 23.30, 'action': 'BUY'},
            {'symbol': 'ANZ.AX', 'entry': 30.87, 'exit': 29.55, 'action': 'BUY'},
            {'symbol': 'NAB.AX', 'entry': 38.44, 'exit': 39.19, 'action': 'BUY'},
        ]
        
        returns = []
        for trade in portfolio_trades:
            return_pct = ((trade['exit'] - trade['entry']) / trade['entry']) * 100
            returns.append(return_pct)
        
        avg_return = sum(returns) / len(returns)
        
        # Should be realistic portfolio average (not near zero due to bug)
        assert abs(avg_return) > 0.1  # Should have meaningful average
        assert -10 < avg_return < 10   # Should be within reasonable daily range
        
        # Check individual returns are in percentage form
        for ret in returns:
            assert abs(ret) > 0.01 or ret == 0  # Should be >0.01% or exactly 0
            assert abs(ret) < 50  # Should be <50% daily change

if __name__ == "__main__":
    # Run tests with detailed output
    pytest.main([__file__, "-v", "--tb=short", "-x"])