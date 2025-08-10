#!/usr/bin/env python3
"""
Unit Tests for Standardized Calculation Helper Functions
Provides tested, reusable calculation functions to prevent future bugs

Created based on return calculation bug fix findings (August 10, 2025)
"""

import pytest
import numpy as np
import math
from typing import Optional, Union
from decimal import Decimal, ROUND_HALF_UP

class CalculationHelpers:
    """Standardized calculation helper functions with comprehensive validation"""
    
    @staticmethod
    def calculate_return_percentage(entry_price: float, exit_price: float, 
                                  precision: int = 4) -> float:
        """
        Standard return percentage calculation for the entire system
        
        Args:
            entry_price: Initial price
            exit_price: Final price
            precision: Decimal places for rounding (default 4 to match database)
            
        Returns:
            Return percentage (e.g., 5.0 for 5%)
            
        Raises:
            ValueError: If entry_price is <= 0
        """
        if entry_price <= 0:
            raise ValueError(f"Entry price must be positive, got {entry_price}")
        
        if exit_price < 0:
            raise ValueError(f"Exit price cannot be negative, got {exit_price}")
        
        return_decimal = (exit_price - entry_price) / entry_price
        return_percentage = return_decimal * 100
        
        return round(return_percentage, precision)
    
    @staticmethod
    def calculate_return_percentage_safe(entry_price: float, exit_price: float,
                                       default: float = 0.0, precision: int = 4) -> float:
        """
        Safe return percentage calculation with error handling
        
        Args:
            entry_price: Initial price
            exit_price: Final price  
            default: Value to return if calculation fails
            precision: Decimal places for rounding
            
        Returns:
            Return percentage or default value
        """
        try:
            if entry_price <= 0:
                return default
            if exit_price < 0:
                return default
            if math.isnan(entry_price) or math.isnan(exit_price):
                return default
            if math.isinf(entry_price) or math.isinf(exit_price):
                return default
                
            return CalculationHelpers.calculate_return_percentage(
                entry_price, exit_price, precision
            )
        except (ValueError, ZeroDivisionError, OverflowError):
            return default
    
    @staticmethod
    def calculate_absolute_return(entry_price: float, exit_price: float, 
                                position_size: float) -> float:
        """
        Calculate absolute dollar return
        
        Args:
            entry_price: Initial price per unit
            exit_price: Final price per unit
            position_size: Number of units or dollar amount
            
        Returns:
            Absolute return in dollars
        """
        return_percentage = CalculationHelpers.calculate_return_percentage(
            entry_price, exit_price
        )
        return (return_percentage / 100) * position_size
    
    @staticmethod
    def validate_return_percentage(return_pct: float, min_val: float = -50.0, 
                                 max_val: float = 50.0) -> bool:
        """
        Validate that return percentage is within reasonable bounds
        
        Args:
            return_pct: Return percentage to validate
            min_val: Minimum allowed return (-50% default for daily trading)
            max_val: Maximum allowed return (50% default for daily trading)
            
        Returns:
            True if valid, False otherwise
        """
        if math.isnan(return_pct) or math.isinf(return_pct):
            return False
        
        return min_val <= return_pct <= max_val
    
    @staticmethod
    def calculate_compound_return(returns: list) -> float:
        """
        Calculate compound return from a series of individual returns
        
        Args:
            returns: List of return percentages
            
        Returns:
            Compound return percentage
        """
        if not returns:
            return 0.0
        
        compound_factor = 1.0
        for ret in returns:
            compound_factor *= (1 + ret / 100)
        
        return (compound_factor - 1) * 100

class TestCalculationHelpers:
    """Test the standardized calculation helper functions"""
    
    def test_basic_return_calculation(self):
        """Test basic return percentage calculation"""
        result = CalculationHelpers.calculate_return_percentage(100.0, 105.0)
        assert result == 5.0
    
    def test_negative_return_calculation(self):
        """Test negative return calculation"""
        result = CalculationHelpers.calculate_return_percentage(100.0, 95.0)
        assert result == -5.0
    
    def test_zero_return_calculation(self):
        """Test zero return calculation"""
        result = CalculationHelpers.calculate_return_percentage(100.0, 100.0)
        assert result == 0.0
    
    def test_precision_rounding(self):
        """Test precision rounding"""
        result = CalculationHelpers.calculate_return_percentage(123.456, 125.789, precision=2)
        expected = round(((125.789 - 123.456) / 123.456) * 100, 2)
        assert result == expected
    
    def test_high_precision_calculation(self):
        """Test high precision calculation"""
        result = CalculationHelpers.calculate_return_percentage(
            100.123456789, 101.987654321, precision=6
        )
        assert isinstance(result, float)
        assert len(str(result).split('.')[-1]) <= 6
    
    def test_invalid_entry_price_error(self):
        """Test error handling for invalid entry price"""
        with pytest.raises(ValueError, match="Entry price must be positive"):
            CalculationHelpers.calculate_return_percentage(0.0, 100.0)
        
        with pytest.raises(ValueError, match="Entry price must be positive"):
            CalculationHelpers.calculate_return_percentage(-10.0, 100.0)
    
    def test_invalid_exit_price_error(self):
        """Test error handling for invalid exit price"""
        with pytest.raises(ValueError, match="Exit price cannot be negative"):
            CalculationHelpers.calculate_return_percentage(100.0, -10.0)
    
    def test_safe_calculation_with_invalid_inputs(self):
        """Test safe calculation handles invalid inputs"""
        # Zero entry price
        result = CalculationHelpers.calculate_return_percentage_safe(0.0, 100.0)
        assert result == 0.0
        
        # Negative entry price
        result = CalculationHelpers.calculate_return_percentage_safe(-10.0, 100.0)
        assert result == 0.0
        
        # Negative exit price
        result = CalculationHelpers.calculate_return_percentage_safe(100.0, -10.0)
        assert result == 0.0
    
    def test_safe_calculation_with_nan(self):
        """Test safe calculation handles NaN values"""
        result = CalculationHelpers.calculate_return_percentage_safe(float('nan'), 100.0)
        assert result == 0.0
        
        result = CalculationHelpers.calculate_return_percentage_safe(100.0, float('nan'))
        assert result == 0.0
    
    def test_safe_calculation_with_infinity(self):
        """Test safe calculation handles infinite values"""
        result = CalculationHelpers.calculate_return_percentage_safe(float('inf'), 100.0)
        assert result == 0.0
        
        result = CalculationHelpers.calculate_return_percentage_safe(100.0, float('inf'))
        assert result == 0.0
    
    def test_safe_calculation_custom_default(self):
        """Test safe calculation with custom default value"""
        result = CalculationHelpers.calculate_return_percentage_safe(
            0.0, 100.0, default=-999.0
        )
        assert result == -999.0
    
    def test_absolute_return_calculation(self):
        """Test absolute return calculation"""
        result = CalculationHelpers.calculate_absolute_return(100.0, 105.0, 1000.0)
        assert result == 50.0  # 5% of $1000 = $50
    
    def test_return_validation_valid_range(self):
        """Test return validation within valid range"""
        assert CalculationHelpers.validate_return_percentage(5.0) == True
        assert CalculationHelpers.validate_return_percentage(-5.0) == True
        assert CalculationHelpers.validate_return_percentage(0.0) == True
        assert CalculationHelpers.validate_return_percentage(25.0) == True
        assert CalculationHelpers.validate_return_percentage(-25.0) == True
    
    def test_return_validation_invalid_range(self):
        """Test return validation outside valid range"""
        assert CalculationHelpers.validate_return_percentage(60.0) == False
        assert CalculationHelpers.validate_return_percentage(-60.0) == False
        assert CalculationHelpers.validate_return_percentage(float('nan')) == False
        assert CalculationHelpers.validate_return_percentage(float('inf')) == False
    
    def test_return_validation_custom_range(self):
        """Test return validation with custom range"""
        assert CalculationHelpers.validate_return_percentage(
            15.0, min_val=-10.0, max_val=10.0
        ) == False
        assert CalculationHelpers.validate_return_percentage(
            5.0, min_val=-10.0, max_val=10.0
        ) == True
    
    def test_compound_return_calculation(self):
        """Test compound return calculation"""
        returns = [5.0, -2.0, 3.0]  # 5%, -2%, 3%
        result = CalculationHelpers.calculate_compound_return(returns)
        
        # Manual calculation: (1.05 * 0.98 * 1.03) - 1 = 0.060594 = 6.0594%
        expected = (1.05 * 0.98 * 1.03 - 1) * 100
        assert abs(result - expected) < 0.0001
    
    def test_compound_return_empty_list(self):
        """Test compound return with empty list"""
        result = CalculationHelpers.calculate_compound_return([])
        assert result == 0.0
    
    def test_compound_return_single_value(self):
        """Test compound return with single value"""
        result = CalculationHelpers.calculate_compound_return([10.0])
        assert result == 10.0

class TestRealWorldScenarios:
    """Test with real-world scenarios from the bug report"""
    
    def test_qbe_sell_scenario(self):
        """Test QBE.AX SELL scenario from bug report"""
        entry_price = 22.90
        exit_price = 23.92
        
        result = CalculationHelpers.calculate_return_percentage(entry_price, exit_price)
        
        # Should be ~4.47% as corrected in bug fix
        assert abs(result - 4.47) < 0.1
        assert result != -0.02  # Should NOT be the buggy value
    
    def test_anz_buy_scenario(self):
        """Test ANZ.AX BUY scenario from bug report"""
        entry_price = 30.87
        exit_price = 29.55
        
        result = CalculationHelpers.calculate_return_percentage(entry_price, exit_price)
        
        # Should be ~-4.28% as corrected in bug fix
        assert abs(result - (-4.28)) < 0.1
        assert result != 0.02  # Should NOT be the buggy value
    
    def test_cba_successful_scenario(self):
        """Test CBA.AX successful scenario from bug report"""
        entry_price = 175.01
        exit_price = 177.91
        
        result = CalculationHelpers.calculate_return_percentage(entry_price, exit_price)
        
        # Should be ~1.66% (this was correct in original data)
        assert abs(result - 1.66) < 0.01
    
    def test_nab_buy_scenario(self):
        """Test NAB.AX BUY scenario from bug report"""
        entry_price = 38.44
        exit_price = 39.19
        
        result = CalculationHelpers.calculate_return_percentage(entry_price, exit_price)
        
        # Should be ~1.95% as corrected in bug fix
        assert abs(result - 1.95) < 0.1
        assert result != 0.03  # Should NOT be the buggy value

class TestEdgeCasesAndBoundaries:
    """Test edge cases and boundary conditions"""
    
    def test_very_small_prices(self):
        """Test with very small price values"""
        result = CalculationHelpers.calculate_return_percentage(0.001, 0.0011)
        assert result == 10.0  # 10% increase
    
    def test_very_large_prices(self):
        """Test with very large price values"""
        result = CalculationHelpers.calculate_return_percentage(1000000.0, 1050000.0)
        assert result == 5.0  # 5% increase
    
    def test_tiny_price_changes(self):
        """Test with tiny price changes"""
        result = CalculationHelpers.calculate_return_percentage(100.0, 100.01)
        assert result == 0.01  # 0.01% increase
    
    def test_extreme_gains(self):
        """Test extreme gain scenarios"""
        result = CalculationHelpers.calculate_return_percentage(10.0, 50.0)
        assert result == 400.0  # 400% gain
        
        # Should be flagged as invalid for daily trading
        assert not CalculationHelpers.validate_return_percentage(result)
    
    def test_extreme_losses(self):
        """Test extreme loss scenarios"""
        result = CalculationHelpers.calculate_return_percentage(100.0, 1.0)
        assert result == -99.0  # 99% loss
        
        # Should be flagged as invalid for daily trading  
        assert not CalculationHelpers.validate_return_percentage(result)

class TestDataTypeHandling:
    """Test different data type inputs"""
    
    def test_integer_inputs(self):
        """Test with integer inputs"""
        result = CalculationHelpers.calculate_return_percentage(100, 105)
        assert result == 5.0
        assert isinstance(result, float)
    
    def test_decimal_inputs(self):
        """Test with Decimal inputs"""
        entry = Decimal('100.00')
        exit_price = Decimal('105.00')
        
        result = CalculationHelpers.calculate_return_percentage(float(entry), float(exit_price))
        assert result == 5.0
    
    def test_string_numeric_conversion(self):
        """Test handling of string numeric inputs"""
        # This should be handled by the calling code, but test robustness
        with pytest.raises(TypeError):
            CalculationHelpers.calculate_return_percentage("100.0", "105.0")

class TestPerformanceAndScalability:
    """Test performance with various data sizes"""
    
    def test_batch_calculations(self):
        """Test batch calculation performance"""
        test_data = [(100.0 + i, 105.0 + i) for i in range(1000)]
        
        results = []
        for entry, exit_price in test_data:
            result = CalculationHelpers.calculate_return_percentage(entry, exit_price)
            results.append(result)
        
        # All should be approximately 5% (with minor variations due to base price)
        assert len(results) == 1000
        assert all(4.9 < r < 5.1 for r in results)

if __name__ == "__main__":
    # Run comprehensive tests
    pytest.main([__file__, "-v", "--tb=short", "--durations=10"])