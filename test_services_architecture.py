"""
Test Services Architecture - Comprehensive Testing Suite for Phase 1

This script validates the Phase 1 services architecture including:
- Service startup and health checks
- Inter-service communication
- API endpoint functionality
- Error handling and fallbacks
- Backwards compatibility
"""

import asyncio
import json
import os
import sys
import time
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Warning: requests not available - testing in compatibility mode")

# Import services for direct testing
try:
    from services.trading_service import trading_service, validate_signal, create_position_from_signal
    from services.sentiment_service import sentiment_service, get_symbol_sentiment
    from services.orchestrator_service import orchestrator_service, orchestrate_symbol_prediction
    SERVICES_AVAILABLE = True
except ImportError as e:
    SERVICES_AVAILABLE = False
    print(f"⚠️  Warning: Services import failed - {e}")


class ServicesArchitectureTester:
    """Comprehensive testing suite for services architecture"""
    
    def __init__(self):
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
        
        self.service_urls = {
            'orchestrator': 'http://localhost:8000',
            'trading': 'http://localhost:8001',
            'sentiment': 'http://localhost:8002'
        }
        
        self.test_symbols = ['CBA', 'ANZ', 'WBC', 'NAB', 'BHP']
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Phase 1 Services Architecture Testing")
        print("=" * 60)
        
        # Test categories
        test_categories = [
            ("Service Health Checks", self.test_service_health),
            ("Direct Service Testing", self.test_direct_services),
            ("API Endpoint Testing", self.test_api_endpoints),
            ("Inter-Service Communication", self.test_inter_service_communication),
            ("Error Handling", self.test_error_handling),
            ("Backwards Compatibility", self.test_backwards_compatibility),
            ("Performance Testing", self.test_performance),
            ("Data Validation", self.test_data_validation)
        ]
        
        for category_name, test_function in test_categories:
            print(f"\n📋 {category_name}")
            print("-" * 40)
            
            try:
                test_function()
            except Exception as e:
                self.add_test_result(f"{category_name} - CATEGORY FAILURE", False, str(e))
                print(f"❌ Category failed: {e}")
        
        # Print final results
        self.print_test_summary()
    
    def test_service_health(self):
        """Test health endpoints of all services"""
        for service_name, base_url in self.service_urls.items():
            self.test_health_endpoint(service_name, f"{base_url}/health")
    
    def test_health_endpoint(self, service_name: str, health_url: str):
        """Test individual health endpoint"""
        if not REQUESTS_AVAILABLE:
            self.add_test_result(f"{service_name} health check", None, "requests not available")
            return
        
        try:
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.add_test_result(f"{service_name} health check", True)
                    print(f"✅ {service_name} is healthy")
                else:
                    self.add_test_result(f"{service_name} health check", False, f"Status: {data.get('status')}")
                    print(f"⚠️  {service_name} reports unhealthy status")
            else:
                self.add_test_result(f"{service_name} health check", False, f"HTTP {response.status_code}")
                print(f"❌ {service_name} health check failed: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.add_test_result(f"{service_name} health check", False, "Connection refused")
            print(f"❌ {service_name} is not running (connection refused)")
        except Exception as e:
            self.add_test_result(f"{service_name} health check", False, str(e))
            print(f"❌ {service_name} health check error: {e}")
    
    def test_direct_services(self):
        """Test services directly (without HTTP)"""
        if not SERVICES_AVAILABLE:
            self.add_test_result("Direct services test", None, "Services not importable")
            return
        
        # Test trading service core
        try:
            portfolio = trading_service.get_portfolio_summary()
            self.add_test_result("Trading service portfolio", True)
            print(f"✅ Trading service portfolio: {portfolio.total_positions} positions")
        except Exception as e:
            self.add_test_result("Trading service portfolio", False, str(e))
            print(f"❌ Trading service portfolio failed: {e}")
        
        # Test sentiment service core
        try:
            sentiment = sentiment_service.get_sentiment_score("CBA")
            self.add_test_result("Sentiment service analysis", True)
            print(f"✅ Sentiment service analysis: {sentiment.confidence_score:.2f} confidence")
        except Exception as e:
            self.add_test_result("Sentiment service analysis", False, str(e))
            print(f"❌ Sentiment service analysis failed: {e}")
        
        # Test orchestrator service core
        try:
            status = orchestrator_service.get_system_status()
            self.add_test_result("Orchestrator system status", True)
            print(f"✅ Orchestrator system status: {status['overall_status']}")
        except Exception as e:
            self.add_test_result("Orchestrator system status", False, str(e))
            print(f"❌ Orchestrator system status failed: {e}")
    
    def test_api_endpoints(self):
        """Test API endpoints if services are running"""
        if not REQUESTS_AVAILABLE:
            self.add_test_result("API endpoints test", None, "requests not available")
            return
        
        # Test trading service endpoints
        self.test_trading_api()
        
        # Test sentiment service endpoints
        self.test_sentiment_api()
        
        # Test orchestrator service endpoints
        self.test_orchestrator_api()
    
    def test_trading_api(self):
        """Test trading service API endpoints"""
        base_url = self.service_urls['trading']
        
        # Test portfolio endpoint
        try:
            response = requests.get(f"{base_url}/trading/portfolio", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.add_test_result("Trading API portfolio", True)
                print(f"✅ Trading API portfolio: {data.get('total_positions', 0)} positions")
            else:
                self.add_test_result("Trading API portfolio", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.add_test_result("Trading API portfolio", False, str(e))
        
        # Test signal analysis endpoint
        try:
            test_signal = {
                'symbol': 'CBA',
                'action': 'BUY',
                'confidence': 75.0,
                'entry_price': 168.50,
                'position_size': 10000
            }
            
            response = requests.post(
                f"{base_url}/trading/analyze",
                json={'signal': test_signal, 'validate_only': True},
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                self.add_test_result("Trading API signal analysis", True)
                print(f"✅ Trading API signal analysis: Valid={data.get('is_valid', False)}")
            else:
                self.add_test_result("Trading API signal analysis", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.add_test_result("Trading API signal analysis", False, str(e))
    
    def test_sentiment_api(self):
        """Test sentiment service API endpoints"""
        base_url = self.service_urls['sentiment']
        
        # Test single symbol sentiment
        try:
            response = requests.get(f"{base_url}/sentiment/CBA", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.add_test_result("Sentiment API single symbol", True)
                print(f"✅ Sentiment API single symbol: {data.get('overall_sentiment', 0):.2f} sentiment")
            else:
                self.add_test_result("Sentiment API single symbol", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.add_test_result("Sentiment API single symbol", False, str(e))
        
        # Test batch sentiment
        try:
            response = requests.post(
                f"{base_url}/sentiment/batch",
                json={'symbols': ['CBA', 'ANZ']},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.add_test_result("Sentiment API batch", True)
                print(f"✅ Sentiment API batch: {data.get('symbols_analyzed', 0)} symbols analyzed")
            else:
                self.add_test_result("Sentiment API batch", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.add_test_result("Sentiment API batch", False, str(e))
    
    def test_orchestrator_api(self):
        """Test orchestrator service API endpoints"""
        base_url = self.service_urls['orchestrator']
        
        # Test system status
        try:
            response = requests.get(f"{base_url}/system/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.add_test_result("Orchestrator API system status", True)
                print(f"✅ Orchestrator API system status: {data.get('overall_status', 'unknown')}")
            else:
                self.add_test_result("Orchestrator API system status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.add_test_result("Orchestrator API system status", False, str(e))
        
        # Test prediction orchestration
        try:
            response = requests.post(
                f"{base_url}/orchestrate/predict",
                json={'symbol': 'CBA', 'market_data': {'current_price': 168.50}},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                self.add_test_result("Orchestrator API prediction", True)
                print(f"✅ Orchestrator API prediction: Success={data.get('success', False)}")
            else:
                self.add_test_result("Orchestrator API prediction", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.add_test_result("Orchestrator API prediction", False, str(e))
    
    def test_inter_service_communication(self):
        """Test communication between services"""
        if not SERVICES_AVAILABLE:
            self.add_test_result("Inter-service communication", None, "Services not available")
            return
        
        try:
            # Test orchestrator calling other services
            result = orchestrator_service.orchestrate_prediction_workflow("CBA", {'current_price': 168.50})
            
            success = result.get('success', False)
            steps_completed = len([step for step in result.get('steps', []) if step.get('success')])
            
            self.add_test_result("Inter-service communication", success)
            print(f"✅ Inter-service communication: {steps_completed} steps completed, Success={success}")
            
        except Exception as e:
            self.add_test_result("Inter-service communication", False, str(e))
            print(f"❌ Inter-service communication failed: {e}")
    
    def test_error_handling(self):
        """Test error handling and fallback mechanisms"""
        if not SERVICES_AVAILABLE:
            self.add_test_result("Error handling test", None, "Services not available")
            return
        
        # Test invalid trading signal
        try:
            invalid_signal = {
                'symbol': 'INVALID',
                'action': 'INVALID_ACTION',
                'confidence': -50,  # Invalid confidence
                'entry_price': 0,   # Invalid price
                'position_size': -1000  # Invalid size
            }
            
            validation = validate_signal(invalid_signal)
            
            # Should fail validation but not crash
            if not validation.get('is_valid', True):
                self.add_test_result("Error handling - invalid signal", True)
                print("✅ Error handling - invalid signal handled correctly")
            else:
                self.add_test_result("Error handling - invalid signal", False, "Invalid signal passed validation")
                print("❌ Error handling - invalid signal not caught")
                
        except Exception as e:
            self.add_test_result("Error handling - invalid signal", False, str(e))
            print(f"❌ Error handling - invalid signal crashed: {e}")
        
        # Test sentiment for non-existent symbol
        try:
            sentiment = get_symbol_sentiment("NONEXISTENT")
            
            # Should return fallback sentiment
            if sentiment.get('confidence_score', 1.0) <= 0.5:
                self.add_test_result("Error handling - invalid symbol", True)
                print("✅ Error handling - invalid symbol handled with fallback")
            else:
                self.add_test_result("Error handling - invalid symbol", False, "No fallback for invalid symbol")
                
        except Exception as e:
            self.add_test_result("Error handling - invalid symbol", False, str(e))
            print(f"❌ Error handling - invalid symbol crashed: {e}")
    
    def test_backwards_compatibility(self):
        """Test backwards compatibility with existing functions"""
        if not SERVICES_AVAILABLE:
            self.add_test_result("Backwards compatibility", None, "Services not available")
            return
        
        # Test legacy trading functions
        try:
            signal_dict = {
                'symbol': 'CBA',
                'action': 'BUY',
                'confidence': 75.0,
                'entry_price': 168.50,
                'position_size': 10000
            }
            
            validation = validate_signal(signal_dict)
            if 'is_valid' in validation:
                self.add_test_result("Backwards compatibility - trading", True)
                print("✅ Backwards compatibility - trading functions work")
            else:
                self.add_test_result("Backwards compatibility - trading", False, "Invalid response format")
                
        except Exception as e:
            self.add_test_result("Backwards compatibility - trading", False, str(e))
            print(f"❌ Backwards compatibility - trading failed: {e}")
        
        # Test legacy sentiment functions
        try:
            sentiment = get_symbol_sentiment("CBA")
            if 'overall_sentiment' in sentiment:
                self.add_test_result("Backwards compatibility - sentiment", True)
                print("✅ Backwards compatibility - sentiment functions work")
            else:
                self.add_test_result("Backwards compatibility - sentiment", False, "Invalid response format")
                
        except Exception as e:
            self.add_test_result("Backwards compatibility - sentiment", False, str(e))
            print(f"❌ Backwards compatibility - sentiment failed: {e}")
    
    def test_performance(self):
        """Test basic performance metrics"""
        if not SERVICES_AVAILABLE:
            self.add_test_result("Performance test", None, "Services not available")
            return
        
        # Test response times
        start_time = time.time()
        
        try:
            # Test multiple operations
            for i in range(3):
                sentiment = sentiment_service.get_sentiment_score("CBA")
                portfolio = trading_service.get_portfolio_summary()
                
            execution_time = time.time() - start_time
            
            if execution_time < 5.0:  # Should complete in under 5 seconds
                self.add_test_result("Performance test", True)
                print(f"✅ Performance test: {execution_time:.2f}s for 6 operations")
            else:
                self.add_test_result("Performance test", False, f"Too slow: {execution_time:.2f}s")
                print(f"⚠️  Performance test: {execution_time:.2f}s (slower than expected)")
                
        except Exception as e:
            self.add_test_result("Performance test", False, str(e))
            print(f"❌ Performance test failed: {e}")
    
    def test_data_validation(self):
        """Test data structure validation"""
        if not SERVICES_AVAILABLE:
            self.add_test_result("Data validation", None, "Services not available")
            return
        
        try:
            # Test sentiment data structure
            sentiment = sentiment_service.get_sentiment_score("CBA")
            required_fields = ['symbol', 'overall_sentiment', 'confidence_score', 'analysis_timestamp']
            
            sentiment_dict = sentiment.to_dict()
            missing_fields = [field for field in required_fields if field not in sentiment_dict]
            
            if not missing_fields:
                self.add_test_result("Data validation - sentiment", True)
                print("✅ Data validation - sentiment structure valid")
            else:
                self.add_test_result("Data validation - sentiment", False, f"Missing fields: {missing_fields}")
                print(f"❌ Data validation - sentiment missing: {missing_fields}")
            
            # Test portfolio data structure
            portfolio = trading_service.get_portfolio_summary()
            required_portfolio_fields = ['total_positions', 'total_value', 'available_cash']
            
            portfolio_dict = portfolio.to_dict()
            missing_portfolio_fields = [field for field in required_portfolio_fields if field not in portfolio_dict]
            
            if not missing_portfolio_fields:
                self.add_test_result("Data validation - portfolio", True)
                print("✅ Data validation - portfolio structure valid")
            else:
                self.add_test_result("Data validation - portfolio", False, f"Missing fields: {missing_portfolio_fields}")
                print(f"❌ Data validation - portfolio missing: {missing_portfolio_fields}")
                
        except Exception as e:
            self.add_test_result("Data validation", False, str(e))
            print(f"❌ Data validation failed: {e}")
    
    def add_test_result(self, test_name: str, passed: Optional[bool], error: str = ""):
        """Add a test result"""
        self.test_results['total_tests'] += 1
        
        if passed is True:
            self.test_results['passed_tests'] += 1
        elif passed is False:
            self.test_results['failed_tests'] += 1
        
        self.test_results['test_details'].append({
            'test_name': test_name,
            'passed': passed,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        skipped = total - passed - failed
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Skipped: {skipped} ⚠️")
        
        if total > 0:
            success_rate = (passed / total) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        # Print failed tests details
        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for test in self.test_results['test_details']:
                if test['passed'] is False:
                    print(f"  • {test['test_name']}: {test['error']}")
        
        # Print skipped tests
        if skipped > 0:
            print(f"\n⚠️  Skipped Tests:")
            for test in self.test_results['test_details']:
                if test['passed'] is None:
                    print(f"  • {test['test_name']}: {test['error']}")
        
        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        if success_rate >= 90:
            print("🟢 EXCELLENT - Phase 1 architecture is working well")
        elif success_rate >= 75:
            print("🟡 GOOD - Phase 1 architecture is mostly functional")
        elif success_rate >= 50:
            print("🟠 NEEDS WORK - Phase 1 architecture has issues")
        else:
            print("🔴 CRITICAL - Phase 1 architecture needs significant fixes")
        
        # Save results to file
        try:
            with open('test_results.json', 'w') as f:
                json.dump(self.test_results, f, indent=2)
            print(f"\n📄 Test results saved to test_results.json")
        except Exception as e:
            print(f"\n⚠️  Could not save test results: {e}")


def main():
    """Main execution"""
    print("Phase 1 Services Architecture Testing Suite")
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Requests Available: {REQUESTS_AVAILABLE}")
    print(f"Services Available: {SERVICES_AVAILABLE}")
    
    tester = ServicesArchitectureTester()
    tester.run_all_tests()


if __name__ == "__main__":
    main()
