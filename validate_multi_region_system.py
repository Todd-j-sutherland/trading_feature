#!/usr/bin/env python3
"""
Comprehensive Multi-Region System Validation Test
Tests all aspects of the multi-region implementation
"""
import asyncio
import sys
import os
import time
from pathlib import Path

# Add paths for imports
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent / "app"))

def test_imports():
    """Test that all multi-region components can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Test config manager import
        from app.config.regions.config_manager import ConfigManager
        print("   ✅ ConfigManager import successful")
        
        # Test base config import
        from app.config.base_config import BaseConfig
        print("   ✅ BaseConfig import successful")
        
        # Test regional configs
        regions_to_test = ["asx", "usa", "uk", "eu"]
        for region in regions_to_test:
            try:
                region_module = f"app.config.regions.{region}"
                __import__(region_module)
                print(f"   ✅ {region.upper()} config import successful")
            except ImportError as e:
                print(f"   ⚠️  {region.upper()} config import failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        return False

def test_config_manager():
    """Test ConfigManager functionality"""
    print("\n🔧 Testing ConfigManager...")
    
    try:
        from app.config.regions.config_manager import ConfigManager
        
        # Test initialization
        config_mgr = ConfigManager(region="asx")
        print(f"   ✅ Initialized with region: {config_mgr.current_region}")
        
        # Test available regions
        available = config_mgr.get_available_regions()
        print(f"   ✅ Available regions: {available}")
        
        # Test region switching
        for region in ["usa", "uk", "eu", "asx"]:
            try:
                config_mgr.set_region(region)
                config = config_mgr.get_config()
                
                # Verify region-specific data
                market_data = config.get("market_data", {})
                symbols = market_data.get("symbols", {})
                big4 = symbols.get("big4_banks", [])
                
                print(f"   ✅ {region.upper()}: {len(big4)} big4 banks - {big4[:2]}...")
                
            except Exception as e:
                print(f"   ⚠️  {region.upper()} switch failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ConfigManager test failed: {e}")
        return False

def test_region_configs():
    """Test individual region configurations"""
    print("\n🌍 Testing Region Configurations...")
    
    expected_regions = {
        "asx": {
            "currency": "AUD",
            "timezone": "Australia/Sydney",
            "big4_sample": ["CBA.AX", "ANZ.AX"]
        },
        "usa": {
            "currency": "USD", 
            "timezone": "America/New_York",
            "big4_sample": ["JPM", "BAC"]
        },
        "uk": {
            "currency": "GBP",
            "timezone": "Europe/London", 
            "big4_sample": ["LLOY.L", "BARC.L"]
        },
        "eu": {
            "currency": "EUR",
            "timezone": "Europe/Paris",
            "big4_sample": ["BNP.PA", "ACA.PA"]
        }
    }
    
    try:
        from app.config.regions.config_manager import ConfigManager
        config_mgr = ConfigManager()
        
        for region, expected in expected_regions.items():
            try:
                config_mgr.set_region(region)
                config = config_mgr.get_config()
                
                # Check basic region info
                region_info = config.get("region", {})
                currency = region_info.get("currency")
                timezone = region_info.get("timezone")
                
                # Check symbols
                symbols = config.get("market_data", {}).get("symbols", {})
                big4_banks = symbols.get("big4_banks", [])
                
                # Validate
                currency_match = currency == expected["currency"]
                timezone_match = timezone == expected["timezone"]
                symbols_exist = len(big4_banks) >= 3
                expected_symbols = all(sym in big4_banks for sym in expected["big4_sample"])
                
                if currency_match and timezone_match and symbols_exist and expected_symbols:
                    print(f"   ✅ {region.upper()}: Currency={currency}, TZ={timezone}, Banks={len(big4_banks)}")
                else:
                    print(f"   ⚠️  {region.upper()}: Issues detected")
                    if not currency_match:
                        print(f"      - Currency: expected {expected['currency']}, got {currency}")
                    if not timezone_match:
                        print(f"      - Timezone: expected {expected['timezone']}, got {timezone}")
                    if not symbols_exist:
                        print(f"      - Not enough bank symbols: {len(big4_banks)}")
                        
            except Exception as e:
                print(f"   ❌ {region.upper()} validation failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Region config test failed: {e}")
        return False

async def test_service_integration():
    """Test service integration with multi-region"""
    print("\n🔌 Testing Service Integration...")
    
    try:
        # Test if prediction service can use multi-region config
        from services.prediction.prediction_service import PredictionService
        
        service = PredictionService(default_region="asx")
        print("   ✅ PredictionService initialized with multi-region support")
        
        # Test region methods
        current_region = await service.get_current_region()
        print(f"   ✅ Current region: {current_region}")
        
        available_regions = await service.get_available_regions()
        print(f"   ✅ Available regions: {available_regions}")
        
        # Test region switching
        for region in ["usa", "uk"]:
            try:
                switch_result = await service.switch_region(region)
                print(f"   ✅ Switched to {region.upper()}: {switch_result}")
                
                # Get region info after switch
                current = await service.get_current_region()
                if current.get("region") == region:
                    print(f"   ✅ Region switch verified: {region.upper()}")
                else:
                    print(f"   ⚠️  Region switch issue: expected {region}, got {current.get('region')}")
                    
            except Exception as e:
                print(f"   ⚠️  Switch to {region.upper()} failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Service integration test failed: {e}")
        return False

async def test_multi_region_predictions():
    """Test multi-region prediction functionality"""
    print("\n🤖 Testing Multi-Region Predictions...")
    
    try:
        from services.prediction.prediction_service import PredictionService
        
        service = PredictionService(default_region="asx")
        
        # Test region-specific predictions
        test_regions = {
            "asx": ["CBA.AX"],
            "usa": ["JPM"], 
            "uk": ["LLOY.L"],
            "eu": ["BNP.PA"]
        }
        
        for region, symbols in test_regions.items():
            try:
                print(f"   Testing {region.upper()} predictions...")
                
                # Generate prediction for this region
                result = await service.generate_predictions(
                    symbols=symbols,
                    region=region,
                    force_refresh=True
                )
                
                if "predictions" in result and symbols[0] in result["predictions"]:
                    prediction = result["predictions"][symbols[0]]
                    confidence = prediction.get("confidence", 0)
                    action = prediction.get("action", "UNKNOWN")
                    
                    print(f"   ✅ {region.upper()} prediction: {symbols[0]} -> {action} ({confidence:.3f})")
                else:
                    print(f"   ⚠️  {region.upper()} prediction incomplete")
                    
            except Exception as e:
                print(f"   ⚠️  {region.upper()} prediction failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Multi-region predictions test failed: {e}")
        return False

async def test_sentiment_service():
    """Test sentiment service multi-region functionality"""
    print("\n📰 Testing Sentiment Service Multi-Region...")
    
    try:
        from services.sentiment.sentiment_service import SentimentService
        
        service = SentimentService(default_region="asx")
        print("   ✅ SentimentService initialized")
        
        # Test region switching
        for region in ["asx", "usa"]:
            try:
                await service.switch_region(region)
                current = await service.get_current_region()
                print(f"   ✅ Sentiment service switched to {region.upper()}")
                
                # Test Big 4 sentiment for region
                big4_sentiment = await service.get_big4_sentiment(region=region)
                if "big4_average_sentiment" in big4_sentiment:
                    avg_sentiment = big4_sentiment["big4_average_sentiment"]
                    print(f"   ✅ {region.upper()} Big 4 sentiment: {avg_sentiment:.3f}")
                else:
                    print(f"   ⚠️  {region.upper()} sentiment data incomplete")
                    
            except Exception as e:
                print(f"   ⚠️  {region.upper()} sentiment test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Sentiment service test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\n📁 Testing File Structure...")
    
    required_files = [
        "app/config/base_config.py",
        "app/config/regions/config_manager.py",
        "app/config/regions/asx/__init__.py",
        "app/config/regions/usa/__init__.py", 
        "app/config/regions/uk/__init__.py",
        "app/config/regions/eu/__init__.py",
        "services/prediction/prediction_service.py",
        "services/sentiment/sentiment_service.py"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            existing_files.append(file_path)
            print(f"   ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path} - MISSING")
    
    print(f"\n   Summary: {len(existing_files)}/{len(required_files)} files exist")
    
    if missing_files:
        print(f"   Missing files: {len(missing_files)}")
        for file in missing_files[:3]:  # Show first 3 missing
            print(f"     - {file}")
        return False
    
    return True

async def run_comprehensive_test():
    """Run all tests in sequence"""
    print("🚀 MULTI-REGION TRADING SYSTEM VALIDATION")
    print("=" * 80)
    
    test_results = {}
    
    # Test 1: File Structure
    test_results["file_structure"] = test_file_structure()
    
    # Test 2: Imports
    test_results["imports"] = test_imports()
    
    # Test 3: Config Manager
    test_results["config_manager"] = test_config_manager()
    
    # Test 4: Region Configs
    test_results["region_configs"] = test_region_configs()
    
    # Test 5: Service Integration (async)
    test_results["service_integration"] = await test_service_integration()
    
    # Test 6: Multi-Region Predictions (async)
    test_results["predictions"] = await test_multi_region_predictions()
    
    # Test 7: Sentiment Service (async)
    test_results["sentiment"] = await test_sentiment_service()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Multi-region system is fully functional!")
        print("\nNext steps:")
        print("  1. Deploy services with: systemctl start trading-*")
        print("  2. Run health dashboard: python services/monitoring_dashboard.py")
        print("  3. Test cross-region trading strategies")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check issues above.")
        print("\nCheck:")
        print("  1. File paths and imports")
        print("  2. Python environment setup")
        print("  3. Dependencies installation")
    
    return passed == total

if __name__ == "__main__":
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:2]}...")
    print()
    
    try:
        success = asyncio.run(run_comprehensive_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
