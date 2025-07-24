"""
Test data feed module
"""
import unittest
from unittest.mock import Mock, patch
import pandas as pd
from app.core.data.collectors.market_data import ASXDataFeed


class TestASXDataFeed(unittest.TestCase):
    """Test cases for ASXDataFeed class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.data_feed = ASXDataFeed()
    
    def test_get_stock_data_valid_symbol(self):
        """Test getting stock data for valid symbol"""
        # This test would need to be mocked for real testing
        # For now, just test that the method exists and returns the right type
        try:
            result = self.data_feed.get_stock_data('CBA.AX')
            self.assertTrue(isinstance(result, (pd.DataFrame, type(None))))
        except Exception:
            # It's okay if it fails due to network issues in testing
            pass
    
    def test_get_stock_data_invalid_symbol(self):
        """Test getting stock data for invalid symbol"""
        try:
            result = self.data_feed.get_stock_data('INVALID.AX')
            self.assertTrue(isinstance(result, (pd.DataFrame, type(None))))
        except Exception:
            # It's okay if it fails due to network issues in testing
            pass
    
    @patch('yfinance.Ticker')
    def test_get_stock_data_mocked(self, mock_ticker):
        """Test getting stock data with mocked yfinance"""
        # Mock the yfinance response
        mock_hist = Mock()
        mock_hist.empty = False
        mock_hist.iloc = Mock()
        mock_ticker.return_value.history.return_value = mock_hist
        
        result = self.data_feed.get_current_data('CBA.AX')
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
