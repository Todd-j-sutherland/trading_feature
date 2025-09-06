#!/usr/bin/env python3
"""
Test Suite for IG Markets Paper Trading System
Validates core functionality and ensures system integrity.
"""

import sys
import os
import unittest
import tempfile
import shutil
import json
from unittest.mock import Mock, patch, MagicMock

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from position_manager import PositionManager
from ig_markets_client import IGMarketsClient
from paper_trader import PaperTrader


class TestPositionManager(unittest.TestCase):
    """Test the position management system."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test.db')
        
        # Create test config
        self.config_path = os.path.join(self.test_dir, 'test_config.json')
        test_config = {
            "initial_balance": 10000.0,
            "max_position_size": 0.1,
            "risk_percentage": 0.02,
            "stop_loss_percentage": 0.05,
            "take_profit_percentage": 0.1
        }
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        self.pm = PositionManager(self.db_path, self.config_path)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_initial_balance(self):
        """Test initial balance is set correctly."""
        balance = self.pm.get_account_balance()
        self.assertEqual(balance, 10000.0)
    
    def test_position_limit_enforcement(self):
        """Test that only one position per symbol is allowed."""
        # Open first position
        result1 = self.pm.can_open_position('BTCUSD', 100.0)
        self.assertTrue(result1)
        
        # Record the position
        self.pm.add_position('BTCUSD', 'BUY', 50000.0, 0.002, 100.0)
        
        # Try to open second position on same symbol
        result2 = self.pm.can_open_position('BTCUSD', 100.0)
        self.assertFalse(result2)
        
        # Different symbol should be allowed
        result3 = self.pm.can_open_position('ETHUSD', 100.0)
        self.assertTrue(result3)
    
    def test_fund_availability_check(self):
        """Test fund availability checking."""
        # Should have funds for small position
        result1 = self.pm.can_open_position('BTCUSD', 100.0)
        self.assertTrue(result1)
        
        # Should not have funds for huge position
        result2 = self.pm.can_open_position('BTCUSD', 20000.0)
        self.assertFalse(result2)
    
    def test_position_size_calculation(self):
        """Test position size calculation."""
        size = self.pm.calculate_position_size(50000.0)  # BTC at $50k
        
        # Should be reasonable size (max 10% of balance)
        max_size = 10000.0 * 0.1 / 50000.0  # $1000 max
        self.assertLessEqual(size, max_size)
        self.assertGreater(size, 0)
    
    def test_position_closure(self):
        """Test position closure and balance update."""
        # Open position
        self.pm.add_position('BTCUSD', 'BUY', 50000.0, 0.002, 100.0)
        
        # Close with profit
        self.pm.close_position('BTCUSD', 51000.0, 102.0)
        
        # Balance should be updated
        balance = self.pm.get_account_balance()
        self.assertGreater(balance, 10000.0)


class TestIGMarketsClient(unittest.TestCase):
    """Test the IG Markets API client."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test config
        self.config_path = os.path.join(self.test_dir, 'test_config.json')
        test_config = {
            "api_key": "test_key",
            "username": "test_user",
            "password": "test_pass",
            "account_id": "test_account",
            "base_url": "https://demo-api.ig.com/gateway/deal",
            "cst_token": "test_cst",
            "x_security_token": "test_security"
        }
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    @patch('requests.get')
    def test_get_current_price(self, mock_get):
        """Test price fetching."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'snapshot': {
                'bid': 49000.0,
                'offer': 50000.0
            }
        }
        mock_get.return_value = mock_response
        
        client = IGMarketsClient(self.config_path)
        price = client.get_current_price('BTCUSD')
        
        self.assertEqual(price, 49500.0)  # Mid price
    
    @patch('requests.get')
    def test_connection_test(self, mock_get):
        """Test connection testing."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'accounts': []}
        mock_get.return_value = mock_response
        
        client = IGMarketsClient(self.config_path)
        result = client.test_connection()
        
        self.assertTrue(result)
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        client = IGMarketsClient(self.config_path)
        
        # First call should be immediate
        start_time = client.last_request_time
        self.assertIsNone(start_time)
        
        # Simulate rate limiting
        with patch('time.sleep') as mock_sleep:
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'snapshot': {'bid': 50000, 'offer': 50000}}
                mock_get.return_value = mock_response
                
                # Make two quick requests
                client.get_current_price('BTCUSD')
                client.get_current_price('ETHUSD')
                
                # Second request should trigger rate limiting
                mock_sleep.assert_called()


class TestPaperTrader(unittest.TestCase):
    """Test the main paper trading engine."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test configs
        self.config_path = os.path.join(self.test_dir, 'test_config.json')
        test_config = {
            "initial_balance": 10000.0,
            "max_position_size": 0.1,
            "risk_percentage": 0.02
        }
        with open(self.config_path, 'w') as f:
            json.dump(test_config, f)
        
        self.ig_config_path = os.path.join(self.test_dir, 'ig_config.json')
        ig_config = {
            "api_key": "test_key",
            "username": "test_user",
            "password": "test_pass",
            "account_id": "test_account"
        }
        with open(self.ig_config_path, 'w') as f:
            json.dump(ig_config, f)
        
        self.db_path = os.path.join(self.test_dir, 'test.db')
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    @patch('sys.path')
    def test_integration_with_exit_strategy(self, mock_path):
        """Test integration with exit strategy system."""
        # Mock the exit strategy import
        mock_exit_strategy = Mock()
        mock_exit_strategy.evaluate_position_exit.return_value = {
            'action': 'HOLD',
            'confidence': 0.7,
            'reason': 'Technical indicators neutral'
        }
        
        with patch.dict('sys.modules', {'phase_4_exit_strategy': mock_exit_strategy}):
            trader = PaperTrader(
                self.db_path,
                self.config_path,
                self.ig_config_path
            )
            
            # Add a mock position
            trader.position_manager.add_position('BTCUSD', 'BUY', 50000.0, 0.002, 100.0)
            
            # Test exit evaluation
            with patch.object(trader.ig_client, 'get_current_price', return_value=51000.0):
                exit_decision = trader.evaluate_exit_strategy('BTCUSD', 51000.0)
                
                self.assertIn('action', exit_decision)
                mock_exit_strategy.evaluate_position_exit.assert_called()
    
    def test_prediction_processing(self):
        """Test prediction processing logic."""
        trader = PaperTrader(
            self.db_path,
            self.config_path,
            self.ig_config_path
        )
        
        # Mock a prediction
        prediction = {
            'symbol': 'BTCUSD',
            'direction': 'BUY',
            'confidence': 0.8,
            'entry_price': 50000.0
        }
        
        with patch.object(trader.ig_client, 'get_current_price', return_value=50000.0):
            with patch.object(trader.position_manager, 'can_open_position', return_value=True):
                result = trader.process_prediction(prediction)
                
                self.assertTrue(result)


class TestSystemIntegration(unittest.TestCase):
    """Test system-wide integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp()
        
        # Create test configs
        self.trading_config = os.path.join(self.test_dir, 'trading_config.json')
        trading_params = {
            "initial_balance": 10000.0,
            "max_position_size": 0.1,
            "risk_percentage": 0.02,
            "stop_loss_percentage": 0.05,
            "take_profit_percentage": 0.1
        }
        with open(self.trading_config, 'w') as f:
            json.dump(trading_params, f)
        
        self.ig_config = os.path.join(self.test_dir, 'ig_config.json')
        ig_params = {
            "api_key": "test_key",
            "username": "test_user",
            "password": "test_pass",
            "account_id": "test_account",
            "base_url": "https://demo-api.ig.com/gateway/deal"
        }
        with open(self.ig_config, 'w') as f:
            json.dump(ig_params, f)
        
        self.db_path = os.path.join(self.test_dir, 'integration_test.db')
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir)
    
    def test_full_trading_cycle(self):
        """Test a complete trading cycle."""
        # Initialize system
        pm = PositionManager(self.db_path, self.trading_config)
        
        # Test initial state
        self.assertEqual(pm.get_account_balance(), 10000.0)
        self.assertEqual(len(pm.get_open_positions()), 0)
        
        # Test position opening
        can_open = pm.can_open_position('BTCUSD', 100.0)
        self.assertTrue(can_open)
        
        # Open position
        pm.add_position('BTCUSD', 'BUY', 50000.0, 0.002, 100.0)
        
        # Verify position is open
        positions = pm.get_open_positions()
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0]['symbol'], 'BTCUSD')
        
        # Test that second position on same symbol is blocked
        can_open_second = pm.can_open_position('BTCUSD', 100.0)
        self.assertFalse(can_open_second)
        
        # Close position with profit
        pm.close_position('BTCUSD', 51000.0, 102.0)
        
        # Verify position is closed and balance updated
        positions = pm.get_open_positions()
        self.assertEqual(len(positions), 0)
        
        balance = pm.get_account_balance()
        self.assertGreater(balance, 10000.0)
    
    def test_fund_management(self):
        """Test fund management across multiple trades."""
        pm = PositionManager(self.db_path, self.trading_config)
        
        # Test maximum position size enforcement
        max_size = pm.calculate_position_size(50000.0)  # BTC at $50k
        max_value = max_size * 50000.0
        
        # Should not exceed 10% of balance
        self.assertLessEqual(max_value, 1000.0)
        
        # Test insufficient funds scenario
        can_open_huge = pm.can_open_position('BTCUSD', 15000.0)  # $15k position
        self.assertFalse(can_open_huge)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPositionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestIGMarketsClient))
    suite.addTests(loader.loadTestsFromTestCase(TestPaperTrader))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    print("🧪 Running IG Markets Paper Trading System Tests")
    print("=" * 50)
    
    success = run_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
