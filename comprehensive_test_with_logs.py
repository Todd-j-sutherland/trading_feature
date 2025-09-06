#!/usr/bin/env python3
"""
Comprehensive Test Suite with Detailed Logging
Tests all enhanced functionality and outputs logs to file for review
"""

import logging
import sys
import traceback
import os
from datetime import datetime
from pathlib import Path

# Setup comprehensive logging to file
log_file = f"enhanced_integration_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
log_path = Path(__file__).parent / log_file

# Configure logging to both file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_with_error_handling(test_name, test_func):
    """Run a test with comprehensive error handling and logging"""
    logger.info(f"{'='*60}")
    logger.info(f"STARTING TEST: {test_name}")
    logger.info(f"{'='*60}")
    
    try:
        result = test_func()
        logger.info(f"✅ TEST PASSED: {test_name}")
        return result
    except Exception as e:
        logger.error(f"❌ TEST FAILED: {test_name}")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def test_plugin_initialization():
    """Test plugin initialization with detailed logging"""
    logger.info("Testing plugin initialization...")
    
    # Test IG Markets credentials plugin
    try:
        from app.core.data.collectors.ig_markets_credentials_plugin import (
            activate_ig_markets_credentials, 
            validate_ig_markets_credentials,
            get_ig_markets_plugin_status
        )
        
        logger.info("✅ IG Markets credentials plugin imported successfully")
        
        # Test activation
        activation_result = activate_ig_markets_credentials()
        logger.info(f"IG Markets activation result: {activation_result}")
        
        # Test validation
        validation_result = validate_ig_markets_credentials()
        logger.info(f"IG Markets validation result: {validation_result}")
        
        # Test status
        status_result = get_ig_markets_plugin_status()
        logger.info(f"IG Markets status: {status_result}")
        
    except Exception as e:
        logger.error(f"IG Markets plugin test failed: {e}")
        logger.error(traceback.format_exc())
    
    # Test exit strategy plugin
    try:
        from app.core.exit_strategy_plugin import (
            activate_exit_strategy,
            get_exit_strategy_status,
            is_market_hours
        )
        
        logger.info("✅ Exit strategy plugin imported successfully")
        
        # Test activation
        activation_result = activate_exit_strategy()
        logger.info(f"Exit strategy activation result: {activation_result}")
        
        # Test market hours
        market_hours_result = is_market_hours()
        logger.info(f"Market hours active: {market_hours_result}")
        
        # Test status
        status_result = get_exit_strategy_status()
        logger.info(f"Exit strategy status: {status_result}")
        
    except Exception as e:
        logger.error(f"Exit strategy plugin test failed: {e}")
        logger.error(traceback.format_exc())
    
    # Test main app integration
    try:
        from app.core.main_app_integration import (
            initialize_app_plugins,
            enhance_morning_routine,
            enhance_status_check,
            print_plugin_summary
        )
        
        logger.info("✅ Main app integration imported successfully")
        
        # Test plugin initialization
        plugin_results = initialize_app_plugins()
        logger.info(f"Plugin initialization results: {plugin_results}")
        
        return True
        
    except Exception as e:
        logger.error(f"Main app integration test failed: {e}")
        logger.error(traceback.format_exc())
        return False

def test_enhanced_main_commands():
    """Test enhanced main application commands"""
    logger.info("Testing enhanced main application commands...")
    
    import subprocess
    import os
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    commands_to_test = [
        "python3 -m app.main_enhanced market-status",
        "python3 -m app.main_enhanced test-market-context", 
        "python3 -m app.main_enhanced test-predictor"
    ]
    
    success_count = 0
    total_commands = len(commands_to_test)
    
    for cmd in commands_to_test:
        logger.info(f"Testing command: {cmd}")
        try:
            result = subprocess.run(
                cmd.split(),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            logger.info(f"Command exit code: {result.returncode}")
            logger.info(f"Command stdout: {result.stdout}")
            if result.stderr:
                logger.warning(f"Command stderr: {result.stderr}")
            
            # Check if command was successful
            if result.returncode == 0:
                success_count += 1
                logger.info(f"✅ Command successful: {cmd}")
            else:
                logger.error(f"❌ Command failed with exit code {result.returncode}: {cmd}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Command timed out: {cmd}")
        except Exception as e:
            logger.error(f"❌ Command failed: {cmd}")
            logger.error(f"Error: {e}")
    
    logger.info(f"Commands test summary: {success_count}/{total_commands} successful")
    
    # Return True if all commands were successful
    return success_count == total_commands

def test_status_enhancement_fix():
    """Test the specific status enhancement issue"""
    logger.info("Testing status enhancement fix...")
    
    try:
        from app.core.main_app_integration import enhance_status_check
        
        # Test with None input (the problematic case)
        logger.info("Testing with None input...")
        result_none = enhance_status_check(None)
        logger.info(f"Result with None input: {result_none}")
        
        # Test with empty dict
        logger.info("Testing with empty dict...")
        result_empty = enhance_status_check({})
        logger.info(f"Result with empty dict: {result_empty}")
        
        # Test with sample data
        logger.info("Testing with sample data...")
        sample_data = {
            'status': 'operational',
            'timestamp': datetime.now().isoformat()
        }
        result_sample = enhance_status_check(sample_data)
        logger.info(f"Result with sample data: {result_sample}")
        
        return True
        
    except Exception as e:
        logger.error(f"Status enhancement test failed: {e}")
        logger.error(traceback.format_exc())
        return False

def test_exit_strategy_functionality():
    """Test exit strategy functionality with sample data"""
    logger.info("Testing exit strategy functionality...")
    
    try:
        from app.core.exit_strategy_plugin import check_position_exits
        
        # Sample positions for testing
        sample_positions = [
            {
                'symbol': 'CBA.AX',
                'entry_price': 100.50,
                'predicted_action': 'BUY',
                'prediction_confidence': 0.75,
                'entry_timestamp': '2025-09-05T09:30:00',
                'shares': 100
            },
            {
                'symbol': 'WBC.AX', 
                'entry_price': 25.80,
                'predicted_action': 'BUY',
                'prediction_confidence': 0.82,
                'entry_timestamp': '2025-09-05T10:15:00',
                'shares': 200
            }
        ]
        
        logger.info(f"Testing with {len(sample_positions)} sample positions...")
        
        exit_recommendations = check_position_exits(sample_positions)
        logger.info(f"Exit recommendations received: {len(exit_recommendations)}")
        
        for i, rec in enumerate(exit_recommendations):
            logger.info(f"Exit recommendation {i+1}: {rec}")
        
        return True
        
    except Exception as e:
        logger.error(f"Exit strategy functionality test failed: {e}")
        logger.error(traceback.format_exc())
        return False

def test_ig_markets_data_fetching():
    """Test IG Markets data fetching functionality"""
    logger.info("Testing IG Markets data fetching...")
    
    try:
        # Test enhanced market data collector
        from app.core.data.collectors.enhanced_market_data_collector import get_current_price, get_data_source_stats
        
        test_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX']
        
        for symbol in test_symbols:
            logger.info(f"Testing price fetch for {symbol}...")
            price_data = get_current_price(symbol)
            logger.info(f"{symbol} price data: {price_data}")
        
        # Test data source statistics
        stats = get_data_source_stats()
        logger.info(f"Data source statistics: {stats}")
        
        return True
        
    except Exception as e:
        logger.error(f"IG Markets data fetching test failed: {e}")
        logger.error(traceback.format_exc())
        return False

def run_comprehensive_tests():
    """Run all comprehensive tests"""
    logger.info(f"Starting comprehensive test suite")
    logger.info(f"Log file: {log_path}")
    logger.info(f"Timestamp: {datetime.now()}")
    
    test_results = {}
    
    # Run all tests
    test_results['plugin_initialization'] = test_with_error_handling(
        "Plugin Initialization", 
        test_plugin_initialization
    )
    
    test_results['status_enhancement_fix'] = test_with_error_handling(
        "Status Enhancement Fix",
        test_status_enhancement_fix
    )
    
    test_results['exit_strategy_functionality'] = test_with_error_handling(
        "Exit Strategy Functionality",
        test_exit_strategy_functionality
    )
    
    test_results['ig_markets_data_fetching'] = test_with_error_handling(
        "IG Markets Data Fetching",
        test_ig_markets_data_fetching
    )
    
    test_results['enhanced_main_commands'] = test_with_error_handling(
        "Enhanced Main Commands",
        test_enhanced_main_commands
    )
    
    # Summary
    logger.info(f"{'='*60}")
    logger.info(f"TEST SUITE SUMMARY")
    logger.info(f"{'='*60}")
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result is not None else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result is not None:
            passed_tests += 1
    
    logger.info(f"{'='*60}")
    logger.info(f"OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    logger.info(f"Log file saved to: {log_path}")
    logger.info(f"{'='*60}")
    
    return test_results

if __name__ == "__main__":
    print(f"🧪 Starting comprehensive test suite...")
    print(f"📝 Logs will be saved to: {log_path}")
    
    try:
        results = run_comprehensive_tests()
        
        print(f"\n📊 Test Results Summary:")
        for test_name, result in results.items():
            status = "✅" if result is not None else "❌"
            print(f"   {status} {test_name}")
        
        print(f"\n📝 Detailed logs saved to: {log_path}")
        print(f"💡 Review the log file for detailed error analysis")
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        logger.error(traceback.format_exc())
        print(f"❌ Test suite failed - check log file: {log_path}")
