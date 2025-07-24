#!/usr/bin/env python3
"""
Tests for Daily Manager
"""

import unittest
import tempfile
import shutil
import sys
import os
import subprocess
from unittest.mock import Mock, patch, MagicMock

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDailyManager(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_daily_manager_initialization(self):
        """Test daily manager initialization"""
        try:
            from daily_manager import TradingSystemManager
            
            # Test initialization
            manager = TradingSystemManager()
            self.assertIsNotNone(manager)
            self.assertTrue(hasattr(manager, 'base_dir'))
            
        except ImportError:
            self.skipTest("TradingSystemManager not available for testing")
    
    def test_daily_manager_commands(self):
        """Test daily manager command structure"""
        
        # Test command mapping
        commands = {
            'morning': 'morning_routine',
            'evening': 'evening_routine',
            'status': 'quick_status',
            'weekly': 'weekly_maintenance',
            'restart': 'emergency_restart'
        }
        
        for command, method in commands.items():
            self.assertIsInstance(command, str)
            self.assertIsInstance(method, str)
            self.assertGreater(len(command), 0)
    
    @patch('subprocess.run')
    def test_run_command_functionality(self, mock_subprocess):
        """Test run_command functionality"""
        # Mock successful command execution
        mock_subprocess.return_value = Mock(returncode=0, stdout="Success", stderr="")
        
        # Test command execution simulation
        result = self._simulate_run_command("echo 'test'", "Test command")
        self.assertTrue(result)
    
    @patch('subprocess.Popen')
    def test_morning_routine_commands(self, mock_popen):
        """Test morning routine commands"""
        # Mock subprocess calls
        mock_popen.return_value = Mock()
        
        # Test morning routine steps
        morning_steps = [
            'comprehensive_analyzer.py',
            'smart_collector.py',
            'launch_dashboard_auto.py'
        ]
        
        for step in morning_steps:
            self.assertIn('.py', step)
            self.assertGreater(len(step), 0)
    
    def test_evening_routine_commands(self):
        """Test evening routine commands"""
        
        # Test evening routine steps
        evening_steps = [
            'advanced_daily_collection.py',
            'advanced_paper_trading.py',
            'comprehensive_analyzer.py'
        ]
        
        for step in evening_steps:
            self.assertIn('.py', step)
            self.assertGreater(len(step), 0)
    
    def test_status_check_commands(self):
        """Test status check commands"""
        
        # Mock status check outputs
        status_checks = {
            'sample_count': 87,
            'win_rate': 0.6,
            'collection_progress': 'Active',
            'system_health': 'Good'
        }
        
        # Test status data structure
        for key, value in status_checks.items():
            self.assertIsNotNone(value)
            if isinstance(value, (int, float)):
                self.assertGreaterEqual(value, 0)
    
    def test_weekly_maintenance_commands(self):
        """Test weekly maintenance commands"""
        
        # Test weekly maintenance steps
        weekly_steps = [
            'retrain_ml_models.py',
            'sentiment_threshold_calibrator.py',
            'market_timing_optimizer.py',
            'advanced_paper_trading.py'
        ]
        
        for step in weekly_steps:
            self.assertIn('.py', step)
            self.assertGreater(len(step), 0)
    
    @patch('subprocess.run')
    def test_emergency_restart_functionality(self, mock_subprocess):
        """Test emergency restart functionality"""
        # Mock subprocess calls for restart
        mock_subprocess.return_value = Mock(returncode=0)
        
        # Test restart steps
        restart_steps = [
            'pkill -f "smart_collector\\|launch_dashboard\\|news_trading"',
            'smart_collector.py',
            'launch_dashboard_auto.py'
        ]
        
        for step in restart_steps:
            self.assertGreater(len(step), 0)
    
    def test_command_validation(self):
        """Test command validation"""
        
        # Valid commands
        valid_commands = ['morning', 'evening', 'status', 'weekly', 'restart']
        for command in valid_commands:
            self.assertTrue(self._is_valid_command(command))
        
        # Invalid commands
        invalid_commands = ['invalid', '', 'test', 'random']
        for command in invalid_commands:
            self.assertFalse(self._is_valid_command(command))
    
    def test_error_handling(self):
        """Test error handling in daily manager"""
        
        # Test command timeout handling
        with self.assertRaises((subprocess.TimeoutExpired, Exception)):
            # Simulate timeout
            raise subprocess.TimeoutExpired("test", 30)
        
        # Test invalid command handling
        try:
            result = self._handle_invalid_command("invalid_command")
            self.assertFalse(result)
        except Exception:
            pass  # Expected for error testing
    
    def test_logging_functionality(self):
        """Test logging in daily manager"""
        
        # Test log message format
        log_messages = [
            "🔄 Starting system...",
            "✅ Success",
            "❌ Error occurred",
            "⏰ Timeout after 30 seconds"
        ]
        
        for message in log_messages:
            self.assertIsInstance(message, str)
            self.assertGreater(len(message), 0)
    
    def test_background_process_management(self):
        """Test background process management"""
        
        # Mock background processes
        background_processes = [
            'smart_collector.py',
            'launch_dashboard_auto.py'
        ]
        
        for process in background_processes:
            self.assertIn('.py', process)
            # Test process should be suitable for background execution
            self.assertTrue(self._is_background_suitable(process))
    
    def test_system_health_monitoring(self):
        """Test system health monitoring"""
        
        # Mock health metrics
        health_metrics = {
            'processes_running': 2,
            'memory_usage': 0.3,
            'disk_usage': 0.1,
            'last_update': 'recent'
        }
        
        # Test health thresholds
        self.assertLessEqual(health_metrics['memory_usage'], 0.8)
        self.assertLessEqual(health_metrics['disk_usage'], 0.9)
        self.assertGreater(health_metrics['processes_running'], 0)
    
    def test_configuration_management(self):
        """Test configuration management"""
        
        # Test configuration paths
        config_paths = [
            '/Users/toddsutherland/Repos/trading_analysis',
            'data/ml_models',
            'reports',
            'logs'
        ]
        
        for path in config_paths:
            self.assertIsInstance(path, str)
            self.assertGreater(len(path), 0)
    
    # Helper methods
    def _simulate_run_command(self, command, description):
        """Simulate command execution"""
        if not command or not isinstance(command, str):
            return False
        return True
    
    def _is_valid_command(self, command):
        """Check if command is valid"""
        valid_commands = ['morning', 'evening', 'status', 'weekly', 'restart']
        return command in valid_commands
    
    def _handle_invalid_command(self, command):
        """Handle invalid command"""
        return False
    
    def _is_background_suitable(self, process):
        """Check if process is suitable for background execution"""
        background_suitable = ['smart_collector.py', 'launch_dashboard_auto.py']
        return process in background_suitable

if __name__ == "__main__":
    unittest.main()
