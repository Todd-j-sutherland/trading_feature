#!/usr/bin/env python3
"""
Multi-Region Trading System Validation Suite
Comprehensive testing of all multi-region functionality
"""

import asyncio
import json
import time
import sys
import os
from typing import Dict, List, Any
from datetime import datetime

# Add the services directory to the path
sys.path.append('/opt/trading_services')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MultiRegionValidator:
    """Comprehensive validation of multi-region trading system"""
    
    def __init__(self):
        self.regions = ["asx", "usa", "uk", "eu"]
        self.services = ["prediction", "market-data", "sentiment"]
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results[test_name] = result
        
        if status == "PASS":
            self.passed_tests.append(test_name)
            print(f"✅ {test_name}: PASSED")
        elif status == "FAIL":
            self.failed_tests.append(test_name)
            print(f"❌ {test_name}: FAILED - {details}")
        elif status == "WARN":
            print(f"⚠️  {test_name}: WARNING - {details}")
        else:
            print(f"ℹ️  {test_name}: {status} - {details}")
            
        if details:
            print(f"   Details: {details}")
    
    async def test_service_socket_connection(self, service_name: str):
        """Test Unix socket connection to service"""
        test_name = f"Socket Connection - {service_name}"
        
        try:
            socket_path = f"/tmp/trading_{service_name}.sock"
            
            if not os.path.exists(socket_path):
                self.log_test(test_name, "FAIL", f"Socket file {socket_path} does not exist")
                return False
            
            # Try to connect to socket
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path),
                timeout=5.0
            )
            
            # Send health check
            request = {"method": "health", "params": {}}
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            # Read response
            response_data = await asyncio.wait_for(reader.read(8192), timeout=5.0)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            if response.get("status") == "success":
                self.log_test(test_name, "PASS", f"Service responding on {socket_path}")
                return True
            else:
                self.log_test(test_name, "FAIL", f"Service returned error: {response.get('error', 'Unknown')}")
                return False
                
        except asyncio.TimeoutError:
            self.log_test(test_name, "FAIL", "Connection timeout")
            return False
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Connection error: {str(e)}")
            return False
    
    async def test_configuration_manager(self):
        """Test configuration manager functionality"""
        test_name = "Configuration Manager"
        
        try:
            from app.config.regions.config_manager import ConfigManager
            
            # Test initialization
            config_mgr = ConfigManager(region="asx")
            
            # Test available regions
            available_regions = config_mgr.get_available_regions()
            expected_regions = set(self.regions)
            actual_regions = set(available_regions)
            
            if expected_regions.issubset(actual_regions):
                self.log_test(f"{test_name} - Region Discovery", "PASS", 
                             f"Found regions: {available_regions}")
            else:
                missing = expected_regions - actual_regions
                self.log_test(f"{test_name} - Region Discovery", "FAIL", 
                             f"Missing regions: {missing}")
                return False
            
            # Test region switching
            for region in self.regions:
                config_mgr.set_region(region)
                config = config_mgr.get_config()
                
                # Verify region-specific configuration
                region_info = config.get("region", {})
                if region_info.get("code") == region:
                    self.log_test(f"{test_name} - {region.upper()} Switch", "PASS",
                                 f"Successfully loaded {region} configuration")
                else:
                    self.log_test(f"{test_name} - {region.upper()} Switch", "FAIL",
                                 f"Region code mismatch: expected {region}, got {region_info.get('code')}")
                    return False
            
            return True
            
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Configuration manager error: {str(e)}")
            return False
    
    async def test_regional_configurations(self):
        """Test all regional configurations"""
        test_name = "Regional Configurations"
        
        try:
            from app.config.regions.config_manager import ConfigManager
            config_mgr = ConfigManager()
            
            for region in self.regions:
                region_test = f"{test_name} - {region.upper()}"
                
                try:
                    config_mgr.set_region(region)
                    config = config_mgr.get_config()
                    
                    # Check required sections
                    required_sections = ["region", "market_data", "sentiment", "prediction"]
                    missing_sections = []
                    
                    for section in required_sections:
                        if section not in config:
                            missing_sections.append(section)
                    
                    if missing_sections:
                        self.log_test(region_test, "FAIL", 
                                     f"Missing sections: {missing_sections}")
                        continue
                    
                    # Check region-specific data
                    market_data = config["market_data"]
                    sentiment = config["sentiment"]
                    
                    # Verify symbols exist
                    symbols = market_data.get("symbols", {})
                    big4_banks = symbols.get("big4_banks", [])
                    
                    if len(big4_banks) >= 4:
                        self.log_test(f"{region_test} - Symbols", "PASS",
                                     f"Found {len(big4_banks)} big4 banks: {big4_banks}")
                    else:
                        self.log_test(f"{region_test} - Symbols", "FAIL",
                                     f"Insufficient big4 banks: {big4_banks}")
                    
                    # Verify trading hours
                    trading_hours = market_data.get("trading_hours", {})
                    if "market_open" in trading_hours and "market_close" in trading_hours:
                        self.log_test(f"{region_test} - Trading Hours", "PASS",
                                     f"Open: {trading_hours['market_open']}, Close: {trading_hours['market_close']}")
                    else:
                        self.log_test(f"{region_test} - Trading Hours", "FAIL",
                                     "Missing trading hours configuration")
                    
                    # Verify sentiment sources
                    news_sources = sentiment.get("news_sources", {})
                    if news_sources:
                        source_count = sum(len(sources) for sources in news_sources.values())
                        self.log_test(f"{region_test} - News Sources", "PASS",
                                     f"Found {source_count} news sources")
                    else:
                        self.log_test(f"{region_test} - News Sources", "FAIL",
                                     "No news sources configured")
                    
                except Exception as e:
                    self.log_test(region_test, "FAIL", f"Configuration error: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Regional configuration test failed: {str(e)}")
            return False
    
    async def test_service_region_switching(self, service_name: str):
        """Test region switching functionality for a service"""
        test_name = f"Region Switching - {service_name}"
        
        try:
            socket_path = f"/tmp/trading_{service_name}.sock"
            
            for region in self.regions:
                region_test = f"{test_name} - {region.upper()}"
                
                try:
                    # Connect to service
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_unix_connection(socket_path),
                        timeout=5.0
                    )
                    
                    # Switch region
                    request = {"method": "switch_region", "params": {"region": region}}
                    writer.write(json.dumps(request).encode())
                    await writer.drain()
                    
                    response_data = await asyncio.wait_for(reader.read(8192), timeout=10.0)
                    response = json.loads(response_data.decode())
                    
                    writer.close()
                    await writer.wait_closed()
                    
                    if response.get("status") == "success":
                        result = response.get("result", {})
                        if result.get("region") == region:
                            self.log_test(region_test, "PASS", 
                                         f"Successfully switched to {region}")
                        else:
                            self.log_test(region_test, "FAIL",
                                         f"Region switch failed: expected {region}, got {result.get('region')}")
                    else:
                        self.log_test(region_test, "FAIL",
                                     f"Region switch error: {response.get('error')}")
                
                except Exception as e:
                    self.log_test(region_test, "FAIL", f"Region switch failed: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Service region switching test failed: {str(e)}")
            return False
    
    async def test_prediction_service_functionality(self):
        """Test prediction service functionality"""
        test_name = "Prediction Service Functionality"
        
        try:
            socket_path = "/tmp/trading_prediction.sock"
            
            # Test health check
            reader, writer = await asyncio.open_unix_connection(socket_path)
            request = {"method": "health", "params": {}}
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            response_data = await reader.read(8192)
            response = json.loads(response_data.decode())
            writer.close()
            await writer.wait_closed()
            
            if response.get("status") == "success":
                health_data = response.get("result", {})
                self.log_test(f"{test_name} - Health Check", "PASS",
                             f"Service status: {health_data.get('status')}")
            else:
                self.log_test(f"{test_name} - Health Check", "FAIL",
                             f"Health check failed: {response.get('error')}")
                return False
            
            # Test predictions for each region
            for region in self.regions:
                region_test = f"{test_name} - {region.upper()} Predictions"
                
                try:
                    reader, writer = await asyncio.open_unix_connection(socket_path)
                    
                    # Get region-specific symbols
                    from app.config.regions.config_manager import ConfigManager
                    config_mgr = ConfigManager(region=region)
                    config = config_mgr.get_config()
                    symbols = config["market_data"]["symbols"]["big4_banks"][:2]  # Test with 2 symbols
                    
                    request = {
                        "method": "generate_predictions",
                        "params": {"symbols": symbols, "region": region}
                    }
                    writer.write(json.dumps(request).encode())
                    await writer.drain()
                    
                    response_data = await asyncio.wait_for(reader.read(32768), timeout=30.0)
                    response = json.loads(response_data.decode())
                    
                    writer.close()
                    await writer.wait_closed()
                    
                    if response.get("status") == "success":
                        result = response.get("result", {})
                        predictions = result.get("predictions", {})
                        
                        if len(predictions) == len(symbols):
                            successful_preds = sum(1 for p in predictions.values() if "error" not in p)
                            self.log_test(region_test, "PASS",
                                         f"Generated {successful_preds}/{len(symbols)} predictions")
                        else:
                            self.log_test(region_test, "WARN",
                                         f"Generated {len(predictions)}/{len(symbols)} predictions")
                    else:
                        self.log_test(region_test, "FAIL",
                                     f"Prediction generation failed: {response.get('error')}")
                
                except Exception as e:
                    self.log_test(region_test, "FAIL", f"Prediction test failed: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Prediction service test failed: {str(e)}")
            return False
    
    async def test_sentiment_service_functionality(self):
        """Test sentiment service functionality"""
        test_name = "Sentiment Service Functionality"
        
        try:
            socket_path = "/tmp/trading_sentiment.sock"
            
            # Test Big 4 sentiment for each region
            for region in self.regions:
                region_test = f"{test_name} - {region.upper()} Big4 Sentiment"
                
                try:
                    reader, writer = await asyncio.open_unix_connection(socket_path)
                    
                    request = {
                        "method": "get_big4_sentiment",
                        "params": {"region": region}
                    }
                    writer.write(json.dumps(request).encode())
                    await writer.drain()
                    
                    response_data = await asyncio.wait_for(reader.read(8192), timeout=20.0)
                    response = json.loads(response_data.decode())
                    
                    writer.close()
                    await writer.wait_closed()
                    
                    if response.get("status") == "success":
                        result = response.get("result", {})
                        avg_sentiment = result.get("big4_average_sentiment", 0)
                        consensus = result.get("consensus", "UNKNOWN")
                        region_code = result.get("region", "unknown")
                        
                        if region_code == region:
                            self.log_test(region_test, "PASS",
                                         f"Sentiment: {avg_sentiment:.3f}, Consensus: {consensus}")
                        else:
                            self.log_test(region_test, "FAIL",
                                         f"Region mismatch: expected {region}, got {region_code}")
                    else:
                        self.log_test(region_test, "FAIL",
                                     f"Sentiment analysis failed: {response.get('error')}")
                
                except Exception as e:
                    self.log_test(region_test, "FAIL", f"Sentiment test failed: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Sentiment service test failed: {str(e)}")
            return False
    
    async def test_market_data_service_functionality(self):
        """Test market data service functionality"""
        test_name = "Market Data Service Functionality"
        
        try:
            socket_path = "/tmp/trading_market-data.sock"
            
            # Test market status for each region
            for region in self.regions:
                region_test = f"{test_name} - {region.upper()} Market Status"
                
                try:
                    reader, writer = await asyncio.open_unix_connection(socket_path)
                    
                    request = {
                        "method": "is_market_open",
                        "params": {"region": region}
                    }
                    writer.write(json.dumps(request).encode())
                    await writer.drain()
                    
                    response_data = await asyncio.wait_for(reader.read(8192), timeout=10.0)
                    response = json.loads(response_data.decode())
                    
                    writer.close()
                    await writer.wait_closed()
                    
                    if response.get("status") == "success":
                        market_open = response.get("result", False)
                        status = "OPEN" if market_open else "CLOSED"
                        self.log_test(region_test, "PASS", f"Market status: {status}")
                    else:
                        self.log_test(region_test, "FAIL",
                                     f"Market status check failed: {response.get('error')}")
                
                except Exception as e:
                    self.log_test(region_test, "FAIL", f"Market data test failed: {str(e)}")
            
            return True
            
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Market data service test failed: {str(e)}")
            return False
    
    async def test_cross_region_isolation(self):
        """Test that region switching doesn't affect other services"""
        test_name = "Cross-Region Isolation"
        
        try:
            # Switch prediction service to USA
            pred_socket = "/tmp/trading_prediction.sock"
            reader, writer = await asyncio.open_unix_connection(pred_socket)
            request = {"method": "switch_region", "params": {"region": "usa"}}
            writer.write(json.dumps(request).encode())
            await writer.drain()
            response_data = await reader.read(8192)
            writer.close()
            await writer.wait_closed()
            
            # Check sentiment service is still on original region (should not be affected)
            sent_socket = "/tmp/trading_sentiment.sock"
            reader, writer = await asyncio.open_unix_connection(sent_socket)
            request = {"method": "get_current_region", "params": {}}
            writer.write(json.dumps(request).encode())
            await writer.drain()
            response_data = await reader.read(8192)
            response = json.loads(response_data.decode())
            writer.close()
            await writer.wait_closed()
            
            if response.get("status") == "success":
                sentiment_region = response.get("result", {}).get("region")
                if sentiment_region != "usa":  # Should not have changed
                    self.log_test(test_name, "PASS",
                                 f"Services are isolated - sentiment still on {sentiment_region}")
                else:
                    self.log_test(test_name, "WARN",
                                 "Services may not be properly isolated")
            else:
                self.log_test(test_name, "FAIL",
                             f"Isolation test failed: {response.get('error')}")
            
            return True
            
        except Exception as e:
            self.log_test(test_name, "FAIL", f"Cross-region isolation test failed: {str(e)}")
            return False
    
    async def run_comprehensive_validation(self):
        """Run all validation tests"""
        print("🔍 Starting Multi-Region Trading System Validation")
        print("=" * 60)
        
        start_time = time.time()
        
        # Basic connectivity tests
        print("\n📡 Testing Service Connectivity...")
        for service in self.services:
            await self.test_service_socket_connection(service)
        
        # Configuration tests
        print("\n⚙️  Testing Configuration System...")
        await self.test_configuration_manager()
        await self.test_regional_configurations()
        
        # Region switching tests
        print("\n🌍 Testing Region Switching...")
        for service in self.services:
            await self.test_service_region_switching(service)
        
        # Service functionality tests
        print("\n🧠 Testing Service Functionality...")
        await self.test_prediction_service_functionality()
        await self.test_sentiment_service_functionality()
        await self.test_market_data_service_functionality()
        
        # Integration tests
        print("\n🔗 Testing Service Integration...")
        await self.test_cross_region_isolation()
        
        # Generate report
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed = len(self.passed_tests)
        failed = len(self.failed_tests)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Success Rate: {(passed/total_tests)*100:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS ({failed}):")
            for test in self.failed_tests:
                result = self.test_results[test]
                print(f"  - {test}: {result['details']}")
        
        if passed == total_tests:
            print("\n🎉 ALL TESTS PASSED! Multi-region system is working correctly.")
            return True
        else:
            print(f"\n⚠️  {failed} tests failed. Please check the system configuration.")
            return False
    
    def save_test_report(self, filename: str = "validation_report.json"):
        """Save detailed test report to file"""
        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "total_tests": len(self.test_results),
            "passed_tests": len(self.passed_tests),
            "failed_tests": len(self.failed_tests),
            "success_rate": (len(self.passed_tests) / len(self.test_results)) * 100 if self.test_results else 0,
            "test_results": self.test_results,
            "failed_test_names": self.failed_tests,
            "passed_test_names": self.passed_tests
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Detailed test report saved to: {filename}")

async def main():
    """Main validation function"""
    print("Multi-Region Trading System Validator")
    print("====================================")
    
    validator = MultiRegionValidator()
    
    try:
        success = await validator.run_comprehensive_validation()
        validator.save_test_report()
        
        if success:
            print("\n✅ Validation completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Validation completed with failures!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
